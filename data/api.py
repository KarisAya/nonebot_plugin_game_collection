from typing import Tuple,Dict,List
from pathlib import Path
from fastapi import FastAPI
import pickle
from data import (
    DataBase,
    UserData,
    UserDict,
    GroupAccount,
    GroupData,
    GroupDict
    )

datafile = Path() / "russian_data.pickle"

# 加载数据

data:DataBase = None

if datafile.exists():
    with open(datafile, "rb") as f:
        data = pickle.load(f)
else:
    data = DataBase(file = datafile)

app = FastAPI()

@app.get("/data")
def get_user():
    return data