from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import os
from supabase import create_client
from dotenv import load_dotenv

# 환경 변수 로드 (.env 파일에 SUPABASE_URL, SUPABASE_KEY, NEOPLE_API_KEY 등을 설정)
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")  # templates 폴더에 index.html, party.html, multinput.html 배치

# ✅ 버퍼 직업 목록
BUFFER_JOBS = ["眞 크루세이더", "眞 인챈트리스", "眞 뮤즈"]

# ✅ 네오플 API 설정 (환경 변수에서 API 키 불러오기)
NEOPLE_API_KEY = os.getenv("NEOPLE_API_KEY")
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

# ✅ Supabase 클라이언트 생성
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------
# 템플릿 렌더링 엔드포인트
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "servers": SERVER_LIST})

@app.get("/party", response_class=HTMLResponse)
async def party(request: Request):
    return templates.TemplateResponse("party.html", {"request": request})

@app.get("/multinput", response_class=HTMLResponse)
async def multinput(request: Request):
    return templates.TemplateResponse("multinput.html", {"request": request, "servers": SERVER_LIST})

# ---------------------------------------------------------------------
# Supabase를 사용하여 캐릭터 정보를 저장하거나 업데이트
def save_adventurer(character_id, adventure_name, character_name, server_id, job_name, job_grow_name, character_img, fame):
    data = {
        "characterId": character_id,
        "adventureName": adventure_name,
        "characterName": character_name,
        "serverId": server_id,
        "jobName": job_name,
        "jobGrowName": job_grow_name,
        "characterImg": character_img,
        "fame": fame
    }
    supabase.table("adventurers").upsert(data).execute()

# ---------------------------------------------------------------------
# 캐릭터 검색 API
@app.get("/search_character")
async def search_character_api(character_name: str = Query(...), server_id: str = Query(...)):
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
                adv_name = detail_data.get("adventureName", "없음")

                # 캐릭터 정보 저장 및 업데이트 (Supabase 사용)
                save_adventurer(character_id, adv_name, character_name, srv_id,
                                char_info["jobName"], final_job_name, character_img_url, fame)

                results.append({
                    "characterName": character_name,
                    "serverName": server_name,
                    "jobName": final_job_name,
                    "adventureName": adv_name,
                    "fame": fame,
                    "characterImg": character_img_url
                })

    if results:
        return JSONResponse(content=results)
    return JSONResponse(content={"error": "해당 캐릭터를 찾을 수 없습니다."})

# ---------------------------------------------------------------------
# 모험단 검색 API
@app.get("/search_adventure")
async def search_adventure_api(adventure_name: str = Query(...)):
    response = supabase.table("adventurers") \
                .select("adventureName, characterName, serverId, jobGrowName, characterImg, fame") \
                .eq("adventureName", adventure_name).execute()
    db_results = response.data
    if not db_results:
        return JSONResponse(content={"error": "저장된 모험단 정보가 없습니다."})
    results = []
    for record in db_results:
        server_id = record.get("serverId")
        server_name = next((s["serverName"] for s in SERVER_LIST if s["serverId"] == server_id), server_id)
        results.append({
            "adventureName": record.get("adventureName"),
            "characterName": record.get("characterName"),
            "serverName": server_name,
            "jobName": record.get("jobGrowName"),
            "characterImg": record.get("characterImg"),
            "fame": record.get("fame")
        })
    return JSONResponse(content=results)

# ---------------------------------------------------------------------
# 특정 모험단 캐릭터 가져오기 (Supabase 쿼리 사용)
def get_adventure_characters(adventure_name):
    response = supabase.table("adventurers") \
                .select("characterName, jobGrowName, fame, characterImg") \
                .eq("adventureName", adventure_name) \
                .order("fame", desc=True).execute()
    characters = response.data
    if not characters:
        return []
    character_list = [
        {
            "name": rec.get("characterName"),
            "job": rec.get("jobGrowName"),
            "fame": rec.get("fame"),
            "image": rec.get("characterImg"),
            "role": "버퍼" if rec.get("jobGrowName") in BUFFER_JOBS else "딜러"
        }
        for rec in characters
    ]
    return character_list

# ---------------------------------------------------------------------
# 모험단 새로고침 API (Supabase 업데이트 사용)
@app.get("/refresh_adventure")
async def refresh_adventure(adventure_name: str = Query(...)):
    response = supabase.table("adventurers") \
                .select("characterId, characterName, serverId") \
                .eq("adventureName", adventure_name).execute()
    characters = response.data
    if not characters:
        return JSONResponse(content={"error": "모험단 정보를 찾을 수 없습니다."})
    
    updated_characters = []
    for record in characters:
        character_id = record.get("characterId")
        character_name = record.get("characterName")
        server_id = record.get("serverId")
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

        update_data = {
            "jobGrowName": final_job_name,
            "fame": fame,
            "characterImg": character_img_url
        }
        supabase.table("adventurers").update(update_data).eq("characterId", character_id).execute()

        updated_characters.append({
            "characterName": character_name,
            "serverName": next((s["serverName"] for s in SERVER_LIST if s["serverId"] == server_id), server_id),
            "jobName": final_job_name,
            "fame": fame,
            "characterImg": character_img_url
        })
    
    if not updated_characters:
        return JSONResponse(content={"error": "캐릭터 정보를 업데이트할 수 없습니다."})
    
    return JSONResponse(content=updated_characters)

# ---------------------------------------------------------------------
# 파티 자동 편성 (버퍼 1 + 딜러 3)
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
        members = [buffers[buffer_idx]] + dealers[i:i+3]
        # 파티 내 최소 명성을 기준으로 입장 가능한 던전 추천
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

@app.get("/auto_party")
async def auto_party(adventures: str = Query(...)):
    adventure_name = adventures.strip()
    if not adventure_name:
        raise HTTPException(status_code=400, detail="모험단명을 입력해주세요.")
    parties = create_parties(adventure_name)
    if not parties:
        raise HTTPException(status_code=404, detail="해당 모험단의 데이터를 찾을 수 없습니다.")
    return JSONResponse(content=parties)

# ---------------------------------------------------------------------
# 입장 가능 던전 추천 함수
def get_eligible_dungeons(min_fame, dungeon_list):
    if not isinstance(dungeon_list, list):
        print(f"❌ 잘못된 dungeon_list 전달됨: {dungeon_list}")
        return []
    eligible = []
    for dungeon_data in dungeon_list:
        if isinstance(dungeon_data, tuple) and len(dungeon_data) == 2:
            dungeon, threshold = dungeon_data
            if min_fame >= threshold:
                eligible.append(dungeon)
    return eligible[:2]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
