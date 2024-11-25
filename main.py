#this is before adding authorisation
from fastapi import FastAPI, HTTPException
import mysql.connector
from pydantic import BaseModel
from typing import List
import httpx
import asyncpg
import aiomysql

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

async def healthcheck():
    try:
        config = get_connect()
        async with aiomysql.connect(
            user=config['user'],
            password=config['password'],
            database=config['database'],
            host=config['host'],
            port=config['port']
        ) as connection:
            return True
    except:
        return False

@app.get("/health/")
async def health_check():
    status = await healthcheck()
    return {"message": "okay" if status else "not okay"}              

@app.post("/users/", response_model=User)
async def create_user(user: User):
    try:
        connection = get_connect()
        conn = connection.cursor(dictionary=True)
        query = "insert into usr (username, phone, email, city, district, state) VALUES (%s, %s, %s, %s, %s, %s)"
        conn.execute(query, (user.username, user.phone, user.email, user.city, user.district, user.state))
        connection.commit()
        user_id = conn.lastrowid
        return {**user.dict(), "id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500,details="")
    finally:
        conn.close()
        connection.close()
    
@app.get("/users/", response_model=List[User])
async def get_users():
    try:
        connection = get_connect()
        conn = connection.cursor(dictionary=True)
        conn.execute("select * from usr")
        rows = conn.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500,details="error occured while viewing all users")
    finally:
        conn.close()
        connection.close()
    return rows

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    try:
        connection = get_connect()
        conn = connection.cursor(dictionary=True)
        conn.execute("select * from usr where id = %s", (user_id,))
        row = conn.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="user not found")
        return row
    
    except Exception as e:
        raise HTTPException(status_code="500",details="an error occured while inserting values into the table")
    
    finally:
        conn.close()
        connection.close()

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
        raise HTTPException(status_code=500, detail="error occurred while updating user")

    finally:
        if conn:
            conn.close()
        if connection:
            connection.close()

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    try:
        connection = get_connect()
        conn = connection.cursor(dictionary=True)
        conn.execute("select * from usr where id = %s", (user_id,))
        existing_user= conn.fetchone()

        if not existing_user:
            raise HTTPException(status_code=404, detail="user not found")
        query= "delete from usr where id=%s"
        conn.execute(query,(user_id,))
        connection.commit()
        return {"message": "User deleted"}
    
    except Exception:
        raise HTTPException(status_code=500,detail="error occured while deleting")
    
    finally:
        conn.close()
        connection.close()
    
