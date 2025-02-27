# 🚀 Flask 기반 던전앤파이터 파티 자동 편성 웹 서비스

이 프로젝트는 **Railway**에서 배포 가능한 Flask 기반 웹 애플리케이션으로, 던전앤파이터의 모험단 정보를 조회하고 최적의 파티를 자동으로 구성하는 기능을 제공합니다.

---

## ✅ 주요 기능

### 🔹 1. 캐릭터 검색

- 서버 및 닉네임을 입력하면 네오플 API에서 데이터를 가져와 조회 가능
- 데이터가 기존 DB(`sqlite3`)에 없을 경우 자동으로 저장됨

### 🔹 2. 모험단 검색

- 특정 모험단명을 입력하면 저장된 데이터에서 조회 가능
- 저장된 데이터가 없을 경우 오류 메시지 반환

### 🔹 3. 파티 자동 편성

- 모험단 내 버퍼 1명 + 딜러 3명을 자동으로 편성
- 각 캐릭터의 명성을 기준으로 입장 가능한 **최적의 던전 추천**
- **상급 던전**(죽음의 여신전, 애쥬어 메인, 달이 잠긴 호수) 및 **레기온 던전**(베누스 1~2단, 베누스 강림) 자동 판별

### 🔹 4. 다중 캐릭터 입력

- `%` 구분자로 여러 개의 캐릭터를 입력하면 한 번에 검색 가능
- 검색된 결과를 한 화면에 출력

### 🔹 5. 데이터 갱신 (모험단 정보 업데이트)

- 모험단 검색 후 "새로고침" 버튼을 눌러 최신 정보로 갱신 가능

---

## 🚀 Railway 배포 및 실행 방법

### 📌 **1. Railway에 프로젝트 배포하기**

1️⃣ **[Railway.app](https://railway.app/)에 가입 및 로그인**
2️⃣ `New Project` → `Deploy from GitHub repo` 클릭
3️⃣ GitHub에서 해당 저장소 선택 후 배포
4️⃣ **"Deployments" → "Start Command" 설정 변경**

```bash
 gunicorn index:app --bind 0.0.0.0:5000 --timeout 120
```

5️⃣ 배포 완료 후 `https://your-railway-app.up.railway.app/`에서 확인

---

### 📌 **2. 로컬에서 실행하는 방법**

#### **1️⃣ 가상환경 설정 (선택 사항)**

```bash
python -m venv venv  # 가상환경 생성
source venv/bin/activate  # (Linux/macOS)
venv\Scripts\activate  # (Windows)
```

#### **2️⃣ 필요한 패키지 설치**

```bash
pip install -r requirements.txt
```

#### **3️⃣ Flask 실행**

```bash
python index.py  # (로컬 개발용)
```

🚀 서버가 실행되면 `http://127.0.0.1:5000/`에서 확인 가능

---

## ✅ 파일 구조

```
.
├── api/
│   ├── index.py  # Flask 서버
│   ├── templates/
│   │   ├── index.html  # 캐릭터 검색 페이지
│   │   ├── party.html  # 파티 편성 페이지
│   │   ├── multinput.html  # 다중 캐릭터 입력 페이지
├── adventure.db  # SQLite 데이터베이스 (Railway에서는 /data/adventure.db로 변경됨)
├── requirements.txt  # 필요한 패키지 목록
├── README.md  # 프로젝트 설명 파일
```

---

## 🎯 API 엔드포인트

| 기능           | HTTP Method | 엔드포인트                                                 |
| -------------- | ----------- | ---------------------------------------------------------- |
| 캐릭터 검색    | `GET`       | `/search_character?character_name=닉네임&server_id=서버ID` |
| 모험단 검색    | `GET`       | `/search_adventure?adventure_name=모험단명`                |
| 파티 자동 편성 | `GET`       | `/auto_party?adventures=모험단명`                          |
| 데이터 갱신    | `GET`       | `/refresh_adventure?adventure_name=모험단명`               |

---

## 🚀 **배포된 Railway URL 예시**

```
https://your-railway-app.up.railway.app/
https://your-railway-app.up.railway.app/search_adventure?adventure_name=테스트모험단
https://your-railway-app.up.railway.app/auto_party?adventures=테스트모험단
```
