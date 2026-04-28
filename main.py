from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import psycopg2

app = FastAPI()

# Схема данных для Команды (чтобы FastAPI понимал, какие поля мы присылаем)
class TeamSchema(BaseModel):
    title: str
    coach: Optional[str] = None
    region: Optional[str] = None
    foundation_date: Optional[str] = None # формат ГГГГ-ММ-ДД

def get_db_connection():
    return psycopg2.connect("postgresql://localhost/esports_db")

# 1. Получить все команды (READ)
@app.get("/api/teams")
def get_teams():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT team_id, title, coach, region, foundation_date FROM team ORDER BY team_id')
    result = cursor.fetchall()
    res = []
    for row in result:
        res.append({'team_id': row[0], 'title': row[1], 'coach': row[2], 'region': row[3], 'foundation_date': str(row[4])})
    cursor.close()
    conn.close()
    return JSONResponse(content=jsonable_encoder(res))

# 2. Создать новую команду (CREATE)
@app.post("/api/teams")
def create_team(team: TeamSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO team (title, coach, region, foundation_date) VALUES (%s, %s, %s, %s) RETURNING team_id',
            (team.title, team.coach, team.region, team.foundation_date)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "success", "team_id": new_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# 3. Обновить команду (UPDATE)
@app.put("/api/teams/{team_id}")
def update_team(team_id: int, team: TeamSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE team SET title=%s, coach=%s, region=%s, foundation_date=%s WHERE team_id=%s',
        (team.title, team.coach, team.region, team.foundation_date, team_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Team not found")
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "updated"}

# 4. Удалить команду (DELETE)
@app.delete("/api/teams/{team_id}")
def delete_team(team_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM team WHERE team_id = %s', (team_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Team not found")
        conn.commit()
        return {"status": "deleted"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete team (it might have related matches)")
    finally:
        cursor.close()
        conn.close()