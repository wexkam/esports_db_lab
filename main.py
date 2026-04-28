from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import psycopg2

app = FastAPI()

class MatchSchema(BaseModel):
    team_id: int
    match_code: str
    stage: str
    result_1: int = 0
    result_2: int = 0
    maps: Optional[str] = None

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
        conn.close() # <--- ГАРАНТИРОВАННОЕ ЗАКРЫТИЕ

# 3. Обновить команду (UPDATE)
@app.put("/api/teams/{team_id}")
def update_team(team_id: int, team: TeamSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE team SET title=%s, coach=%s, region=%s, foundation_date=%s WHERE team_id=%s',
            (team.title, team.coach, team.region, team.foundation_date, team_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Team not found")
        conn.commit()
        return {"status": "updated"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

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
        raise HTTPException(status_code=400, detail="Error: possible related data")
    finally:
        cursor.close()
        conn.close()

@app.get("/api/matches")
def get_matches():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Используем INNER JOIN, чтобы достать название команды
    query = """
        SELECT m.match_id, m.match_code, m.stage, m.result_1, m.result_2, m.maps, 
               t.team_id, t.title 
        FROM match m
        INNER JOIN team t ON m.team_id = t.team_id
    """
    cursor.execute(query)
    result = cursor.fetchall()
    
    res = []
    for row in result:
        res.append({
            "match_id": row[0],
            "match_code": row[1],
            "stage": row[2],
            "score": f"{row[3]}:{row[4]}",
            "maps": row[5],
            "team": {
                "id": row[6],
                "name": row[7]
            }
        })
    cursor.close()
    conn.close()
    return JSONResponse(content=jsonable_encoder(res))

@app.post("/api/matches")
def create_match(match: MatchSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Проверяем, существует ли такая команда
        cursor.execute("SELECT team_id FROM team WHERE team_id = %s", (match.team_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Team not found. Cannot create match.")
            
        cursor.execute(
            'INSERT INTO match (team_id, match_code, stage, result_1, result_2, maps) VALUES (%s, %s, %s, %s, %s, %s) RETURNING match_id',
            (match.team_id, match.match_code, match.stage, match.result_1, match.result_2, match.maps)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "success", "match_id": new_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/api/matches/{match_id}")
def update_match(match_id: int, match: MatchSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT team_id FROM team WHERE team_id = %s", (match.team_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Team not found")

        cursor.execute(
            'UPDATE match SET team_id=%s, match_code=%s, stage=%s, result_1=%s, result_2=%s, maps=%s WHERE match_id=%s',
            (match.team_id, match.match_code, match.stage, match.result_1, match.result_2, match.maps, match_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Match not found")
        conn.commit()
        return {"status": "updated"}
    finally:
        cursor.close()
        conn.close()

@app.delete("/api/matches/{match_id}")
def delete_match(match_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM match WHERE match_id = %s', (match_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Match not found")
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "deleted"}

@app.put("/api/teams/{team_id}/attach/player/{player_id}")
def attach_player_to_team(team_id: int, player_id: int, join_date: str = "2024-01-01"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT player_id FROM player WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Player not found")
        
        cursor.execute("SELECT team_id FROM team WHERE team_id = %s", (team_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Team not found")

        cursor.execute(
            "INSERT INTO player_team (player_id, team_id, join_date) VALUES (%s, %s, %s)",
            (player_id, team_id, join_date)
        )
        conn.commit()
        return {"status": "success", "message": "Player attached to team"}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="This player is already in this team on this date")
    finally:
        cursor.close()
        conn.close()

# Удалить запись о нахождении игрока в команде (Detach)
@app.put("/api/teams/{team_id}/detach/player/{player_id}")
def detach_player_from_team(team_id: int, player_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM player_team WHERE team_id = %s AND player_id = %s",
        (team_id, player_id)
    )
    res = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "deleted_rows": res}

@app.get("/api/teams/{team_id}/players")
def get_team_players(team_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT p.player_id, p.nickname, p.role, pt.join_date 
        FROM player p
        INNER JOIN player_team pt ON p.player_id = pt.player_id
        WHERE pt.team_id = %s
    """
    cursor.execute(query, (team_id,))
    result = cursor.fetchall()
    res = []
    for row in result:
        res.append({"id": row[0], "nickname": row[1], "role": row[2], "joined": str(row[3])})
    cursor.close()
    conn.close()
    return res