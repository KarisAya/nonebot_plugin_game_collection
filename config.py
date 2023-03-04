from typing import Tuple
from pydantic import BaseModel, Extra

class Config(BaseModel, extra=Extra.ignore):
    # 每日签到的范围
    sign_gold:Tuple[int, int] = (200, 500)
    # 每日补贴的范围
    security_gold:Tuple[int, int] = (100, 300)
    # 重置签到的范围
    revolt_gold:Tuple[int, int] = (1000, 2000)
    # 重置冷却时间
    revolt_cd:int = 28800
    # 重置的基尼系数
    revolt_gini:float = 0.68
    # 最大赌注
    max_bet_gold:int = 2000
    # 默认赌注
    bet_gold:int = 200
    # 单抽所需金币
    gacha_gold:int = 50
    # 一张测试字体测试字符串（
    lucky_clover= "• ＬＵＣＫＹ  ＣＬＯＶＥＲ •"
    # 默认显示字体
    game_fontname = "simsun"

    """+++++++++++++++++
    ——————————
       下面是赛马设置
    ——————————
    +++++++++++++++++"""

    # 跑道长度
    setting_track_length = 20
    # 随机位置事件，最小能到的跑道距离
    setting_random_min_length = 0
    # 随机位置事件，最大能到的跑道距离
    setting_random_max_length = 15
    # 每回合基础移动力最小值
    base_move_min = 1
    # 每回合基础移动力最大值
    base_move_max = 3
    # 最大支持玩家数
    max_player = 8
    # 最少玩家数
    min_player = 2
    # 事件概率 = event_rate / 1000
    event_rate = 450

import nonebot
from pathlib import Path

# 默认数据存数路径
path = Path() / "data" / "russian"
path.mkdir(exist_ok = True, parents = True)

# 备份路径
backup = path / "backup"
backup.mkdir(exist_ok = True, parents = True)

# 缓存路径
cache = path / "cache"
cache.mkdir(exist_ok = True, parents = True)

# 背景图片路径
BG_image = path / "BG_image"
BG_image.mkdir(exist_ok = True, parents = True)


global_config = nonebot.get_driver().config
config = Config.parse_obj(global_config.dict())

# bot昵称
bot_name = list(global_config.nickname)[0] if global_config.nickname else "bot"

sign_gold = config.sign_gold
security_gold = config.security_gold
revolt_gold = config.revolt_gold
revolt_cd = config.revolt_cd
revolt_gini = config.revolt_gini
max_bet_gold = config.max_bet_gold
bet_gold = config.bet_gold
gacha_gold = config.gacha_gold
lucky_clover = config.lucky_clover
fontname = config.game_fontname
setting_track_length = config.setting_track_length
setting_random_min_length = config.setting_random_min_length
setting_random_max_length = config.setting_random_max_length
base_move_min = config.base_move_min
base_move_max = config.base_move_max
max_player = config.max_player
min_player = config.min_player
event_rate = config.event_rate

"""
from .config import *
"""
__all__ = [
    bot_name,
    sign_gold,
    security_gold,
    revolt_gold,
    revolt_cd,
    revolt_gini,
    max_bet_gold,
    bet_gold,
    gacha_gold,
    lucky_clover,
    fontname,
    setting_track_length,
    setting_random_min_length,
    setting_random_max_length,
    base_move_min,
    base_move_max,
    max_player,
    min_player,
    event_rate,
    path,
    backup,
    cache,
    BG_image,
]