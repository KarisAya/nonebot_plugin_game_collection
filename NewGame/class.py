from typing import Dict
from pydantic import BaseModel
from pathlib import Path
import random
try:
    import ujson as json
except ModuleNotFoundError:
    import json



class City(BaseModel):
    """
    城池属性
    """

class Player(BaseModel):
    """
    玩家属性
    """

class PlayerData(Dict[int, Player]):
    """
    玩家数据
    """