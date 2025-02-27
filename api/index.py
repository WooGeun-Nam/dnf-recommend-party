from flask import Flask, request, render_template, jsonify
import sqlite3
import requests
import os

# ✅ 현재 스크립트 실행 디렉토리에 있는 adventure.db 파일을 사용하도록 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = "/data/adventure.db"  # ✅ Railway에서 영구 저장 가능

def get_db_connection():
    """SQLite DB 연결을 반환하는 함수"""
    return sqlite3.connect(DB_PATH)

app = Flask(__name__)

# ✅ 버퍼 직업 목록
BUFFER_JOBS = ["眞 크루세이더", "眞 인챈트리스", "眞 뮤즈"]

# ✅ 네오플 API 설정
NEOPLE_API_KEY = "W2HjAdMmD01JCEwoCV1DApnLsXmtXSjL"
BASE_URL = "https://api.neople.co.kr/df"

# ✅ 상급 던전 입장 제한 명성 값
HIGH_LEVEL_DUNGEONS = [
    ("죽음의 여신전", 48988),
    ("애쥬어 메인", 44929),
    ("달이 잠긴 호수", 34749)
]


# ✅ 레기온 던전 (베누스 단계별 명성 제한)
LEGION_DUNGEONS = [
    ("베누스 강림", 54580),
    ("베누스 2단", 51527),
    ("베누스 1단", 41929)
]

# ✅ 서버 목록 (드롭다운에서 사용)
SERVER_LIST = [
    {"serverId": "anton", "serverName": "안톤"},
    {"serverId": "bakal", "serverName": "바칼"},
    {"serverId": "cain", "serverName": "카인"},
    {"serverId": "casillas", "serverName": "카시야스"},
    {"serverId": "diregie", "serverName": "디레지에"},
    {"serverId": "hilder", "serverName": "힐더"},
    {"serverId": "prey", "serverName": "프레이"},
    {"serverId": "siroco", "serverName": "시로코"}
]

# ✅ 서버 실행 시 DB를 유지하면서, 테이블이 없을 때만 생성하도록 수정
def init_db():
    """DB 초기화 (이미 존재하면 유지)"""
    if not os.path.exists(DB_PATH):
        print(f"🔹 데이터베이스 파일이 존재하지 않음. 새로 생성: {DB_PATH}")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS adventurers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                characterId TEXT UNIQUE,
                adventureName TEXT,
                characterName TEXT,
                serverId TEXT,
                jobName TEXT,
                jobGrowName TEXT,
                characterImg TEXT,
                fame INTEGER DEFAULT 0,
                role TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ 데이터베이스 초기화 완료.")
    else:
        print(f"✅ 기존 데이터베이스 사용 중: {DB_PATH}")

# ✅ 서버 실행 시 DB 초기화
init_db()

@app.route("/")
def index():
    return render_template("index.html", servers=SERVER_LIST)

@app.route("/party")
def party():
    return render_template("party.html")

@app.route("/multinput")
def multinput():
    return render_template("multinput.html", servers=SERVER_LIST)

