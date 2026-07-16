import json
import math
import os
import random
import re
import sqlite3
from typing import List, Optional
from contextlib import asynccontextmanager  # 1. 파일 최상단 근처에 추가
from fastapi import FastAPI


from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_databases()  # 서버가 켜질 때 DB 초기화 실행
    yield             # 서버가 작동하는 동안 대기


app = FastAPI(
    title="LocalHub API Server",
    description=(
        "관광지 정보 조회, 게시판, AI 챗봇 API를 제공하는 FastAPI 백엔드 (Render 배포용). "
        "프론트엔드(Vue 3 + Vite)는 Netlify에 별도로 배포되어 이 서버를 CORS로 호출한다."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# CORS 설정
#   프론트엔드(Netlify)와 백엔드(Render)가 서로 다른 도메인이므로 CORS가 반드시 필요하다.
#   FRONTEND_ORIGINS 환경변수에 콤마(,)로 구분된 허용 도메인 목록을 설정한다.
#   예) FRONTEND_ORIGINS=https://your-app.netlify.app,https://your-custom-domain.com
#   설정하지 않으면 로컬 개발용 주소만 기본 허용된다.
# ------------------------------------------------------------------
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
allow_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# 프로젝트 디렉터리 구조 (Render 배포용 - API 서버 전용)
#   .
#   ├── main.py
#   ├── requirements.txt
#   └── data/
#       ├── tour_data.db    (관광지 POI 데이터)
#       ├── bus_data.db     (버스 노선 데이터)
#       └── post.db         (커뮤니티 게시판, 최초 실행 시 자동 생성)
#
# 프론트엔드(index_db2.html → Vue 프로젝트, kakaomap.html)는 더 이상 이 서버가 서빙하지 않고
# Netlify에 정적 사이트로 별도 배포된다. 이 서버는 순수 API + WebSocket만 제공한다.
# ------------------------------------------------------------------
# DB 경로
# ------------------------------------------------------------------
# 관광지(POI) DB: 환경변수로 오버라이드 가능 (기본값: data/tour_data.db)
TOUR_DB_PATH = os.getenv("TOUR_DB_PATH", os.path.join("data", "tour_data.db"))

# 버스 노선 통합 DB 경로 (route_nodes + route_mapping 테이블이 함께 들어있는 단일 파일)
BUS_DATA_DB_PATH = os.getenv("BUS_DATA_DB_PATH", os.path.join("data", "bus_data.db"))

# 커뮤니티 게시판 DB
POST_DB_DIR = "data"
POST_DB_PATH = os.path.join(POST_DB_DIR, "post.db")


def init_databases():
    os.makedirs(POST_DB_DIR, exist_ok=True)
    conn = sqlite3.connect(POST_DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                password TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                tags TEXT,
                likes INTEGER DEFAULT 0,
                image TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            cursor.execute("ALTER TABLE posts ADD COLUMN image TEXT")
        except sqlite3.OperationalError:
            pass
        conn.commit()
    finally:
        conn.close()


def get_tour_db():
    if not os.path.exists(TOUR_DB_PATH):
        raise HTTPException(status_code=500, detail=f"관광지 데이터베이스({TOUR_DB_PATH})가 존재하지 않습니다.")
    conn = sqlite3.connect(TOUR_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_post_db():
    conn = sqlite3.connect(POST_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_db_connection():
    """/api/pois, /api/routes 처럼 Depends 없이 직접 커넥션이 필요한 곳에서 사용."""
    if not os.path.exists(TOUR_DB_PATH):
        raise HTTPException(status_code=500, detail=f"DB 파일을 찾을 수 없습니다: {TOUR_DB_PATH}")
    conn = sqlite3.connect(TOUR_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 버스 노선은 정적 데이터이므로 최초 요청 시 한 번만 계산해서 메모리에 캐싱한다.
_route_cache = None


def _build_routes():
    """
    bus_data.db 안의 두 테이블을 조인해서 노선별 근사 경로를 만든다.
        - route_nodes   : 정류장/경유노드 좌표 (원본 CSV를 그대로 옮긴 테이블)
        - route_mapping : 노선ID -> 실제 버스번호/노선유형/기점/종점

    route_mapping에 없는(실제 버스번호를 모르는) 노선은 결과에서 제외한다.
    주의: 이 데이터셋은 POSX=위도, POSY=경도 (일반적인 명명과 반대).
    """
    global _route_cache
    if _route_cache is not None:
        return _route_cache

    if not os.path.exists(BUS_DATA_DB_PATH):
        raise HTTPException(
            status_code=500,
            detail=f"버스 데이터 DB 파일을 찾을 수 없습니다: {BUS_DATA_DB_PATH}"
        )

    conn = sqlite3.connect(BUS_DATA_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                rn.BUS_ROUTE_ID AS route_id,
                rn.SEQ          AS seq,
                rn.POSX         AS lat,
                rn.POSY         AS lng,
                rm.routeno      AS routeno,
                rm.routetp      AS routetp,
                rm.startnodenm  AS startnodenm,
                rm.endnodenm    AS endnodenm
            FROM route_nodes rn
            JOIN route_mapping rm ON rn.BUS_ROUTE_ID = rm.route_id
            WHERE rn.STTN_YN = '1'
              AND rn.POSX IS NOT NULL AND rn.POSX != 0
              AND rn.POSY IS NOT NULL AND rn.POSY != 0
            ORDER BY rn.BUS_ROUTE_ID, rn.SEQ
            """
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    grouped = {}
    for row in rows:
        grouped.setdefault(row["route_id"], {
            "route_no": row["routeno"],
            "route_type": row["routetp"] or "",
            "start_name": row["startnodenm"],
            "end_name": row["endnodenm"],
            "path": [],
        })["path"].append({"lat": row["lat"], "lng": row["lng"]})

    routes = []
    for route_id, data in grouped.items():
        if len(data["path"]) < 2:
            continue  # 점 하나로는 선을 그릴 수 없음
        routes.append({
            "route_id": route_id,
            "route_no": data["route_no"],
            "route_type": data["route_type"],
            "start_name": data["start_name"],
            "end_name": data["end_name"],
            "stop_count": len(data["path"]),
            "path": data["path"],
        })

    # 실제 버스번호가 숫자면 숫자 기준, 아니면 문자 기준으로 자연스럽게 정렬
    def sort_key(r):
        no = str(r["route_no"])
        return (0, int(no)) if no.isdigit() else (1, no)

    routes.sort(key=sort_key)
    _route_cache = routes
    return _route_cache


# ------------------------------------------------------------------
# Pydantic 스키마
# ------------------------------------------------------------------

class TourSchema(BaseModel):
    contentid: str
    contenttypeid: str
    region: str
    title: str
    addr1: Optional[str] = None
    addr2: Optional[str] = None
    zipcode: Optional[str] = None
    tel: Optional[str] = None
    mapx: Optional[float] = None
    mapy: Optional[float] = None
    mlevel: Optional[str] = None
    firstimage: Optional[str] = None
    firstimage2: Optional[str] = None


class TourListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[TourSchema]


class PostCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    password: str = Field(..., min_length=4)
    tags: Optional[str] = None
    image: Optional[str] = None


class PostUpdateSchema(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    image: Optional[str] = None
    password: str


class PasswordVerifySchema(BaseModel):
    password: str


class PostResponseSchema(BaseModel):
    id: int
    title: str
    content: str
    views: int
    tags: Optional[str] = None
    likes: int
    image: Optional[str] = None
    created_at: str


class PostListResponseSchema(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    items: List[PostResponseSchema]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


# ------------------------------------------------------------------
# 페이지 라우트 (프론트엔드 서빙)
# ------------------------------------------------------------------

@app.get("/", tags=["System"])
async def read_root():
    """루트 헬스체크 겸 안내. 실제 화면은 Netlify에 배포된 프론트엔드에서 제공한다."""
    return {
        "service": "LocalHub API Server",
        "status": "ok",
        "frontend": "이 서버는 API 전용입니다. 프론트엔드는 Netlify에 별도 배포되어 있습니다.",
        "docs": "/docs",
    }


# ------------------------------------------------------------------
# 지도용 API (kakaomap.html에서 사용)
# ------------------------------------------------------------------

@app.get("/api/pois", tags=["Map API"])
async def get_pois():
    """
    지도에 표시할 관광 데이터(POI)를 카테고리(contenttypeid)와 함께 반환.
    mapx(경도)/mapy(위도) 값이 없는 행은 지도에 찍을 수 없으므로 제외한다.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT contentid, contenttypeid, title, addr1, addr2, tel,
                   mapx, mapy, firstimage
            FROM pois
            WHERE mapx IS NOT NULL AND mapy IS NOT NULL
              AND mapx != '' AND mapy != ''
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
        return rows
    finally:
        conn.close()


@app.get("/api/routes", tags=["Map API"])
async def get_routes():
    """
    버스 노선별 근사 경로(정류장만 이어붙인 좌표 목록)를 반환.
    bus_data.db 하나에서 route_nodes와 route_mapping을 조인해서 만들며,
    매핑이 없는 노선은 결과에서 제외한다.
    """
    return _build_routes()


@app.get("/api/routes/near", tags=["Map API"])
async def get_nearby_routes(mapx: float, mapy: float, radius_km: float = 1.0, limit: int = 10):
    """
    특정 지점(mapx=경도, mapy=위도) 기준 반경 radius_km 이내를 지나는 버스 노선을 반환.
    노선까지의 거리는 해당 노선이 지나는 정류장 좌표들 중 지점에서 가장 가까운
    정류장까지의 거리로 근사한다 (실제 도로 경로가 아닌 직선 거리).
    반경 안에 노선이 하나도 없으면, 대신 가장 가까운 노선 1개만 반환한다.
    """
    def min_distance_km(path):
        best = None
        for point in path:
            dlat = math.radians(point["lat"] - mapy)
            dlon = math.radians(point["lng"] - mapx)
            a = (math.sin(dlat / 2) ** 2
                 + math.cos(math.radians(mapy)) * math.cos(math.radians(point["lat"])) * math.sin(dlon / 2) ** 2)
            distance = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            if best is None or distance < best:
                best = distance
        return best

    scored = []
    for route in _build_routes():
        distance = min_distance_km(route["path"])
        if distance is not None:
            scored.append((distance, route))
    scored.sort(key=lambda item: item[0])

    within_radius = [(d, r) for d, r in scored if d <= radius_km]
    selected = within_radius[:limit] if within_radius else scored[:1]

    return [
        {
            "route_id": route["route_id"],
            "route_no": route["route_no"],
            "route_type": route["route_type"],
            "start_name": route["start_name"],
            "end_name": route["end_name"],
            "stop_count": route["stop_count"],
            "distance_km": round(distance, 3),
        }
        for distance, route in selected
    ]


# ------------------------------------------------------------------
# 버스 길찾기 (출발지 -> 도착지 최적 노선 탐색, 1회 환승 지원)
# ------------------------------------------------------------------
# 알고리즘 개요
#   1) 출발지에서 걸어갈 수 있는(walk_radius_km 이내) 정류장을 가진 노선 = 승차 후보
#   2) 도착지에서 걸어갈 수 있는 정류장을 가진 노선 = 하차 후보
#   3) 직행: 승차 후보 ∩ 하차 후보 노선에서 (도보 + 승차거리) 비용 최소 조합 선택
#   4) 환승: 승차 후보 노선의 각 정류장 근처(transfer_radius_km)에 하차 후보 노선의
#      정류장이 있으면 1회 환승 경로로 계산 (공간 그리드 인덱스로 근접 탐색)
#   5) 비용 = 도보거리*도보가중치 + 승차거리 + (환승 시 환승 페널티)
#
# 주의: route_nodes의 SEQ는 기점->종점 방향 순서이지만, 상/하행이 한 노선에 함께
#       들어있는 데이터셋도 있어 여기서는 양방향 승차를 모두 허용하는 근사 방식을 쓴다.

WALK_WEIGHT = 4.0          # 도보 1km를 버스 4km와 같은 비용으로 취급 (도보 기피 가중치)
TRANSFER_PENALTY_KM = 2.0  # 환승 1회당 추가 비용 (버스 2km에 해당)
GRID_CELL_DEG = 0.005      # 정류장 그리드 셀 크기 (약 500m)

_transit_index = None      # {"stops": {route_id: [...]}, "cum": {route_id: [...]}, "grid": {...}}


def _haversine_km(lat1, lng1, lat2, lng2):
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_transit_index():
    """노선별 정류장 목록/누적거리와, 근접 탐색용 공간 그리드를 1회 계산해 캐싱한다."""
    global _transit_index
    if _transit_index is not None:
        return _transit_index

    stops, cum, grid, meta = {}, {}, {}, {}
    for route in _build_routes():
        route_id = route["route_id"]
        path = route["path"]
        stops[route_id] = path
        meta[route_id] = route

        # 누적 거리: cum[i] = 0번 정류장부터 i번 정류장까지의 경로 길이(km)
        distances = [0.0]
        for i in range(1, len(path)):
            prev, curr = path[i - 1], path[i]
            distances.append(distances[-1] + _haversine_km(prev["lat"], prev["lng"], curr["lat"], curr["lng"]))
        cum[route_id] = distances

        for idx, point in enumerate(path):
            cell = (int(point["lat"] / GRID_CELL_DEG), int(point["lng"] / GRID_CELL_DEG))
            grid.setdefault(cell, []).append((route_id, idx, point["lat"], point["lng"]))

    _transit_index = {"stops": stops, "cum": cum, "grid": grid, "meta": meta}
    return _transit_index


def _stops_near(lat, lng, radius_km):
    """그리드 인덱스로 (lat, lng) 반경 radius_km 이내 정류장을 [(dist, route_id, idx)]로 반환."""
    index = _build_transit_index()
    span = max(1, int(math.ceil(radius_km / (GRID_CELL_DEG * 111.0))) + 1)
    base = (int(lat / GRID_CELL_DEG), int(lng / GRID_CELL_DEG))
    found = []
    for dx in range(-span, span + 1):
        for dy in range(-span, span + 1):
            for route_id, idx, stop_lat, stop_lng in index["grid"].get((base[0] + dx, base[1] + dy), []):
                distance = _haversine_km(lat, lng, stop_lat, stop_lng)
                if distance <= radius_km:
                    found.append((distance, route_id, idx))
    found.sort(key=lambda item: item[0])
    return found


def _nearest_stop_per_route(candidates):
    """[(dist, route_id, idx)]에서 노선별로 가장 가까운 정류장 하나만 남긴다."""
    best = {}
    for distance, route_id, idx in candidates:
        if route_id not in best or distance < best[route_id][0]:
            best[route_id] = (distance, idx)
    return best  # {route_id: (walk_km, stop_idx)}


def _leg_payload(route_id, board_idx, alight_idx):
    """지도 표시용 승차 구간(leg) 정보를 만든다."""
    index = _build_transit_index()
    route = index["meta"][route_id]
    path = index["stops"][route_id]
    ride_km = abs(index["cum"][route_id][alight_idx] - index["cum"][route_id][board_idx])
    return {
        "route_id": route_id,
        "route_no": route["route_no"],
        "route_type": route["route_type"],
        "start_name": route["start_name"],
        "end_name": route["end_name"],
        "board": {"idx": board_idx, "lat": path[board_idx]["lat"], "lng": path[board_idx]["lng"]},
        "alight": {"idx": alight_idx, "lat": path[alight_idx]["lat"], "lng": path[alight_idx]["lng"]},
        "ride_km": round(ride_km, 3),
        "ride_stops": abs(alight_idx - board_idx),
    }


@app.get("/api/routes/plan", tags=["Map API"])
async def plan_bus_route(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    walk_radius_km: float = Query(0.8, gt=0, le=2.0, description="출발/도착 지점에서 정류장까지 허용 도보 반경(km)"),
    transfer_radius_km: float = Query(0.35, gt=0, le=1.0, description="환승 시 두 정류장 사이 허용 도보 반경(km)"),
    max_results: int = Query(5, ge=1, le=10),
):
    """
    출발 좌표 -> 도착 좌표로 가는 버스 경로를 찾는다.
    직행 노선을 우선 찾고, 없거나 부족하면 1회 환승 경로까지 탐색해서
    (도보 + 승차거리 + 환승 페널티) 비용이 낮은 순으로 최대 max_results개 반환한다.
    """
    straight_km = _haversine_km(start_lat, start_lng, end_lat, end_lng)
    if straight_km < 0.05:
        return {"plans": [], "message": "출발지와 도착지가 너무 가깝습니다."}

    start_candidates = _nearest_stop_per_route(_stops_near(start_lat, start_lng, walk_radius_km))
    end_candidates = _nearest_stop_per_route(_stops_near(end_lat, end_lng, walk_radius_km))

    if not start_candidates or not end_candidates:
        missing = "출발지" if not start_candidates else "도착지"
        return {"plans": [], "message": f"{missing} 근처 {walk_radius_km}km 이내에 버스 정류장이 없습니다."}

    index = _build_transit_index()
    plans = []

    # ---------- 1) 직행 (같은 노선이 출발지/도착지 근처를 모두 지나는 경우) ----------
    for route_id in set(start_candidates) & set(end_candidates):
        walk_start, board_idx = start_candidates[route_id]
        walk_end, alight_idx = end_candidates[route_id]
        if board_idx == alight_idx:
            continue
        leg = _leg_payload(route_id, board_idx, alight_idx)
        # 승차거리가 직선거리 대비 지나치게 길면(크게 돌아가면) 후보에서 제외
        if leg["ride_km"] > max(straight_km * 3.0, straight_km + 4.0):
            continue
        cost = (walk_start + walk_end) * WALK_WEIGHT + leg["ride_km"]
        plans.append({
            "type": "direct",
            "cost": round(cost, 3),
            "walk_start_km": round(walk_start, 3),
            "walk_end_km": round(walk_end, 3),
            "transfer_walk_km": None,
            "total_ride_km": leg["ride_km"],
            "legs": [leg],
        })

    # ---------- 2) 1회 환승 ----------
    # 승차/하차 후보를 도보거리 순으로 최대 15개 노선씩만 검토해서 계산량을 제한한다.
    start_routes = sorted(start_candidates.items(), key=lambda item: item[1][0])[:15]
    end_routes = dict(sorted(end_candidates.items(), key=lambda item: item[1][0])[:15])
    direct_route_ids = {plan["legs"][0]["route_id"] for plan in plans}
    best_pairs = {}  # {(route_a, route_b): plan}

    for route_a, (walk_start, board_idx) in start_routes:
        path_a = index["stops"][route_a]
        cum_a = index["cum"][route_a]
        for idx_a, stop_a in enumerate(path_a):
            if idx_a == board_idx:
                continue
            ride_a = abs(cum_a[idx_a] - cum_a[board_idx])
            if ride_a > straight_km * 3.0 + 2.0:
                continue
            # stop_a 근처의 "하차 후보 노선" 정류장을 그리드로 탐색
            for t_walk, route_b, idx_b in _stops_near(stop_a["lat"], stop_a["lng"], transfer_radius_km):
                if route_b == route_a or route_b not in end_routes:
                    continue
                walk_end, alight_idx = end_routes[route_b]
                if idx_b == alight_idx:
                    continue
                ride_b = abs(index["cum"][route_b][alight_idx] - index["cum"][route_b][idx_b])
                total_ride = ride_a + ride_b
                if total_ride > max(straight_km * 3.5, straight_km + 5.0):
                    continue
                cost = ((walk_start + t_walk + walk_end) * WALK_WEIGHT
                        + total_ride + TRANSFER_PENALTY_KM)
                key = (route_a, route_b)
                if key in best_pairs and best_pairs[key]["cost"] <= cost:
                    continue
                best_pairs[key] = {
                    "type": "transfer",
                    "cost": round(cost, 3),
                    "walk_start_km": round(walk_start, 3),
                    "walk_end_km": round(walk_end, 3),
                    "transfer_walk_km": round(t_walk, 3),
                    "total_ride_km": round(total_ride, 3),
                    "legs": [
                        _leg_payload(route_a, board_idx, idx_a),
                        _leg_payload(route_b, idx_b, alight_idx),
                    ],
                }

    # 직행이 이미 있는 노선 조합의 환승 경로는 대부분 열등하므로,
    # 같은 노선으로 시작하는 환승 경로는 직행보다 비용이 확실히 낮을 때만 남긴다.
    min_direct_cost = min((plan["cost"] for plan in plans), default=None)
    for pair_plan in best_pairs.values():
        if min_direct_cost is not None and pair_plan["cost"] >= min_direct_cost and pair_plan["legs"][0]["route_id"] in direct_route_ids:
            continue
        plans.append(pair_plan)

    plans.sort(key=lambda plan: plan["cost"])
    if not plans:
        return {"plans": [], "message": "조건에 맞는 버스 경로를 찾지 못했습니다. 도보 반경을 넓혀 다시 시도해보세요."}
    return {"plans": plans[:max_results], "message": None}


# ------------------------------------------------------------------
# 관광지(Tour) API (검색/상세/주변 검색 등, index_db2.html의 통합검색 화면 등에서 사용)
# ------------------------------------------------------------------

@app.get("/api/tours", response_model=TourListResponse, tags=["Tour API"])
def get_tours(region: Optional[str] = None, contenttypeid: Optional[str] = None,
              search: Optional[str] = None, page: int = Query(1, ge=1),
              limit: int = Query(10, ge=1, le=100), db: sqlite3.Connection = Depends(get_tour_db)):
    conditions, params = [], []
    if region:
        conditions.append("region = ?"); params.append(region)
    if contenttypeid:
        conditions.append("contenttypeid = ?"); params.append(contenttypeid)
    if search:
        conditions.append("(title LIKE ? OR content LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    cursor = db.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM pois {where_clause}", params)
    total = cursor.fetchone()[0]
    cursor.execute(f"SELECT * FROM pois {where_clause} ORDER BY title ASC LIMIT ? OFFSET ?", params + [limit, (page - 1) * limit])
    return {"total": total, "page": page, "limit": limit, "items": [dict(row) for row in cursor.fetchall()]}


NEIGHBORHOODS = {
    "중구": "중구", "동구": "동구", "서구": "서구", "유성구": "유성구", "대덕구": "대덕구",
    "둔산동": "둔산동", "봉명동": "봉명동", "은행동": "은행동", "대흥동": "대흥동",
    "궁동": "궁동", "노은동": "노은동", "가수원동": "가수원동", "관저동": "관저동",
}


def _count_neighborhood_mentions():
    """게시글 해시태그에서 동네별 언급 횟수를 센다."""
    counts = {}
    post_conn = sqlite3.connect(POST_DB_PATH)
    try:
        for row in post_conn.execute("SELECT tags FROM posts WHERE tags IS NOT NULL"):
            for tag in str(row[0]).split(","):
                normalized = tag.strip().lstrip("#").replace(" ", "")
                if normalized in NEIGHBORHOODS:
                    name = NEIGHBORHOODS[normalized]
                    counts[name] = counts.get(name, 0) + 1
    finally:
        post_conn.close()
    return counts


@app.get("/api/hot-place", tags=["Community API"])
def get_hot_place(
    region: Optional[str] = None,
    limit_per_category: int = Query(4, ge=1, le=10),
):
    """상위 지역 해시태그와 선택 지역의 무작위 장소를 반환한다."""
    counts = _count_neighborhood_mentions()

    if not counts:
        return {"regions": [], "selected_region": None, "items": {"맛집": [], "관광지": []}}

    ranked_regions = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:3]
    regions = [{"neighborhood": name, "mention_count": count} for name, count in ranked_regions]
    if not region:
        return {"regions": regions, "selected_region": None, "items": {"맛집": [], "관광지": []}}

    selected_region = next((item for item in regions if item["neighborhood"] == region), None)
    if not selected_region:
        raise HTTPException(status_code=404, detail="상위 지역 해시태그에서 찾을 수 없습니다.")
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT contentid, contenttypeid, title, addr1, addr2, mapx, mapy, firstimage "
            "FROM pois WHERE (addr1 LIKE ? OR addr2 LIKE ?) "
            "AND CAST(contenttypeid AS TEXT) IN ('12', '39') ORDER BY RANDOM()",
            (f"%{region}%", f"%{region}%"),
        ).fetchall()
        items = {"맛집": [], "관광지": []}
        for row in rows:
            place = dict(row)
            category = "맛집" if str(place["contenttypeid"]) == "39" else "관광지"
            if len(items[category]) < limit_per_category:
                items[category].append(place)
        return {"regions": regions, "selected_region": selected_region, "items": items}
    finally:
        conn.close()


@app.get("/api/hot-place/random", tags=["Community API"])
def get_random_hot_places(count: int = Query(3, ge=1, le=10), pool_size: int = Query(10, ge=1, le=20)):
    """
    게시글 해시태그 언급 횟수 기준 상위 pool_size개 동네(최대 10개)에 속한 장소들을 모아,
    그중 무작위로 count개를 뽑아 반환한다. 지도 검색창에 검색어가 없을 때
    "게시글에서 많이 언급된 동네의 추천 장소"로 보여주기 위한 용도.
    """
    counts = _count_neighborhood_mentions()
    if not counts:
        return []

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:pool_size]
    top_neighborhoods = [name for name, _ in ranked]

    conn = get_db_connection()
    try:
        conditions = " OR ".join(["(addr1 LIKE ? OR addr2 LIKE ?)"] * len(top_neighborhoods))
        params = []
        for name in top_neighborhoods:
            params.extend([f"%{name}%", f"%{name}%"])
        rows = conn.execute(
            f"SELECT contentid, contenttypeid, title, addr1, addr2, mapx, mapy, firstimage "
            f"FROM pois WHERE ({conditions}) AND CAST(contenttypeid AS TEXT) = '39' ORDER BY RANDOM()",
            params,
        ).fetchall()
        candidates = [dict(row) for row in rows]
    finally:
        conn.close()

    random.shuffle(candidates)
    return candidates[:count]


@app.get("/api/tours/near", response_model=List[TourSchema], tags=["Tour API"])
def get_nearby_tours(mapx: float, mapy: float, radius_km: float = 5.0, limit: int = 20,
                     db: sqlite3.Connection = Depends(get_tour_db)):
    nearby_items = []
    for row in db.execute("SELECT * FROM pois WHERE mapx IS NOT NULL AND mapy IS NOT NULL"):
        poi = dict(row)
        try:
            lon, lat = float(poi["mapx"]), float(poi["mapy"])
        except (TypeError, ValueError):
            continue
        dlat, dlon = math.radians(lat - mapy), math.radians(lon - mapx)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(mapy)) * math.cos(math.radians(lat)) * math.sin(dlon / 2) ** 2
        distance = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        if distance <= radius_km:
            poi["distance_km"] = round(distance, 3)
            nearby_items.append(poi)
    return sorted(nearby_items, key=lambda item: item["distance_km"])[:limit]


@app.get("/api/tours/{contentid}", response_model=TourSchema, tags=["Tour API"])
def get_tour_detail(contentid: str, db: sqlite3.Connection = Depends(get_tour_db)):
    row = db.execute("SELECT * FROM pois WHERE contentid = ?", (contentid,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="해당 관광지 정보를 찾을 수 없습니다.")
    return dict(row)



# ------------------------------------------------------------------
# 예정 축제/행사 API
# ------------------------------------------------------------------

def _parse_event_date(value):
    """관광 데이터의 YYYYMMDD/ISO 날짜 문자열을 YYYY-MM-DD로 정규화한다."""
    if value is None:
        return None
    digits = re.sub(r"[^0-9]", "", str(value))
    if len(digits) < 8:
        return None
    yyyy, mm, dd = digits[:4], digits[4:6], digits[6:8]
    try:
        # datetime import 없이 유효성만 간단히 검증
        import datetime as _dt
        parsed = _dt.date(int(yyyy), int(mm), int(dd))
        return parsed.isoformat()
    except ValueError:
        return None


@app.get("/api/events/upcoming", tags=["Tour API"])
def get_upcoming_events(
    limit: int = Query(10, ge=1, le=100),
    include_past: bool = Query(False, description="true면 이미 종료된 과거 행사도 포함해서 반환한다 (예: 캘린더에 전체 행사를 표시할 때)"),
):
    """
    pois 테이블에 저장된 축제·공연·행사(contenttypeid=15)만 조회한다.
    데이터베이스에 존재하는 날짜 컬럼을 자동 탐색하고, 기본적으로는 오늘 이후 또는 진행 중인 행사만
    시작일 기준으로 정렬해서 반환한다. include_past=true면 종료된 과거 행사도 함께 반환한다.
    """
    import datetime as _dt

    conn = get_db_connection()
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(pois)").fetchall()}
        start_candidates = ["eventstartdate", "event_start_date", "startdate", "start_date"]
        end_candidates = ["eventenddate", "event_end_date", "enddate", "end_date"]
        start_column = next((name for name in start_candidates if name in columns), None)
        end_column = next((name for name in end_candidates if name in columns), None)

        if not start_column:
            return {
                "items": [],
                "total": 0,
                "warning": "pois 테이블에서 행사 시작일 컬럼을 찾지 못했습니다. 지원 컬럼: eventstartdate, event_start_date, startdate, start_date"
            }

        select_columns = [
            "contentid", "contenttypeid", "title", "addr1", "addr2",
            "mapx", "mapy", "firstimage", start_column
        ]
        if end_column:
            select_columns.append(end_column)

        rows = conn.execute(
            f"SELECT {', '.join(select_columns)} FROM pois WHERE CAST(contenttypeid AS TEXT) = '15'"
        ).fetchall()

        today = _dt.date.today().isoformat()
        items = []
        for row in rows:
            item = dict(row)
            start_date = _parse_event_date(item.get(start_column))
            end_date = _parse_event_date(item.get(end_column)) if end_column else start_date
            if not start_date:
                continue
            effective_end = end_date or start_date
            if not include_past and effective_end < today:
                continue
            try:
                mapx = float(item.get("mapx"))
                mapy = float(item.get("mapy"))
            except (TypeError, ValueError):
                continue

            items.append({
                "contentid": str(item.get("contentid")),
                "title": item.get("title"),
                "address": " ".join(filter(None, [item.get("addr1"), item.get("addr2")])),
                "mapx": mapx,
                "mapy": mapy,
                "firstimage": item.get("firstimage"),
                "start_date": start_date,
                "end_date": end_date or start_date,
            })

        items.sort(key=lambda event: (event["start_date"], event["title"] or ""))
        return {"items": items[:limit], "total": len(items)}
    finally:
        conn.close()


# ------------------------------------------------------------------
# 게시판(Post) API (index_db2.html 커뮤니티 화면에서 사용)
# ------------------------------------------------------------------

@app.get("/api/posts", response_model=PostListResponseSchema, tags=["Post API"])
def get_posts(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    period: str = Query("all", pattern="^(all|day|week|month|3months|year)$"),
    sort_by: str = Query("recent", pattern="^(recent|views|likes|id|title)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: sqlite3.Connection = Depends(get_post_db),
):
    conditions, params = [], []
    if search:
        conditions.append("(title LIKE ? OR content LIKE ?)"); params.extend([f"%{search}%", f"%{search}%"])
    if tag:
        # 태그는 쉼표로 저장되므로 부분 문자열이 아닌 태그 단위로 비교한다.
        # 예: '#맛' 검색이 '#맛집' 게시글까지 포함되지 않도록 한다.
        normalized_tag = tag.strip().lstrip("#").replace(" ", "")
        if normalized_tag:
            escaped_tag = (
                normalized_tag.replace("\\", "\\\\")
                .replace("%", "\\%").replace("_", "\\_")
            )
            conditions.append(
                "(',' || REPLACE(REPLACE(COALESCE(tags, ''), ' ', ''), '#', '') || ',') "
                "LIKE ? ESCAPE '\\'"
            )
            params.append(f"%,{escaped_tag},%")
    period_modifiers = {
        "day": "-1 day",
        "week": "-7 days",
        "month": "-1 month",
        "3months": "-3 months",
        "year": "-1 year",
    }
    if period in period_modifiers:
        conditions.append("datetime(created_at) >= datetime('now', ?)")
        params.append(period_modifiers[period])
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    order_columns = {
        "recent": "datetime(created_at)", "views": "views", "likes": "likes",
        "id": "id", "title": "title COLLATE NOCASE",
    }
    order_by = f"{order_columns[sort_by]} {sort_order.upper()}, id {sort_order.upper()}"
    total = db.execute(f"SELECT COUNT(*) FROM posts {where_clause}", params).fetchone()[0]
    total_pages = max(1, math.ceil(total / limit))
    page = min(page, total_pages)
    rows = db.execute(
        f"SELECT id, title, content, views, tags, likes, image, created_at FROM posts "
        f"{where_clause} ORDER BY {order_by} LIMIT ? OFFSET ?",
        params + [limit, (page - 1) * limit],
    ).fetchall()
    return {"total": total, "page": page, "limit": limit, "total_pages": total_pages, "items": [dict(row) for row in rows]}


@app.get("/api/posts/{post_id}", response_model=PostResponseSchema, tags=["Post API"])
def get_post_detail(post_id: int, db: sqlite3.Connection = Depends(get_post_db)):
    db.execute("UPDATE posts SET views = views + 1 WHERE id = ?", (post_id,)); db.commit()
    row = db.execute("SELECT id, title, content, views, tags, likes, image, created_at FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not row: raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return dict(row)


@app.post("/api/posts", response_model=PostResponseSchema, status_code=status.HTTP_201_CREATED, tags=["Post API"])
def create_post(post: PostCreateSchema, db: sqlite3.Connection = Depends(get_post_db)):
    cursor = db.execute("INSERT INTO posts (title, content, password, tags, views, likes, image) VALUES (?, ?, ?, ?, 0, 0, ?)", (post.title, post.content, post.password, post.tags, post.image)); db.commit()
    return dict(db.execute("SELECT id, title, content, views, tags, likes, image, created_at FROM posts WHERE id = ?", (cursor.lastrowid,)).fetchone())


@app.put("/api/posts/{post_id}", response_model=PostResponseSchema, tags=["Post API"])
def update_post(post_id: int, updated_data: PostUpdateSchema, db: sqlite3.Connection = Depends(get_post_db)):
    row = db.execute("SELECT password FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not row: raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if row["password"] != updated_data.password: raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않아 수정할 수 없습니다.")
    fields, params = [], []
    for field in ("title", "content", "tags", "image"):
        value = getattr(updated_data, field)
        if value is not None: fields.append(f"{field} = ?"); params.append(value)
    if not fields: raise HTTPException(status_code=400, detail="수정할 내용이 존재하지 않습니다.")
    db.execute(f"UPDATE posts SET {', '.join(fields)} WHERE id = ?", params + [post_id]); db.commit()
    return dict(db.execute("SELECT id, title, content, views, tags, likes, image, created_at FROM posts WHERE id = ?", (post_id,)).fetchone())


@app.delete("/api/posts/{post_id}", tags=["Post API"])
def delete_post(post_id: int, verify: PasswordVerifySchema, db: sqlite3.Connection = Depends(get_post_db)):
    row = db.execute("SELECT password FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not row: raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if row["password"] != verify.password: raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않아 삭제할 수 없습니다.")
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,)); db.commit()
    return {"status": "success", "message": "게시글이 성공적으로 삭제되었습니다."}


@app.post("/api/posts/{post_id}/like", response_model=PostResponseSchema, tags=["Post API"])
def like_post(post_id: int, db: sqlite3.Connection = Depends(get_post_db)):
    if not db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone(): raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    db.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,)); db.commit()
    return dict(db.execute("SELECT id, title, content, views, tags, likes, image, created_at FROM posts WHERE id = ?", (post_id,)).fetchone())


# ------------------------------------------------------------------
# AI 챗봇 API (index_db2.html 우측 하단 챗봇 위젯에서 사용)
# ------------------------------------------------------------------

CONTENT_TYPE_KEYWORDS = {
    "12": {"관광지", "명소", "볼거리", "여행지", "가볼만한곳", "관광"},
    "14": {"문화시설", "문화", "박물관", "미술관", "도서관", "공연장", "전시"},
    "15": {"축제", "공연", "행사", "페스티벌"},
    "25": {"여행코스", "여행 코스", "코스", "투어코스", "관광코스"},
    "28": {"레포츠", "스포츠", "체험", "등산", "캠핑", "자전거", "레저"},
    "32": {"숙박", "호텔", "모텔", "펜션", "게스트하우스", "리조트", "숙소"},
    "38": {"쇼핑", "시장", "백화점", "아울렛", "면세점", "상점"},
    "39": {"음식", "음식점", "맛집", "식당", "레스토랑", "카페", "술집", "한식",
           "중식", "중국집", "일식", "양식", "분식", "고기", "치킨", "피자",
           "햄버거", "칼국수", "국밥", "빵집", "디저트"},
}
TYPE_KEYWORD_TO_ID = {
    keyword.replace(" ", ""): content_type_id
    for content_type_id, keywords in CONTENT_TYPE_KEYWORDS.items()
    for keyword in keywords
}
SEARCH_STOPWORDS = set(TYPE_KEYWORD_TO_ID) | {"추천", "알려줘", "찾아줘", "어디", "근처", "좀", "좋은", "있는"}


def is_search_stopword(token: str) -> bool:
    """'맛집추천', '숙소알려줘'처럼 붙여 쓴 의도 표현도 검색 조건에서 제거한다."""
    return any(stopword in token for stopword in SEARCH_STOPWORDS)


def parse_tour_search(
    search: str,
    location: Optional[str] = None,
    content_type_ids: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    food_only: bool = False,
):
    """자연어 검색어에서 지역과 TourAPI 콘텐츠 유형 조건을 추출한다."""
    normalized = re.sub(r"\s+", " ", (search or "").strip())
    tokens = re.findall(r"[가-힣A-Za-z0-9]+", normalized)
    compact_text = normalized.replace(" ", "")
    inferred_type_ids = {
        content_type_id
        for keyword, content_type_id in TYPE_KEYWORD_TO_ID.items()
        if keyword in compact_text
    }
    if food_only:
        inferred_type_ids.add("39")
    requested_type_ids = {str(value) for value in (content_type_ids or [])}
    type_ids = sorted((inferred_type_ids | requested_type_ids) & set(CONTENT_TYPE_KEYWORDS))

    if location:
        location_terms = [location.strip()]
    else:
        # '봉명동', '유성구'처럼 행정구역 형태인 단어를 지역으로 우선 인식한다.
        location_terms = [token for token in tokens if token.endswith(("동", "읍", "면", "구", "군", "시"))]

    # AI가 질문의 의도를 해석해 전달한 DB 검색어를 우선 사용한다.
    # 예: '봉명동 맛집추천' -> location=['봉명동'], type_ids=['39'], keywords=[]
    if keywords is not None:
        db_keywords = [
            keyword.strip() for keyword in keywords
            if isinstance(keyword, str) and keyword.strip()
        ]
    else:
        db_keywords = [
            token for token in tokens
            if not is_search_stopword(token) and token not in location_terms
        ]
    return location_terms, db_keywords, type_ids


def db_search_tours_internal(
    search: str = "",
    limit: int = 5,
    location: Optional[str] = None,
    content_type_ids: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    food_only: bool = False,
) -> list:
    if not os.path.exists(TOUR_DB_PATH):
        return [{"error": f"데이터베이스 파일({TOUR_DB_PATH})을 찾을 수 없습니다."}]
    location_terms, db_keywords, type_ids = parse_tour_search(
        search, location, content_type_ids, keywords, food_only
    )
    # 모델이 비정상적으로 큰 값을 보내도 DB 검색량을 제한한다.
    limit = max(1, min(int(limit), 10))
    conn = sqlite3.connect(TOUR_DB_PATH); conn.row_factory = sqlite3.Row
    try:
        base_conditions, base_params = [], []

        # 지역은 주소에 우선 적용한다. 예: '봉명동 음식점 추천' -> addr1 LIKE '%봉명동%'.
        for term in location_terms:
            base_conditions.append("(addr1 LIKE ? OR addr2 LIKE ? OR title LIKE ?)")
            base_params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])

        # 지역 외 키워드는 장소명·주소·분류 중 어디에든 포함되도록 한다.
        if type_ids:
            placeholders = ", ".join("?" for _ in type_ids)
            base_conditions.append(f"contenttypeid IN ({placeholders})")
            base_params.extend(type_ids)

        keyword_conditions, keyword_params = [], []
        for term in db_keywords:
            keyword_conditions.append("(title LIKE ? OR addr1 LIKE ? OR addr2 LIKE ? OR cat1 LIKE ? OR cat2 LIKE ? OR cat3 LIKE ?)")
            keyword_params.extend([f"%{term}%"] * 6)

        select_query = """
            SELECT contentid, contenttypeid, region, title, addr1, addr2, zipcode, tel,
                   mapx, mapy, mlevel, cat1, cat2, cat3, firstimage
            FROM pois
        """

        def run_query(conditions, params):
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            return conn.execute(select_query + where_clause + " ORDER BY title LIMIT ?", params + [limit]).fetchall()

        rows = run_query(base_conditions + keyword_conditions, base_params + keyword_params)
        # AI가 '맛집추천', '아이와갈곳'처럼 DB에 없는 수식어를 search에 넣어도,
        # 지역·콘텐츠 유형을 파악했다면 해당 조건만으로 한 번 더 찾아 결과를 제공한다.
        if not rows and db_keywords and base_conditions:
            rows = run_query(base_conditions, base_params)
        return [dict(row) for row in rows]
    except Exception as exc:
        return [{"error": f"조회 중 오류가 발생했습니다: {exc}"}]
    finally:
        conn.close()


