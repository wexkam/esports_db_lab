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
    foundation_date: Optional[str] = None 

class PlayerSchema(BaseModel):
    nickname: str
    full_name: Optional[str] = None
    role: Optional[str] = None

def get_db_connection():
    return psycopg2.connect("postgresql://localhost/esports_db")

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


@app.get("/api/teams/search")
def search_teams(
    title: str = None, 
    region: str = None, 
    order_by: str = "team_id", 
    limit: int = 5,         
    offset: int = 0
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    filters = ["1=1"]
    params = []
    
    if title:
        filters.append("title ILIKE %s")
        params.append(f"%{title}%")
    if region:
        filters.append("region ILIKE %s")
        params.append(f"%{region}%")
        
    where_clause = " AND ".join(filters)

    allowed_columns = ["team_id", "title", "foundation_date"]
    if order_by not in allowed_columns:
        order_by = "team_id"

    sql = f"""
        SELECT team_id, title, coach, region, foundation_date 
        FROM team 
        WHERE {where_clause}
        ORDER BY {order_by}
        LIMIT %s OFFSET %s
    """
    
    cursor.execute(sql, params + [limit, offset])
    result = cursor.fetchall()
    
    res = []
    for row in result:
        res.append({
            'team_id': row[0], 'title': row[1], 'coach': row[2], 
            'region': row[3], 'foundation_date': str(row[4])
        })
    
    cursor.close()
    conn.close()
    return {"results": res, "limit": limit, "offset": offset}

@app.get("/api/lab6/triangle-calc")
def lab6_task1(a: float, b: float, angle: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("CALL calculate_triangle_params(%s::numeric, %s::numeric, %s::numeric, NULL, NULL)", (a, b, angle))
        res = cursor.fetchone()
        return {"side_c": float(res[0]), "area": float(res[1])}
    finally:
        cursor.close()
        conn.close()

@app.get("/api/lab6/triangle-type")
def lab6_task2(a: float, b: float, c: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("CALL get_triangle_type_full(%s::numeric, %s::numeric, %s::numeric, NULL)", (a, b, c))
        res = cursor.fetchone()
        return {"type": res[0]}
    finally:
        cursor.close()
        conn.close()

@app.get("/api/lab6/best-base")
def lab6_task3(n: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT get_max_sum_base(%s)", (n,))
        return {"best_base": cursor.fetchone()[0]}
    finally:
        cursor.close()
        conn.close()

@app.post("/api/lab6/block-inactive")
def lab6_task4():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("CALL archive_inactive_players()")
        conn.commit()
        return {"status": "success"}
    finally:
        cursor.close()
        conn.close()

@app.post("/api/lab6/login")
def lab6_task5(login: str, password: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT auth_player(%s, %s)", (login, password))
        pid = cursor.fetchone()[0]
        if pid:
            conn.commit()
            return {"status": "success", "player_id": pid}
        raise HTTPException(status_code=401, detail="Auth failed")
    finally:
        cursor.close()
        conn.close()

@app.post("/api/players")
def create_player(player: PlayerSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO player (nickname, full_name, role) VALUES (%s, %s, %s) RETURNING player_id',
            (player.nickname, player.full_name, player.role)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "success", "player_id": new_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Nickname already exists or: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/api/players")
def get_all_players():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT player_id, nickname, full_name, role FROM player ORDER BY player_id')
    result = cursor.fetchall()
    res = []
    for row in result:
        res.append({'player_id': row[0], 'nickname': row[1], 'full_name': row[2], 'role': row[3]})
    cursor.close()
    conn.close()
    return res