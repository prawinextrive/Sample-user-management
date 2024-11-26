#this is after adding OAuth2 wiithout JWT
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Annotated
import mysql.connector

uidpwd = {
    1: {"uid": 1, "pwd": "praw1n", "role": "admin"},
    2: {"uid": 2, "pwd": "sanja1", "role": "user"}
}

def get_connect():
    connection = mysql.connector.connect(
        host="localhost",
        port="3307",
        user="root",
        password="root",
        database="sample"
    )
    return connection

app = FastAPI()
auth_scheme = OAuth2PasswordBearer(tokenUrl='token')

class User(BaseModel):
    id: int
    username: str
    phone: str
    email: str
    city: str
    district: str
    state: str

class Uid(BaseModel):
    uid: int
    pwd: str
    role: str

def get_user(db: dict, uid: int):
    return db.get(uid)

def decode_token(token: str):
    user_id = int(token)
    user = get_user(uidpwd, user_id)
    return user

async def get_current_user(token: Annotated[str, Depends(auth_scheme)]):
    user = decode_token(token)
    if not user:
        raise HTTPException(status_code=400, detail="Access not allowed for this user")
    return user

async def get_current_active_user(current_user: Annotated[Uid, Depends(get_current_user)]):
    if current_user["role"] == "user":
        raise HTTPException(status_code=400, detail="Access not allowed for this user")
    return current_user

def get_viewable_user(current_user: Annotated[Uid, Depends(get_current_active_user)]):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=400, detail="Access not allowed for others")
    return current_user

@app.post("/token/")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = uidpwd.get(int(form_data.username))
    if not user_dict:
        raise HTTPException(status_code=400, detail="Wrong uid or password")
    
    if user_dict["pwd"] != form_data.password:
        raise HTTPException(status_code=400, detail="Wrong uid or password")
    
    return {"access_token": str(user_dict['uid']), "token_type": "bearer"}

@app.get("/")
async def read_root():
    return "message: Go to /docs"

@app.post("/users/", response_model=User)
async def create_user(user: User, current_user: Annotated[Uid, Depends(get_viewable_user)]):
    try:
        connection = get_connect()
        conn = connection.cursor(dictionary=True)
        query = "insert into usr (username, phone, email, city, district, state) VALUES (%s, %s, %s, %s, %s, %s)"
        conn.execute(query, (user.username, user.phone, user.email, user.city, user.district, user.state))
        connection.commit()
        user_id = conn.lastrowid
        return {**user.dict(), "id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error occurred")
    finally:
        conn.close()
        connection.close()

@app.get("/users/", response_model=List[User])
async def get_users(current_user: Annotated[Uid, Depends(get_current_user)]):
    try:
        connection = get_connect()
        conn = connection.cursor(dictionary=True)   
        conn.execute("select * from usr")
        rows = conn.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error occurred while fetching users")
    finally:
        conn.close()
        connection.close()
    return rows

@app.get("/users/{user_id}", response_model=User)
async def get_one_user(user_id: int, current_user: Annotated[Uid, Depends(get_current_active_user)]):
    try:
        connection = get_connect()
        conn = connection.cursor(dictionary=True)
        conn.execute("select * from usr where id = %s", (user_id,))
        row = conn.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
        return row
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error occurred while fetching user")
    
    finally:
        conn.close()
        connection.close()

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: User, current_user: Annotated[Uid, Depends(get_current_active_user)]):
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
        raise HTTPException(status_code=500, detail="Error occurred while updating user")

    finally:
        if conn:
            conn.close()
        if connection:
            connection.close()

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: Annotated[Uid, Depends(get_current_active_user)]):
    try:
        connection = get_connect()
        conn = connection.cursor(dictionary=True)
        conn.execute("select * from usr where id = %s", (user_id,))
        existing_user = conn.fetchone()

        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        query = "delete from usr where id = %s"
        conn.execute(query, (user_id,))
        connection.commit()
        return {"message": "User deleted"}
    
    except Exception:
        raise HTTPException(status_code=500, detail="Error occurred while deleting user")
    
    finally:
        conn.close()
        connection.close()
