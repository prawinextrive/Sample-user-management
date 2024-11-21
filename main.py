from fastapi import FastAPI, HTTPException
import mysql.connector
from pydantic import BaseModel
from typing import List

class User(BaseModel):
    id: int
    username: str
    phone: str
    email: str
    city: str
    district: str
    state: str

    class Config:
        orm_mode = True

app = FastAPI()

@app.get("/")
async def read_root():
    return "message: Go to /docs"

def get_connect():
    connection = mysql.connector.connect(
        host="localhost",
        port="3307",
        user="root",
        password="root",
        database="sample"
    )
    return connection

@app.post("/users/", response_model=User)
async def create_user(user: User):
    connection = get_connect()
    conn = connection.cursor(dictionary=True)
    query = "insert into usr (username, phone, email, city, district, state) VALUES (%s, %s, %s, %s, %s, %s)"
    conn.execute(query, (user.username, user.phone, user.email, user.city, user.district, user.state))
    connection.commit()
    
    user_id = conn.lastrowid
    conn.close()
    connection.close()
    
    return {**user.dict(), "id": user_id}


@app.get("/users/", response_model=List[User])
async def get_users():
    connection = get_connect()
    conn = connection.cursor(dictionary=True)
    conn.execute("select * from usr")
    rows = conn.fetchall()
    conn.close()
    connection.close()
    return rows

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    connection = get_connect()
    conn = connection.cursor(dictionary=True)
    conn.execute("select * from usr where id = %s", (user_id,))
    row = conn.fetchone()
    conn.close()
    connection.close()
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    return row

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: User):
    try:
        connection = get_connect()
        conn = connection.cursor(dictionary=True)
        conn.execute("select * from usr where id = %s", (user_id,))
        existing_user = conn.fetchone()

        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        query = "update usr set username = %s, phone = %s, email = %s, city = %s, district = %s, state = %s where id = %s"
        conn.execute(query, (user.username, user.phone, user.email, user.city, user.district, user.state, user_id))
        connection.commit()

        return {**user.dict(), "id": user_id}

    except Exception:
        raise HTTPException(status_code=500, detail="An error occurred while updating the user")

    finally:
        if conn:
            conn.close()
        if connection:
            connection.close()

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    connection = get_connect()
    conn = connection.cursor(dictionary=True)
    conn.execute("delete from usr where id = %s", (user_id,))
    connection.commit()
    conn.close()
    connection.close()
    return {"message": "User deleted"}
