import sqlite3

def update_database():
    conn = sqlite3.connect("adventure.db")
    cursor = conn.cursor()

    # ✅ 기존 테이블에 `characterImg` 필드 추가
    cursor.execute("ALTER TABLE adventurers ADD COLUMN characterImg TEXT;")
    
    conn.commit()
    conn.close()
    print("✅ DB 업데이트 완료: 'characterImg' 필드 추가됨!")

# 실행
update_database()