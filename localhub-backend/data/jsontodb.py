import json
import sqlite3
import glob
import os

# 💡 여기에 실제 JSON 파일들이 들어있는 폴더 경로를 적어주세요.
# 예: "C:/Users/MyName/Desktop/tour_folder" (윈도우의 경우 슬래시 / 사용 권장)
JSON_FOLDER_PATH = "./"  # 현재 폴더 기준일 때는 "./"

def convert_json_to_sqlite(db_name="tour_data.db"):
    # 1. SQLite 데이터베이스 연결
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 테이블 및 인덱스 생성
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pois (
        contentid TEXT PRIMARY KEY,
        contenttypeid TEXT NOT NULL,
        region TEXT NOT NULL,
        title TEXT NOT NULL,
        addr1 TEXT,
        addr2 TEXT,
        zipcode TEXT,
        tel TEXT,
        mapx REAL,
        mapy REAL,
        mlevel TEXT,
        areacode TEXT,
        sigungucode TEXT,
        lDongRegnCd TEXT,
        lDongSignguCd TEXT,
        cat1 TEXT,
        cat2 TEXT,
        cat3 TEXT,
        lclsSystm1 TEXT,
        lclsSystm2 TEXT,
        lclsSystm3 TEXT,
        firstimage TEXT,
        firstimage2 TEXT,
        cpyrhtDivCd TEXT,
        createdtime TEXT,
        modifiedtime TEXT,
        eventstartdate TEXT,
        eventenddate TEXT,
        eventplace TEXT
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pois_region ON pois(region);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pois_contenttypeid ON pois(contenttypeid);")
    conn.commit()

    # 2. 지정된 경로에서 모든 JSON 파일 검색
    search_path = os.path.join(JSON_FOLDER_PATH, "*.json")
    json_files = glob.glob(search_path)
    
    # 🔍 진단용 출력 추가: 현재 탐색하는 경로를 터미널에 보여줍니다.
    print(f"[시스템] 탐색 대상 경로: {os.path.abspath(JSON_FOLDER_PATH)}")
    
    if not json_files:
        print("[경고] 지정된 폴더에 변환할 JSON 파일이 단 하나도 존재하지 않습니다!")
        print(" -> JSON_FOLDER_PATH 경로 설정이 올바른지 다시 확인해 주세요.")
        conn.close()
        return

    print(f"[성공] 총 {len(json_files)}개의 JSON 파일을 찾았습니다. 변환을 시작합니다.\n")
    
    total_inserted = 0

    for file_path in json_files:
        filename = os.path.basename(file_path)
        print(f"-> {filename} 처리 중...")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                region = data.get("region")
                items = data.get("items", [])
                
                if not region:
                    print(f"   [경고] {filename} 파일에 'region' 정보가 없어 스킵합니다.")
                    continue
                
                file_inserted = 0
                for item in items:
                    mapx_raw = item.get("mapx")
                    mapy_raw = item.get("mapy")
                    
                    try:
                        mapx = float(mapx_raw) if mapx_raw and mapx_raw.strip() else None
                        mapy = float(mapy_raw) if mapy_raw and mapy_raw.strip() else None
                    except ValueError:
                        mapx, mapy = None, None
                    
                    cursor.execute("""
                    INSERT OR REPLACE INTO pois (
                        contentid, contenttypeid, region, title, addr1, addr2, zipcode, tel,
                        mapx, mapy, mlevel, areacode, sigungucode, lDongRegnCd, lDongSignguCd,
                        cat1, cat2, cat3, lclsSystm1, lclsSystm2, lclsSystm3,
                        firstimage, firstimage2, cpyrhtDivCd, createdtime, modifiedtime,
                        eventstartdate, eventenddate, eventplace
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.get("contentid"),
                        item.get("contenttypeid"),
                        region,
                        item.get("title"),
                        item.get("addr1"),
                        item.get("addr2"),
                        item.get("zipcode"),
                        item.get("tel"),
                        mapx,
                        mapy,
                        item.get("mlevel"),
                        item.get("areacode"),
                        item.get("sigungucode"),
                        item.get("lDongRegnCd"),
                        item.get("lDongSignguCd"),
                        item.get("cat1"),
                        item.get("cat2"),
                        item.get("cat3"),
                        item.get("lclsSystm1"),
                        item.get("lclsSystm2"),
                        item.get("lclsSystm3"),
                        item.get("firstimage"),
                        item.get("firstimage2"),
                        item.get("cpyrhtDivCd"),
                        item.get("createdtime"),
                        item.get("modifiedtime"),
                        item.get("eventstartdate"),
                        item.get("eventenddate"),
                        item.get("eventplace")
                    ))
                    file_inserted += 1
                
                print(f"   ㄴ 완료: {file_inserted}개 항목 저장")
                total_inserted += file_inserted

        except json.JSONDecodeError:
            print(f"   [오류] {filename} 파일이 올바른 JSON 형식이 아닙니다.")
        except Exception as e:
            print(f"   [오류] {filename} 처리 중 에러 발생: {e}")

    conn.commit()
    conn.close()
    
    print("\n========================================")
    print(f"작업 완료! 생성된 DB 파일: {os.path.abspath(db_name)}")
    print(f"총 처리된 데이터 항목 수: {total_inserted}개")
    print("========================================")

if __name__ == "__main__":
    convert_json_to_sqlite()