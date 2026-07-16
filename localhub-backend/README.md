# LocalHub Backend (FastAPI, Render 배포용)

기존 `main.py`에서 프론트엔드 HTML(`index_db2.html`, `kakaomap.html`)을 직접 서빙하던 부분
(Jinja2 템플릿, `/css` `/img` 정적 마운트, `/`, `/kakaomap.html` 라우트)을 제거하고,
순수 API + WebSocket 서버로 정리했습니다. 프론트엔드는 Netlify에 별도로 배포됩니다.

## 변경 사항 요약

- `CORSMiddleware`의 `allow_origins`를 `"*"` 대신 `FRONTEND_ORIGINS` 환경변수 기반으로 변경
  (Netlify 도메인만 명시적으로 허용)
- Jinja2/StaticFiles/`css`,`img` 폴더 자동 생성 로직 제거
- `/` 는 안내용 헬스체크 JSON을 반환하도록 변경 (`/docs`에서 Swagger UI 확인 가능)
- 나머지 `/api/*`, `/ws/presence` 로직은 원본과 동일

## 로컬 실행

```bash
python -m venv .venv && source .venv/bin/activate  # Windows는 .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # 값 채워넣기
uvicorn main:app --reload
```

`data/tour_data.db`, `data/bus_data.db` 파일이 `data/` 폴더에 있어야 관광지/버스 API가 동작합니다
(원본 프로젝트에서 그대로 복사해오세요). `data/post.db`는 최초 실행 시 자동 생성됩니다.

## Render 배포

1. 이 폴더를 GitHub 저장소로 푸시 (`data/tour_data.db`, `data/bus_data.db` 포함해서 커밋)
2. Render 대시보드 → New → Blueprint → 저장소 선택 (`render.yaml` 자동 인식)
   - 또는 New → Web Service 로 수동 생성 시:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Environment 탭에서 값 등록
   - `FRONTEND_ORIGINS` = Netlify 배포 주소 (예: `https://your-app.netlify.app`)
   - `OPENAI_API_KEY` = 챗봇용 OpenAI API 키
4. 배포 완료 후 나오는 주소(`https://xxx.onrender.com`)를 프론트엔드의 `VITE_API_BASE_URL`에 설정

## 알아둘 점 (무료 플랜 한계)

Render 무료 웹서비스 플랜은 영구 디스크를 지원하지 않습니다. 즉:
- 서버가 슬립 후 다시 깨어나거나 재배포되면 `data/post.db`에 새로 쓴 게시글이 초기화될 수 있습니다.
- 게시판 데이터를 영구 보관하려면 유료 플랜의 Persistent Disk를 추가하거나,
  SQLite 대신 Render의 관리형 PostgreSQL 등으로 교체하는 것을 권장합니다.
- `tour_data.db`, `bus_data.db`는 읽기 전용 시드 데이터이므로 git에 커밋되어 있기만 하면
  재배포되어도 계속 사용 가능합니다 (`.gitignore`에서 제외되지 않았는지 확인하세요).