# 캐릭터 정보를 DB에 저장하거나 업데이트하는 함수 (characterId 기준, fame 포함)
def save_adventurer(character_id, adventure_name, character_name, server_id, job_name, job_grow_name, character_img, fame):
    conn = sqlite3.connect("adventure.db")
    cursor = conn.cursor()
    cursor.execute("SELECT characterId FROM adventurers WHERE characterId = ?", (character_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE adventurers 
            SET adventureName = ?, characterName = ?, jobName = ?, jobGrowName = ?, characterImg = ?, fame = ?
            WHERE characterId = ?
        """, (adventure_name, character_name, job_name, job_grow_name, character_img, fame, character_id))
    else:
        cursor.execute("""
            INSERT INTO adventurers (characterId, adventureName, characterName, serverId, jobName, jobGrowName, characterImg, fame) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (character_id, adventure_name, character_name, server_id, job_name, job_grow_name, character_img, fame))
    conn.commit()
    conn.close()

# 캐릭터 검색 API
@app.route("/search_character", methods=["GET"])
def search_character_api():
    character_name = request.args.get("character_name")
    server_id = request.args.get("server_id")
    results = []
    
    # 서버 선택이 "all"이면 전체 서버, 아니면 SERVER_LIST에서 해당 서버 정보를 가져옴
    if server_id == "all":
        target_servers = SERVER_LIST
    else:
        target = next((s for s in SERVER_LIST if s["serverId"] == server_id), {"serverId": server_id, "serverName": server_id})
        target_servers = [target]

    for server in target_servers:
        srv_id = server["serverId"]
        server_name = server["serverName"]
        url = f"{BASE_URL}/servers/{srv_id}/characters?characterName={character_name}&apikey={NEOPLE_API_KEY}"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
        except Exception as e:
            print(f"Error fetching characters from server {srv_id}: {e}")
            continue

        if "rows" in data and len(data["rows"]) > 0:
            for char_info in data["rows"]:
                character_id = char_info["characterId"]
                detail_url = f"{BASE_URL}/servers/{srv_id}/characters/{character_id}?apikey={NEOPLE_API_KEY}"
                try:
                    detail_response = requests.get(detail_url, timeout=5)
                    detail_data = detail_response.json()
                except Exception as e:
                    print(f"Error fetching detail for character {character_id}: {e}")
                    continue

                final_job_name = detail_data.get("jobGrowName", "알 수 없음")
                fame = detail_data.get("fame", 0)
                character_img_url = f"https://img-api.neople.co.kr/df/servers/{srv_id}/characters/{character_id}"
                adventure_name = detail_data.get("adventureName", "없음")

                # 캐릭터 정보 저장 및 업데이트
                save_adventurer(character_id, adventure_name, character_name, srv_id,
                                char_info["jobName"], final_job_name, character_img_url, fame)

                results.append({
                    "characterName": character_name,
                    "serverName": server_name,
                    "jobName": final_job_name,
                    "adventureName": adventure_name,
                    "fame": fame,
                    "characterImg": character_img_url
                })

    if results:
        return jsonify(results)
    return jsonify({"error": "해당 캐릭터를 찾을 수 없습니다."})

# ✅ 모험단 검색 (DB에서 조회)
@app.route("/search_adventure", methods=["GET"])
def search_adventure_api():
    adventure_name = request.args.get("adventure_name")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT adventureName, characterName, serverId, jobGrowName, characterImg, fame FROM adventurers WHERE adventureName = ?", (adventure_name,))
    db_results = cursor.fetchall()
    conn.close()

    if not db_results:
        return jsonify({"error": "저장된 모험단 정보가 없습니다."})

    results = []
    for char_advName, char_name, server_id, job_grow_name, character_img, fame in db_results:
        server_name = next((s["serverName"] for s in SERVER_LIST if s["serverId"] == server_id), server_id)
        results.append({
            "adventureName" : char_advName,
            "characterName": char_name,
            "serverName": server_name,
            "jobName": job_grow_name,
            "characterImg": character_img,
            "fame": fame
        })

    return jsonify(results)

# ✅ 특정 모험단 캐릭터 가져오기
def get_adventure_characters(adventure_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ `role`을 조회하는 대신, jobGrowName만 가져옴
    cursor.execute("""
        SELECT characterName, jobGrowName, fame, characterImg
        FROM adventurers
        WHERE adventureName = ?
        ORDER BY fame DESC
    """, (adventure_name,))

    characters = cursor.fetchall()
    conn.close()

    # ✅ 직업군을 기반으로 버퍼/딜러 역할 부여
    character_list = [
        {
            "name": row[0],
            "job": row[1],
            "fame": row[2],
            "image": row[3],
            "role": "버퍼" if row[1] in BUFFER_JOBS else "딜러"  # ✅ `BUFFER_JOBS` 기준으로 역할 자동 설정
        }
        for row in characters
    ]

    return character_list

@app.route("/refresh_adventure", methods=["GET"])
def refresh_adventure():
    adventure_name = request.args.get("adventure_name")
    if not adventure_name:
        return jsonify({"error": "모험단 이름을 입력하세요."})

    # DB에서 해당 모험단에 속한 캐릭터 목록 조회 (characterId, characterName, serverId)
    conn = sqlite3.connect("adventure.db")
    cursor = conn.cursor()
    cursor.execute("SELECT characterId, characterName, serverId FROM adventurers WHERE adventureName = ?", (adventure_name,))
    characters = cursor.fetchall()
    conn.close()

    if not characters:
        return jsonify({"error": "모험단 정보를 찾을 수 없습니다."})

    updated_characters = []

    # 각 캐릭터의 최신 정보 API 호출 및 DB 업데이트
    for character_id, character_name, server_id in characters:
        detail_url = f"{BASE_URL}/servers/{server_id}/characters/{character_id}?apikey={NEOPLE_API_KEY}"
        try:
            detail_response = requests.get(detail_url, timeout=5)
            if detail_response.status_code != 200:
                print(f"Error fetching detail for {character_name} ({character_id}) from server {server_id}")
                continue
            detail_data = detail_response.json()
        except Exception as e:
            print(f"Exception while fetching detail for {character_name} ({character_id}): {e}")
            continue

        final_job_name = detail_data.get("jobGrowName", "알 수 없음")
        fame = detail_data.get("fame", 0)
        character_img_url = f"https://img-api.neople.co.kr/df/servers/{server_id}/characters/{character_id}"

        # DB 업데이트: 해당 캐릭터의 최신 정보로 덮어쓰기
        conn = sqlite3.connect("adventure.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE adventurers
            SET jobGrowName = ?, fame = ?, characterImg = ?
            WHERE characterId = ?
        """, (final_job_name, fame, character_img_url, character_id))
        conn.commit()
        conn.close()

        updated_characters.append({
            "characterName": character_name,
            "serverName": next((s["serverName"] for s in SERVER_LIST if s["serverId"] == server_id), server_id),
            "jobName": final_job_name,
            "fame": fame,
            "characterImg": character_img_url
        })

    if not updated_characters:
        return jsonify({"error": "캐릭터 정보를 업데이트할 수 없습니다."})
    
    return jsonify(updated_characters)

# ✅ 파티 자동 편성 (버퍼 1 + 딜러 3)
def create_parties(adventure_name):
    characters = get_adventure_characters(adventure_name)

    buffers = [char for char in characters if char["role"] == "버퍼"]
    dealers = [char for char in characters if char["role"] == "딜러"]

    parties = []
    party_count = 1
    buffer_idx = 0

    for i in range(0, len(dealers), 3):
        if buffer_idx >= len(buffers):
            break

        # 파티 멤버 구성 (버퍼 1 + 딜러 3)
        members = [buffers[buffer_idx]] + dealers[i:i+3]

        # ✅ 파티 내 가장 낮은 명성 값 기준으로 던전 추천
        min_fame = min(member["fame"] for member in members)

        party = {
            "partyNumber": party_count,
            "members": members,
            "eligibleHighLevelDungeons": get_eligible_dungeons(min_fame, HIGH_LEVEL_DUNGEONS),
            "eligibleLegionDungeons": get_eligible_dungeons(min_fame, LEGION_DUNGEONS)
        }
        parties.append(party)
        party_count += 1
        buffer_idx += 1

    return parties

# ✅ API: 모험단명을 받아서 파티 구성
@app.route('/auto_party', methods=['GET'])
def auto_party():
    adventure_name = request.args.get("adventures", "").strip()

    if not adventure_name:
        return jsonify({"error": "모험단명을 입력해주세요."}), 400

    parties = create_parties(adventure_name)

    if not parties:
        return jsonify({"error": "해당 모험단의 데이터를 찾을 수 없습니다."}), 404

    return jsonify(parties)

# ✅ 입장 가능 던전 추천 함수 (상급 던전 & 레기온 던전)
def get_eligible_dungeons(min_fame, dungeon_list):
    """
    파티 내 가장 낮은 명성을 기준으로,
    입장 가능한 던전 중 가장 상위 2개만 반환합니다.
    """
    # ✅ 리스트 형태로 된 던전 데이터를 안전하게 처리
    if not isinstance(dungeon_list, list):
        print(f"❌ 잘못된 dungeon_list 전달됨: {dungeon_list}")  # 디버깅용 출력
        return []

    # ✅ 입장 가능한 던전 필터링
    eligible = []
    for dungeon_data in dungeon_list:
        if isinstance(dungeon_data, tuple) and len(dungeon_data) == 2:
            dungeon, threshold = dungeon_data
            if min_fame >= threshold:
                eligible.append(dungeon)

    return eligible[:2]  # ✅ 최상위 2개 던전만 반환

app = Flask(__name__)