def db_search_posts_internal(search: str = "", tag: Optional[str] = None, limit: int = 5) -> list:
    """챗봇용 공개 게시글 조회. 비밀번호와 이미지 데이터는 반환하지 않는다."""
    if not os.path.exists(POST_DB_PATH):
        return [{"error": f"게시글 데이터베이스 파일({POST_DB_PATH})을 찾을 수 없습니다."}]

    limit = max(1, min(int(limit), 10))
    conditions, params = [], []
    keyword = (search or "").strip()
    if keyword:
        conditions.append("(title LIKE ? OR content LIKE ? OR tags LIKE ?)")
        params.extend([f"%{keyword}%"] * 3)
    if tag:
        normalized_tag = tag.strip().lstrip("#").replace(" ", "")
        if normalized_tag:
            escaped_tag = normalized_tag.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            conditions.append(
                "(',' || REPLACE(REPLACE(COALESCE(tags, ''), ' ', ''), '#', '') || ',') "
                "LIKE ? ESCAPE '\\'"
            )
            params.append(f"%,{escaped_tag},%")

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = (
        "SELECT id, title, substr(content, 1, 1000) AS content, tags, views, likes, created_at "
        "FROM posts" + where_clause + " ORDER BY datetime(created_at) DESC, id DESC LIMIT ?"
    )
    conn = sqlite3.connect(POST_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(query, params + [limit]).fetchall()]
    except Exception as exc:
        return [{"error": f"게시글 조회 중 오류가 발생했습니다: {exc}"}]
    finally:
        conn.close()


