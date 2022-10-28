from typing import Tuple
from pydantic import BaseModel, Extra
from pathlib import Path


class Config(BaseModel, extra=Extra.ignore):
    russian_path: Path = Path()
    max_bet_gold: int = 1000
    race_bet_gold: int = 100
    gacha_gold: int = 500
    sign_gold: Tuple[int, int] = (100, 300)
    revolt_sign_gold:Tuple[int, int] = (800, 1200)
    security_gold:Tuple[int, int] = (50, 200)

    lucky_clover= "• ＬＵＣＫＹ  ＣＬＯＶＥＲ •"