from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery
import requests
import pandas as pd
from datetime import datetime
import sqlite3
import uvicorn
import os

API_KEYS = [
    "123456",
    "123456",
    "123456",
]

# Define the name of query param to retrieve an API key from
# api_key_query = APIKeyQuery(name="api-key", auto_error=False)

# Define the name of HTTP header to retrieve an API key from
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def get_api_key(
    # api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
):
    """Retrieve & validate an API key from the query parameters or HTTP header"""
    # If the API Key is present as a query param & is valid, return it
    # if api_key_query in API_KEYS:
    #     return api_key_query

    # If the API Key is present in the header of the request & is valid, return it
    if api_key_header in API_KEYS:
        return api_key_header

    # Otherwise, we can raise a 401
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

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
async def curriencies(api_key: str = Security(get_api_key)):
    df = pd.read_csv("currency_list.csv", index_col='currency_code', encoding='latin-1')
    currency_list = dict()
    for i in df.index:
        idx = df["currency"][i]
        currency_list[idx] = i
    return currency_list

@app.get("/convert")  
async def convert(amount, from_currency, to_currency, api_key: str = Security(get_api_key)): 
    url = 'https://www.xe.com/api/protected/midmarket-converter/'
    headers = {
        "authorization": "Basic bG9kZXN0YXI6RDlxT3N3RVg4WEJabjVidGhYRDN5Rk1OOG0yVXE3ZXQ=",
    }
    response = requests.get(url, headers=headers).json()
    rate = response["rates"][to_currency]/response["rates"][from_currency]
    converted_amount = rate*float(amount)
    timestamp = response["timestamp"]/1000
    time_of_conversion = datetime.fromtimestamp(timestamp)
    out = {
        "converted_amount": converted_amount,
        "rate": rate,
        "time_of_conversion": time_of_conversion,
    }
    
    values = (from_currency, to_currency, converted_amount, rate, time_of_conversion)
    cursor.execute('''INSERT INTO history VALUES (NULL, ?, ?, ?, ?, ?)''', values)
    conn.commit()
    return out

@app.get("/history")  
async def history(api_key: str = Security(get_api_key)): 
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