@app.post("/api/chat", tags=["Chat API"])
async def chat_endpoint(request: ChatRequest):
    if not os.getenv("OPENAI_API_KEY"):
        return {"role": "assistant", "content": "서버에 OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요."}
    messages = [{"role": "system", "content": "당신은 대전광역시 및 충청권 전문 로컬 관광 가이드 이름은 '대롱이'입니다. 친절한 충청도 사투리로 답변하세요. 장소 추천·정보 질문은 반드시 db_search_tours 도구로 실제 데이터베이스를 조회하세요. 도구를 호출하기 전에 사용자 질문의 의미를 분석해 DB 조건으로 변환하세요. 질문 원문을 search나 keywords에 그대로 넣지 마세요. location에는 행정구역만, content_type_ids에는 가장 알맞은 유형 코드만, keywords에는 실제 장소명·음식명처럼 DB에서 찾을 수 있는 핵심어만 넣으세요. 의미상 지역·유형만 필요하면 keywords는 빈 배열로 두세요. 예: '봉명동 맛집추천'은 location='봉명동', content_type_ids=['39'], keywords=[]입니다. '유성구 아이와 갈 박물관'은 location='유성구', content_type_ids=['14'], keywords=[]입니다. 콘텐츠 유형은 관광지=12, 문화시설=14, 축제공연행사=15, 여행코스=25, 레포츠=28, 숙박=32, 쇼핑=38, 음식점=39입니다. 도구 응답에 있는 장소만 추천할 수 있으며, 결과가 빈 배열이면 장소명·주소·전화번호를 추가하거나 이전 대화의 장소를 재사용하지 마세요."}] + [message.model_dump() for message in request.messages]
    tools = [{"type": "function", "function": {"name": "db_search_tours", "description": "대전·충청권 관광 데이터를 구조화된 지역·유형·핵심어 조건으로 조회합니다. 반드시 질문의 의미를 조건으로 변환해 호출합니다.", "parameters": {"type": "object", "properties": {"search": {"type": "string", "description": "하위 호환용 단일 핵심어. 사용자 질문 전체를 넣지 않습니다."}, "location": {"type": "string", "description": "행정동·구 등 지역명. 예: 봉명동"}, "content_type_ids": {"type": "array", "items": {"type": "string", "enum": ["12", "14", "15", "25", "28", "32", "38", "39"]}, "description": "콘텐츠 유형 ID. 관광지 12, 문화시설 14, 축제공연행사 15, 여행코스 25, 레포츠 28, 숙박 32, 쇼핑 38, 음식점 39"}, "keywords": {"type": "array", "items": {"type": "string"}, "description": "DB에서 직접 검색할 핵심 장소명·음식명·테마어만 입력. 추천, 알려줘 같은 의도 표현과 질문 원문은 제외합니다."}, "food_only": {"type": "boolean", "description": "하위 호환용 음식점 필터. 가능하면 content_type_ids=['39']를 사용합니다."}, "limit": {"type": "integer", "minimum": 1, "maximum": 10}}}}}]
    messages.insert(1, {
        "role": "system",
        "content": (
            "커뮤니티 게시글, 후기, 주민 의견, 해시태그, 최근 게시물에 관한 질문은 "
            "반드시 db_search_posts 도구로 post.db를 조회하세요. 게시글 도구 결과에 없는 "
            "사실이나 후기를 만들지 마세요."
        ),
    })
    tools.append({
        "type": "function",
        "function": {
            "name": "db_search_posts",
            "description": "커뮤니티 post.db의 공개 게시글 제목, 본문, 태그, 반응 수를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "제목·본문·태그에서 찾을 핵심어"},
                    "tag": {"type": "string", "description": "정확히 일치시킬 해시태그. #은 생략 가능"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                },
            },
        },
    })
    try:
        client = OpenAI()
        response = client.chat.completions.create(model="gpt-5-mini", messages=messages, tools=tools, tool_choice="auto")
        message = response.choices[0].message
        if not message.tool_calls:
            return {"role": "assistant", "content": message.content}
        messages.append(message)
        for tool_call in message.tool_calls:
            if tool_call.function.name == "db_search_tours":
                arguments = json.loads(tool_call.function.arguments)
                results = db_search_tours_internal(
                    search=arguments.get("search", ""),
                    location=arguments.get("location"),
                    content_type_ids=arguments.get("content_type_ids"),
                    keywords=arguments.get("keywords"),
                    food_only=arguments.get("food_only", False),
                    limit=arguments.get("limit", 5),
                )
                messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": "db_search_tours", "content": json.dumps(results, ensure_ascii=False)})
            elif tool_call.function.name == "db_search_posts":
                arguments = json.loads(tool_call.function.arguments)
                results = db_search_posts_internal(
                    search=arguments.get("search", ""),
                    tag=arguments.get("tag"),
                    limit=arguments.get("limit", 5),
                )
                messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": "db_search_posts", "content": json.dumps(results, ensure_ascii=False)})
        final_response = client.chat.completions.create(model="gpt-5-mini", messages=messages)
        return {"role": "assistant", "content": final_response.choices[0].message.content}
    except Exception as exc:
        return {"role": "assistant", "content": f"대화 처리 중 오류가 발생했습니다: {exc}"}


# ------------------------------------------------------------------
# 시스템 API
# ------------------------------------------------------------------

@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "post_db_connected": os.path.exists(POST_DB_PATH),
        "tour_db_connected": os.path.exists(TOUR_DB_PATH),
        "bus_db_connected": os.path.exists(BUS_DATA_DB_PATH),
    }


# ------------------------------------------------------------------
# 실시간 접속자 수 (웹소켓)
# 접속한 클라이언트 목록을 메모리에 들고 있다가, 누가 붙거나 끊길 때마다
# 현재 인원 수를 전원에게 다시 broadcast한다.
# ------------------------------------------------------------------
_presence_connections: set[WebSocket] = set()


async def _broadcast_presence_count():
    count = len(_presence_connections)
    stale = []
    for ws in _presence_connections:
        try:
            await ws.send_json({"type": "presence", "count": count})
        except Exception:
            stale.append(ws)
    for ws in stale:
        _presence_connections.discard(ws)


@app.websocket("/ws/presence")
async def presence_ws(websocket: WebSocket):
    await websocket.accept()
    _presence_connections.add(websocket)
    await _broadcast_presence_count()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _presence_connections.discard(websocket)
        await _broadcast_presence_count()
