from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status
import requests
import pandas as pd
from datetime import datetime
import sqlite3
import uvicorn
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def auth_request(token: str = Depends(oauth2_scheme)) -> bool:
    authenticated = token == os.getenv("API_KEY", "123")
    return authenticated

app = FastAPI()

conn = sqlite3.connect("mydatabase.db")
cursor = conn.cursor()
sql_create_table = """ CREATE TABLE IF NOT EXISTS history (
                            id INTEGER PRIMARY KEY,
                            from_currency VARCHAR(3) NOT NULL,
                            to_currency VARCHAR(3) NOT NULL,
                            converted_amount FLOAT,
                            rate FLOAT,
                            time_of_conversion DATETIME
                        ); """
cursor.execute(sql_create_table)

@app.get("/currencies")
async def curriencies(authenticated: bool = Depends(auth_request)):
    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated")
    df = pd.read_csv("currency_list.csv", index_col='currency_code')
    currency_list = dict()
    for i in df.index:
        idx = df["currency"][i]
        currency_list[idx] = i
    return currency_list

@app.get("/convert")  
async def convert(amount, from_currency, to_currency, authenticated: bool = Depends(auth_request)): 
    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated") 
    url = 'https://www.xe.com/api/protected/midmarket-converter/'
    headers = {
        "authorization": "Basic bG9kZXN0YXI6RDlxT3N3RVg4WEJabjVidGhYRDN5Rk1OOG0yVXE3ZXQ=",
    }
    response = requests.get(url, headers=headers).json()
    out = dict()
    rate = response["rates"][to_currency]/response["rates"][from_currency]
    converted_amount = rate*float(amount)
    timestamp = response["timestamp"]/1000
    time_of_conversion = datetime.fromtimestamp(timestamp)
    out["converted_amount"] = converted_amount
    out["rate"] = rate
    out["time_of_conversion"] = time_of_conversion
    values = (from_currency, to_currency, converted_amount, rate, time_of_conversion)
    cursor.execute('''INSERT INTO history VALUES (NULL, ?, ?, ?, ?, ?)''', values)
    conn.commit()
    return out

@app.get("/history")  
async def history(authenticated: bool = Depends(auth_request)):
    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated") 
    sql = "SELECT * FROM history"
    cursor.execute(sql)
    history = cursor.fetchall()
    out = []
    for row in history:
        temp = {
            "converted_amount": row[3],
            "rate": row[4],
            "metadata": {
                "time_of_conversion": row[5],
                "from_currency": row[1],
                "to_currency": row[2]
            }
        }
        out.append(temp)
    return out

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8080)