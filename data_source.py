from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    Message,
    MessageSegment
    )

from typing import Optional, Tuple, Union, List, Dict
from datetime import datetime
from nonebot.log import logger
from pathlib import Path
from collections import Counter



import nonebot
import asyncio
import random
import time
import os
import re
import unicodedata
import subprocess

from .config import Config
from .utils import get_message_at
from .utils import text_to_png, bbcode_to_png, img_Splicing, ohlc_Splicing, company_info_Splicing, survey_result

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from sys import platform

if platform == "linux" or platform == "linux2":
    python = "python3"
elif platform == "darwin":
    python = "python3"
elif platform == "win32":
    python = "python"

global_config = nonebot.get_driver().config
russian_config = Config.parse_obj(global_config.dict())

russian_path = russian_config.russian_path

cache = russian_path / "data" / "russian" / "cache"
linechart_cache = cache / "linechart"
candlestick_cache = cache / "candlestick"

# 签到金币随机范围
sign_gold = russian_config.sign_gold
revolt_sign_gold = russian_config.revolt_sign_gold
security_gold = russian_config.security_gold

# bot昵称
bot_name = list(global_config.nickname)[0] if global_config.nickname else "bot"

# 赌注
max_bet_gold = russian_config.max_bet_gold
race_bet_gold = russian_config.race_bet_gold
gacha_gold = russian_config.gacha_gold

# 自定义标记
lucky_clover = russian_config.lucky_clover

with open(os.path.dirname(__file__) + "/props_library.json", "r", encoding="utf8") as f:
    props_library = json.load(f)

props_index = {}

for prop_code in props_library.keys():
    props_index.update(
        {
            props_library[prop_code]["name"]:prop_code,
            prop_code:prop_code
            }
        )


def set_type(old:str, line:int) -> str:
    new = ""
    flag = 0
    for x in old:
        new += x
        if x == "\n":
            flag = 0
        elif flag > line:
            new += "\n"
            flag = 0
        else:
            if ord(x) < 0x200:
                flag += 1
            else:
                flag += 2
    return new

async def rank(player_data: dict, group_id: int, type_: str) -> str:
    """
    排行榜数据统计
    :param player_data: 玩家数据
    :param group_id: 群号
    :param type_: 排行榜类型
    """
    group_id = str(group_id)
    all_user = list(player_data[group_id].keys())
    if type_ == "gold_rank":
        rank_name = "【金币排行榜】\n——————————————\n"
        all_user_data = [player_data[group_id][x]["gold"] for x in all_user]
    elif type_ == "win_rank":
        rank_name = "【胜场排行榜】\n——————————————\n"
        all_user_data = [player_data[group_id][x]["win_count"] for x in all_user]
    elif type_ == "lose_rank":
        rank_name = "【败场排行榜】\n——————————————\n"
        all_user_data = [player_data[group_id][x]["lose_count"] for x in all_user]
    elif type_ == "make_gold":
        rank_name = "【赢取金币排行榜】\n——————————————\n"
        all_user_data = [player_data[group_id][x]["make_gold"] for x in all_user]
    else:
        rank_name = "【输掉金币排行榜】\n——————————————\n"
        all_user_data = [player_data[group_id][x]["lose_gold"] for x in all_user]
    rst = ""
    if all_user:
        for _ in range(len(all_user) if len(all_user) < 10 else 10):
            _max = max(all_user_data)
            _max_id = all_user[all_user_data.index(_max)]
            name = player_data[group_id][_max_id]["nickname"]
            rst += f"{_ + 1}.{name}：{_max}\n"
            all_user_data.remove(_max)
            all_user.remove(_max_id)
        rst = rst[:-1]
    return rank_name + rst

def random_bullet(num: int):
    """
    随机子弹排列
    :param num: 装填子弹数量
    """
    bullet_lst = [0, 0, 0, 0, 0, 0, 0]
    for i in random.sample([0, 1, 2, 3, 4, 5, 6], num):
        bullet_lst[i] = 1
    return bullet_lst

def random_dice():
    """
    随机骰子排列
    """
    dice_lst = [0, 0, 0, 0, 0]
    for i in range(5):
        dice_lst[i] = random.randint(1,6)
    return dice_lst

def random_poker():
    """
    生成随机牌库
    """
    poker_deck = []
    for i in range(1,5):
        for j in range(1,14):
            poker_deck.append([i,j])
    else:
        random.shuffle(poker_deck)
    return poker_deck

suit_name_dict = {
    0:"结束",
    1:"防御",
    2:"恢复",
    3:"技能",
    4:"攻击"
    }
point_dict = {
    0:"0",
    1:"A",
    2:"2",
    3:"3",
    4:"4",
    5:"5",
    6:"6",
    7:"7",
    8:"8",
    9:"9",
    10:"10",
    11:"11",
    12:"12",
    13:"13"
    }


class GameManager:
    def __init__(self):
        self._player_data = {}
        self._current_player = {}
        file = russian_path / "data" / "russian" / "russian_data.json"
        self.file = file
        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                self._player_data = json.load(f)

        self.global_data = {}
        file = russian_path / "data" / "russian" / "global_data.json"
        self.global_data_file = file
        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                self.global_data = json.load(f)

        self.alchemy_data = {}
        file = russian_path / "data" / "russian" / "alchemy_data.json"
        self.alchemy_data_file = file
        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                self.alchemy_data = json.load(f)

    def sign(self, event:MessageEvent) -> str:
        """
        签到
        :param event: event
        """
        user_data, group_id, user_id = self.try_get_user_data(event)

        if user_data == None:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        else:
            pass

        if user_data["is_sign"]:
            return "你已经签过到了哦"
        else:
            gold = random.randint(sign_gold[0], sign_gold[1])
            user_data["gold"] += gold
            user_data["make_gold"] += gold
            user_data["is_sign"] = True
            self.save()
            logger.info(f"USER {user_id} | GROUP {group_id} 获取 {gold} 金币")
            return random.choice(["祝你好运~", "可别花光了哦~"]) + f"\n你获得了 {gold} 金币"

    def revolt_sign(self, event:MessageEvent) -> str:
        """
        revolt签到
        :param event: event
        """
        user_data, group_id, user_id = self.try_get_user_data(event)

        if user_data == None:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        else:
            pass

        if user_data["revolution"]:
            return "你没有待领取的金币"
        else:
            gold = random.randint(revolt_sign_gold[0], revolt_sign_gold[1])
            user_data["gold"] += gold
            user_data["make_gold"] += gold
            user_data["revolution"] = True
            self.save()
            logger.info(f"USER {user_id} | GROUP {group_id} 获取 {gold} 金币")
            return f"这是你重置获得的金币，你获得了 {gold} 金币"

    def accept(self, event: GroupMessageEvent) -> Union[str, Message]:
        """
        接受决斗请求
        :param event: event
        """
        self._init_player_data(event)
        if not self._current_player.get(event.group_id):
            return None
        elif self._current_player[event.group_id][1] == 0:
            return None
        elif (
            self._current_player[event.group_id][1] == event.user_id or self._current_player[event.group_id][2] != 0 or 
            self._current_player[event.group_id]["at"] != 0 and self._current_player[event.group_id]["at"] != event.user_id
            ):
            return None
        else:
            if time.time() - self._current_player[event.group_id]["time"] > 30:
                self._current_player[event.group_id] = {}
                return "这场对决邀请已经过时了，请重新发起决斗..."
            else:
                if self._current_player[event.group_id]["game"] ==  "russian":
                    money = self._current_player[event.group_id]["money"]
                    tips = ["本场对决为【俄罗斯轮盘】\n","money"]
                elif self._current_player[event.group_id]["game"] == "dice":
                    money = self._current_player[event.group_id]["money_max"]
                    tips = ["本场对决为【掷色子】\n","money_max"]
                elif self._current_player[event.group_id]["game"] == "poker":
                    money = self._current_player[event.group_id]["money"]
                    tips = ["本场对决为【扑克对战】\n","money"]
                else:
                    return None

                gold = self.get_user_data(event)["gold"]

                if money < 0:
                    if gold < 200:
                        return Message(MessageSegment.at(event.user_id) + "你的金币不足以接受这场对决！")
                    else:
                        money = random.randint(200, min(-money,gold))
                        self._current_player[event.group_id][tips[1]] = money
                        tips[0] += f"赌注为 {money} 金币\n"
                else:
                    tips = ("","")

                if gold < money:
                    return Message(MessageSegment.at(event.user_id) + "你的金币不足以接受这场对决！")
                else:
                    player2_name = event.sender.card or event.sender.nickname
                    self._current_player[event.group_id][2] = event.user_id
                    self._current_player[event.group_id]["player2"] = player2_name
                    self._current_player[event.group_id]["time"] = time.time()
                    if self._current_player[event.group_id]["game"] == "russian":
                        return Message(
                            f"{player2_name}接受了对决！\n"
                            + tips[0] + 
                            f"请{MessageSegment.at(self._current_player[event.group_id][1])}开枪！"
                            )
                    elif self._current_player[event.group_id]["game"] == "dice":
                        self._current_player[event.group_id]["lose"] = event.user_id
                        self._current_player[event.group_id]["lose_name"] = player2_name
                        return Message(
                            f"{player2_name}接受了对决！\n"
                            + tips[0] + 
                            f"请{MessageSegment.at(self._current_player[event.group_id][1])}开数！"
                            )
                    elif self._current_player[event.group_id]["game"] == "poker":
                        self._current_player[event.group_id]["act"] = 1
                        hand = self._current_player[event.group_id]["status1"]["hand"]
                        hand_msg = ""
                        for i in range(3):
                            hand_msg += f'【{suit_name_dict[hand[i][0]]}{point_dict[hand[i][1]]}】'

                        message = (
                            f'玩家：{self._current_player[event.group_id]["player1"]}\n'
                            "状态：\n"
                            f'HP 20  SP 0  DEF 0\n'
                            "——————————————\n"
                            f'玩家：{self._current_player[event.group_id]["player2"]}\n'
                            "状态：\n"
                            f'HP 25  SP 2  DEF 0\n'
                            "——————————————\n"
                            f'当前回合：{self._current_player[event.group_id]["player1"]}\n'
                            "手牌：\n"
                            f"{hand_msg}\n"
                            )
                        output = text_to_png(message,30)
                        return MessageSegment.image(output)
                    else:
                        return Message("error")

    def refuse(self, bot: Bot, event: GroupMessageEvent) -> Union[str, Message]:
        """
        拒绝决斗请求
        :param event: event
        """
        self._init_player_data(event)
        if not self._current_player.get(event.group_id):
            return None
        elif self._current_player[event.group_id][1] == 0:
            return None
        elif self._current_player[event.group_id]["at"] == event.user_id:
            self._current_player[event.group_id] = {}
            return "拒绝成功，对决已结束。"
        else:
            return None

    def settlement(self, event: GroupMessageEvent) -> str:
        """
        结算检测
        :param event: event
        """
        self._init_player_data(event)
        if not self._current_player.get(event.group_id):
            return None
        elif self._current_player[event.group_id][1] == 0:
            return None
        elif (
            self._current_player[event.group_id][1] != 0 and
            self._current_player[event.group_id][2] != 0 and
            time.time() - self._current_player[event.group_id]["time"] > 30
            ):
            if self._current_player[event.group_id]["game"] in ("russian","poker"):
                win_name = (
                    self._current_player[event.group_id]["player1"]
                    if self._current_player[event.group_id][2] == self._current_player[event.group_id]["next"]
                    else self._current_player[event.group_id]["player2"]
                    )
            elif self._current_player[event.group_id]["game"] == "dice":
                win_name = self._current_player[event.group_id]["win_name"]
            else:
                pass

            return f"这场对决是 {win_name} 胜利了"
        else:
            return None

    async def fold(self, bot: Bot, event: GroupMessageEvent):
        """
        结束游戏
        :param event: event
        """
        self._init_player_data(event)
        if not self._current_player.get(event.group_id):
            return None
        elif self._current_player[event.group_id][1] == 0:
            return None
        elif (
            self._current_player[event.group_id]["game"] == "dice" and
            event.user_id == self._current_player[event.group_id]["lose"] and
            event.user_id == self._current_player[event.group_id]["next"]
            ):
            await asyncio.sleep(0.5)
            await self.end_game(bot, event)

    async def check_current_game(self, bot: Bot, event: GroupMessageEvent) -> Optional[str]:
        """
        检查当前是否有决斗存在
        """
        self._init_player_data(event)
        if time.time() - self._current_player[event.group_id]["time"] <= 30:
            if self._current_player[event.group_id][1]:
                if self._current_player[event.group_id][2]:
                    return (
                        f'{self._current_player[event.group_id]["player1"]} 和'
                        f'{self._current_player[event.group_id]["player2"]} 的对决还未结束！'
                        )
                else:
                    return (
                        f'现在是 {self._current_player[event.group_id]["player1"]} 发起的对决\n'
                        "请等待比赛结束后再开始下一轮..."
                        )
            else:
                return None
        else:
            if self._current_player[event.group_id][2]:
                await bot.send(event, message="决斗已过时，强行结算...")
                await self.end_game(bot, event)
                return None
            else:
                self._current_player[event.group_id][1] = 0
                self._current_player[event.group_id][2] = 0
                self._current_player[event.group_id]["at"] = 0
                return None

    def ready_game(
        self,
        event: GroupMessageEvent,
        msg: str,
        player1_name: str,
        at_: int,
        money: int,
        info
        ) -> Message:
        """
        发起游戏
        :param event: event
        :param msg: 提示消息
        :param player1_name: 玩家
        :param at_: at用户
        :param money: 赌注金额
        :param info: 游戏信息
        """
        self._current_player[event.group_id] = {
            1: event.user_id,
            "player1": player1_name,
            2: 0,
            "player2": "",
            "at": at_,
            "next": event.user_id,
            "money": money,
            "time": time.time(),
        }
        if info["game"] == "russian":
            bullet_num = info["bullet_num"]
            self._current_player[event.group_id].update(
                {
                    "game":"russian",
                    "bullet": random_bullet(bullet_num),
                    "bullet_num": bullet_num,
                    "null_bullet_num": 7 - bullet_num,
                    "index": 0
                    } 
                )
            return Message(
                ("咔 " * bullet_num)[:-1] + "，装填完毕\n"
                f"挑战金额：{money}\n"
                f"第一枪的概率为：{str(float(bullet_num) / 7.0 * 100)[:5]}%\n"
                f"{msg}"
                )
        elif info["game"] == "dice":
            self._current_player[event.group_id].update(
                {
                    "game":"dice",
                    "money_max": money,
                    "round":1,
                    "dice_array1":random_dice(),
                    "dice_array2":random_dice(),
                    "win":event.user_id,
                    "win_name":player1_name,
                    "lose":0,
                    "lose_name":"",
                    } 
                )
            self._current_player[event.group_id]["money"] = 0
            return Message(
                "哗啦哗啦~，骰子准备完毕\n"
                f"挑战金额：{money}\n"
                f"{msg}"
                )
        elif info["game"] == "poker":
            hand = []
            deck = random_poker()
            for i in range(4):
                deck.append([0,0]) # 在最后洗入结束卡
            for i in range(3):
                hand.append(deck[0])
                del deck[0]

            self._current_player[event.group_id].update(
                {
                    "game":"poker",
                    "deck":deck,
                    "act":0,
                    "status1":{
                        "hand":hand,
                        "HP":20,
                        "ATK":0,
                        "DEF":0,
                        "SP":0
                        },
                    "status2":{
                        "hand":[],
                        "HP":25,
                        "ATK":0,
                        "DEF":0,
                        "SP":2
                        }
                    } 
                )
            return Message(
                "唰唰~，随机牌库已生成\n"
                f"挑战金额：{money}\n"
                f"{msg}"
                )
        else:
            pass

    async def shot(self, bot: Bot, event: GroupMessageEvent, count: int):
        """
        开枪！！！
        :param bot: bot
        :param event: event
        :param count: 开枪次数
        """
        check_message = await self._shot_check(bot, event)
        if check_message:
            if check_message != "error":
                await bot.send(event, check_message)
            return None
        else:
            player1_name = self._current_player[event.group_id]["player1"]
            player2_name = self._current_player[event.group_id]["player2"]
            current_index = self._current_player[event.group_id]["index"]
            _tmp = self._current_player[event.group_id]["bullet"][current_index : current_index + count]
            if 1 in _tmp:
                flag = _tmp.index(1) + 1
                await bot.send(
                    event,
                    random.choice(
                        [
                            '嘭！，你直接去世了',
                            "眼前一黑，你直接穿越到了异世界...(死亡)",
                            "终究还是你先走一步..."
                            ]
                        )
                    + f"\n第 {current_index + flag} 发子弹送走了你...",
                    at_sender=True,
                    )
                win_name = player1_name if event.user_id == self._current_player[event.group_id][2] else player2_name
                await asyncio.sleep(0.5)
                await bot.send(event, f"这场对决是 {win_name} 胜利了")
                await self.end_game(bot, event)
            else:
                next_user = MessageSegment.at(
                    self._current_player[event.group_id][1]
                    if event.user_id == self._current_player[event.group_id][2]
                    else self._current_player[event.group_id][2]
                    )
                # 概率
                x = str(
                    float(self._current_player[event.group_id]["bullet_num"])
                    / float(
                        self._current_player[event.group_id]["null_bullet_num"]
                        - count
                        + self._current_player[event.group_id]["bullet_num"]
                        )* 100
                    )[:5]
                await bot.send(
                event,
                Message(
                    (f"连开{count}枪，" if count > 1 else "")
                    + random.choice(
                        [
                            "呼呼，没有爆裂的声响，你活了下来",
                            "虽然黑洞洞的枪口很恐怖，但好在没有子弹射出来，你活下来了",
                            f'{"咔 "*count}，看来运气不错，你活了下来'
                            ]
                        )
                    + f"\n\n下一枪中弹的概率：{x}%"
                    + f"\n轮到 {next_user}了"
                    )
                )
                self._current_player[event.group_id]["null_bullet_num"] -= count
                self._current_player[event.group_id]["next"] = (
                    self._current_player[event.group_id][1]
                    if event.user_id == self._current_player[event.group_id][2]
                    else self._current_player[event.group_id][2]
                    )
                self._current_player[event.group_id]["time"] = time.time()
                self._current_player[event.group_id]["index"] += count

    def dice_pt(self,dice_array:list) -> int:
        """
        计算骰子排列pt
        """
        pt = 0
        for i in range(1,7):
            if dice_array.count(i) <= 1:
                pt += i * dice_array.count(i)
            elif dice_array.count(i) == 2:
                pt += (100 + i) * (10 ** dice_array.count(i))
            else:
                pt += i * (10 ** (2 + dice_array.count(i)))
        else:
            return pt

    def dice_pt_analyses(self,pt:int) -> str:
        """
        分析骰子pt
        """
        array_type = ""
        if int(pt/10**7) > 0:
            yiman_pt = int(pt/10**7)
            pt -= yiman_pt*(10**7)
            array_type += f"役满 {yiman_pt} + "
        if int(pt/10**6) > 0:
            chuan_pt = int(pt/10**6)
            pt -= chuan_pt*(10**6)
            array_type += f"串 {chuan_pt} + "
        if int(pt/10**5) > 0:
            tiao_pt = int(pt/10**5)
            pt -= tiao_pt*(10**5)
            array_type += f"条 {tiao_pt} + "
        if int(pt/10**4) > 0:
            if int(pt/100) > 200:
                dui_pt = int(pt/100) - 200
                pt -= (dui_pt + 200)*100
                array_type += f"两对 {dui_pt} + "
            else:
                dui_pt = int(pt/100) - 100
                pt -= (dui_pt + 100)*100
                array_type += f"对 {dui_pt} + "
        if pt>0:
            array_type += f"散 {pt} + "
        return array_type[:-3]

    def dice_list(self,dice_array:list) -> str:
        """
        把骰子列表转成字符串
        """
        lst = ""
        lst_dict = {
            0:"〇",
            1:"１",
            2:"２",
            3:"３",
            4:"４",
            5:"５",
            6:"６",
            7:"７",
            8:"８",
            9:"９"
            }
        for x in dice_array:
            lst += lst_dict[x] + " "
        return lst[:-1]

    async def dice_open(self, bot: Bot, event: GroupMessageEvent):
        """
        开数！！！
        :param bot: bot
        :param event: event
        """
        check_message = await self._shot_check(bot, event)
        if check_message:
            if check_message != "error":
                await bot.send(event, check_message)
            return None
        else:
            round = self._current_player[event.group_id]["round"]
            money = int(self._current_player[event.group_id]["money_max"] * round/10)
            self._current_player[event.group_id]["round"] += 1
            self._current_player[event.group_id]["time"] = time.time()
            self._current_player[event.group_id]["money"] = money

            dice_array1 = (self._current_player[event.group_id]["dice_array1"][:int(round/2+0.5)] + [0, 0, 0, 0, 0])[:5]
            dice_array2 = (self._current_player[event.group_id]["dice_array2"][:int(round/2)] + [0, 0, 0, 0, 0])[:5]
            
            dice_array1.sort(reverse=True)
            dice_array2.sort(reverse=True)

            pt1 = self.dice_pt(dice_array1)
            pt2 = self.dice_pt(dice_array2)
            
            if pt1 > pt2:
                self._current_player[event.group_id]["win"] = self._current_player[event.group_id][1]
                self._current_player[event.group_id]["win_name"] = self._current_player[event.group_id]["player1"]
                self._current_player[event.group_id]["lose"] = self._current_player[event.group_id][2]
                self._current_player[event.group_id]["lose_name"] = self._current_player[event.group_id]["player2"]
            else:
                self._current_player[event.group_id]["win"] = self._current_player[event.group_id][2]
                self._current_player[event.group_id]["win_name"] = self._current_player[event.group_id]["player2"]
                self._current_player[event.group_id]["lose"] = self._current_player[event.group_id][1]
                self._current_player[event.group_id]["lose_name"] = self._current_player[event.group_id]["player1"]
            
            self._current_player[event.group_id]["next"] = (
                    self._current_player[event.group_id][1]
                    if event.user_id == self._current_player[event.group_id][2]
                    else self._current_player[event.group_id][2]
                    )

            next_id = self._current_player[event.group_id]["next"]
            next_name = (
                self._current_player[event.group_id]["player1"] 
                if next_id == self._current_player[event.group_id][1]
                else self._current_player[event.group_id]["player2"]
                )
            next_name = "结算" if self._current_player[event.group_id]["round"] > 10 else next_name
            message = (
                f'玩家：{self._current_player[event.group_id]["player1"]}\n'
                f"组合：{self.dice_list(dice_array1)}\n"
                f"点数：{self.dice_pt_analyses(pt1)}\n"
                "——————————\n"
                f'玩家：{self._current_player[event.group_id]["player2"]}\n'
                f"组合：{self.dice_list(dice_array2)}\n"
                f"点数：{self.dice_pt_analyses(pt2)}\n"
                "——————————\n"
                f"结算金额：{money}\n"
                f'领先：{self._current_player[event.group_id]["win_name"]}\n'
                f'下一回合：{next_name}'
                )
            output = text_to_png(message,30)
            await bot.send(event,message = MessageSegment.image(output))

            if self._current_player[event.group_id]["round"] > 10:
                await asyncio.sleep(0.5)
                await bot.send(event, f'{self._current_player[event.group_id]["win_name"]} 胜利！')
                await self.end_game(bot, event)

    def poker_hand_skill(self,st) -> str:
        '''
        手牌全部作为技能牌
        '''
        card_msg = "技能牌为"
        skill_msg = "\n"
        for card in st["hand"]:
            card_msg += f'【{suit_name_dict[card[0]]} {point_dict[card[1]]}】'
            if card[0] == 1:
                st["DEF"] += card[1]
                skill_msg += f'♤防御力强化了 {card[1]}\n'
            elif card[0] == 2:
                st["HP"] += card[1]
                skill_msg += f'♡生命值增加了 {card[1]}\n'
            elif card[0] == 3:
                st["SP"] += 2 * card[1]
                skill_msg += f'♧技能点增加了 {card[1]}\n'
            elif card[0] == 4:
                st["ATK"] += card[1]
                skill_msg += f'♢发动了攻击 {card[1]}\n'
            else:
                msg = "出现未知错误"
            st["SP"] = 0 if st["SP"] - card[1] <= 0 else st["SP"] - card[1]
        else:
            msg = card_msg + skill_msg[:-1]
            return msg

    def poker_action(self,action_card,st) -> str:
        '''
        行动牌生效
        :param action_card: 行动牌
        :param st: 行动牌生效对象
        '''
        if action_card[1] == 1:
            msg = f'发动ACE技能！\n'
            msg += self.poker_hand_skill(st)
        else:
            if action_card[0] == 1:
                st["ATK"] += action_card[1]
                msg = f"♤发动了攻击{action_card[1]}"
            elif action_card[0] == 2:
                st["HP"] += action_card[1]
                msg = f"♡生命值增加了{action_card[1]}"
            elif action_card[0] == 3:
                st["SP"] += action_card[1]
                msg = f"♧技能点增加了{action_card[1]}...\n"
                roll = random.randint(1,20)
                if  roll <= st["SP"]:
                    msg += f'二十面骰判定为{roll}点，当前技能点{st["SP"]}\n技能发动成功！\n'
                    msg += self.poker_hand_skill(st)
                else:
                    msg += f'二十面骰判定为{roll}点，当前技能点{st["SP"]}\n技能发动失败...'
            elif action_card[0] == 4:
                st["ATK"] = action_card[1]
                msg = f"♢发动了攻击{action_card[1]}"
            else:
                msg = "出现未知错误"
                pass
        return msg

    def poker_skill(self,skill_card,st) -> str:
        '''
        技能牌生效
        :param action_card: 技能牌
        :param st: 技能牌生效对象
        '''
        msg = f'技能牌为【{suit_name_dict[skill_card[0]]} {point_dict[skill_card[1]]}】\n'
        if skill_card[0] == 1:
            st["DEF"] += skill_card[1]
            msg += f"♤防御力强化了 {skill_card[1]}"
        elif skill_card[0] == 2:
            st["HP"] += skill_card[1]
            msg += f"♡生命值增加了 {skill_card[1]}"
        elif skill_card[0] == 3:
            st["SP"] += 2 * skill_card[1]
            msg += f"♧技能点增加了 {skill_card[1]}"
        elif skill_card[0] == 4:
            st["ATK"] += skill_card[1]
            msg += f"♢发动了反击 {skill_card[1]}"
        else:
            msg += "启动结算程序"

        st["SP"] = 0 if st["SP"] - skill_card[1] < 0 else st["SP"] - skill_card[1]

        return msg

    async def poker_play(self, bot: Bot, event: GroupMessageEvent, card:int):
        """
        扑克对战！
        :param bot: bot
        :param event: event
        :param card: 牌号
        """
        check_message = await self._shot_check(bot, event)
        if check_message:
            if check_message != "error":
                await bot.send(event, check_message)
            return None
        elif self._current_player.get(event.group_id,{"act":0})["act"] == 1:
            if card in ["1","2","3"]:
                self._current_player[event.group_id]["act"] = 0
                card = int(card) - 1
                self._current_player[event.group_id]["time"] = time.time()
                next_id = self._current_player[event.group_id]["next"]
                deck = self._current_player[event.group_id]["deck"]
                if next_id == self._current_player[event.group_id][1]:
                    st1 = self._current_player[event.group_id]["status1"]
                    st2 = self._current_player[event.group_id]["status2"]
                else:
                    st1 = self._current_player[event.group_id]["status2"]
                    st2 = self._current_player[event.group_id]["status1"]
            
                # 出牌判定

                action_card = st1["hand"][card]
                del st1["hand"][card]

                if action_card[1] == 1:
                    roll = random.randint(1,6)
                    st1["hand"].append([action_card[0],roll])
                    msg = f'发动ACE技能！六面骰子判定为 {roll}\n'
                    msg += self.poker_hand_skill(st1)
                else:
                    msg = self.poker_action(action_card,st1)

                try:
                    await bot.send(event,message = msg,at_sender=True)
                except:
                    output = text_to_png(msg,30)
                    await bot.send(event,message = MessageSegment.image(output))

                await asyncio.sleep(0.03*len(msg))

                next_name = (
                    self._current_player[event.group_id]["player1"] 
                    if next_id == self._current_player[event.group_id][2]
                    else self._current_player[event.group_id]["player2"]
                    )

                # 敌方技能判定
                if st2["SP"] > 0:
                    roll = random.randint(1,20)
                    if  roll <= st2["SP"]:
                        msg = f'{next_name} 二十面骰判定为{roll}点，当前技能点{st2["SP"]}\n技能发动成功！\n'
                        skill_card = deck[0]
                        del deck[0]
                        msg += self.poker_skill(skill_card,st2)
                    else:
                        msg = f'{next_name} 二十面骰判定为{roll}点，当前技能点{st2["SP"]}\n技能发动失败...'

                    try:
                        await bot.send(event,message = msg)
                    except:
                        output = text_to_png(msg,30)
                        await bot.send(event,message = MessageSegment.image(output))

                await asyncio.sleep(1.5)

                # 回合结算
                st1["HP"] += st1["DEF"] - st2["ATK"] if st1["DEF"] - st2["ATK"] < 0 else 0
                st2["HP"] += st2["DEF"] - st1["ATK"] if st2["DEF"] - st1["ATK"] < 0 else 0

                st1["ATK"] = 0
                st2["ATK"] = 0

                # 防御力强化保留一回合
                st2["DEF"] = 0 

                # 下回合准备
                self._current_player[event.group_id]["next"] = (
                    self._current_player[event.group_id][1]
                    if event.user_id == self._current_player[event.group_id][2]
                    else self._current_player[event.group_id][2]
                    )

                # 抽牌
                hand = []
                for i in range(3):
                    hand.append(deck[0])
                    del deck[0]
                else:
                    st2["hand"] = hand

                hand_msg = ""
                for i in range(3):
                    hand_msg += f'【{suit_name_dict[hand[i][0]]}{point_dict[hand[i][1]]}】'

                if (
                    self._current_player[event.group_id]["status1"]["HP"] < 1 
                    or self._current_player[event.group_id]["status2"]["HP"]  < 1
                    or st2["HP"]  > 40
                    or [0,0] in hand
                    ):
                    next_name = "游戏结束"

                message = (
                    f'玩家：{self._current_player[event.group_id]["player1"]}\n'
                    "状态：\n"
                    f'HP {self._current_player[event.group_id]["status1"]["HP"]}  '
                    f'SP {self._current_player[event.group_id]["status1"]["SP"]}  '
                    f'DEF {self._current_player[event.group_id]["status1"]["DEF"]}\n'
                    "——————————————\n"
                    f'玩家：{self._current_player[event.group_id]["player2"]}\n'
                    "状态：\n"
                    f'HP {self._current_player[event.group_id]["status2"]["HP"]}  '
                    f'SP {self._current_player[event.group_id]["status2"]["SP"]}  '
                    f'DEF {self._current_player[event.group_id]["status2"]["DEF"]}\n'
                    "——————————————\n"
                    f'当前回合：{next_name}\n'
                    "手牌：\n"
                    f"{hand_msg}\n"
                    )
                output = text_to_png(message,30)

                try:
                    await bot.send(event,message = MessageSegment.image(output))
                except Exception as error :
                    await bot.send_private_msg(user_id = list(bot.config.superusers)[0], message = MessageSegment.image(output))
                    await bot.send_private_msg(user_id = list(bot.config.superusers)[0], message = str(error))

                self._current_player[event.group_id]["act"] = 1
                if next_name == "游戏结束":
                    self._current_player[event.group_id]["act"] = 0
                    if st2["HP"]  > 40:
                        st2["HP"] += 100
                    await asyncio.sleep(0.5)
                    await self.end_game(bot, event)
            else:
                await asyncio.sleep(0.5)
                await bot.send(event, "请发送【出牌 1/2/3】打出你的手牌。")

    async def _shot_check(self, bot: Bot, event: GroupMessageEvent) -> Optional[str]:
        """
        开枪前检查游戏是否合法
        :param bot: bot
        :param event: event
        """
        try:
            if time.time() - self._current_player[event.group_id]["time"] > 60:
                if self._current_player[event.group_id][2] == 0:
                    self._current_player[event.group_id][1] = 0
                    logger.info("无人接受对战")
                    return "error"
                else:
                    await bot.send(event, "决斗已过时，强行结算...")
                    await self.end_game(bot, event)
                    return "error"
        except KeyError:
            return None

        if self._current_player[event.group_id][1] == 0:
            return None
        else:
            if self._current_player[event.group_id][2] == 0:
                if self._current_player[event.group_id][1] == event.user_id:
                    return "目前无人接受挑战哦"
                else:
                    return "请这位勇士先接受挑战"
            else:
                player1_name = self._current_player[event.group_id]["player1"]
                player2_name = self._current_player[event.group_id]["player2"]
                if self._current_player[event.group_id]["next"] != event.user_id:
                    if event.user_id != self._current_player[event.group_id][1] and event.user_id != self._current_player[event.group_id][2]:
                        return f"{player1_name} v.s. {player2_name}\n正在进行中..."
                    else:
                        nickname = (
                            player1_name
                            if self._current_player[event.group_id]["next"] == self._current_player[event.group_id][1]
                            else player2_name
                            )
                        return f"现在是{nickname}的回合"
                else:
                    return None

    def try_get_user_data(self, event: MessageEvent):
        """
        获取用户信息，兼容私聊
        """
        user_id = str(event.user_id)
        if isinstance(event,PrivateMessageEvent):
            group_id = self.get_global_data(user_id)["connect"]
            if (not group_id) or (group_id not in self._player_data.keys()):
                return None, None, user_id
            else:
                return self._player_data[group_id][user_id], group_id, user_id
        else:
            self._init_player_data(event)
            group_id = str(event.group_id)
            return self._player_data[group_id][user_id], group_id, user_id

    def get_global_data(self, user_id:str) -> dict:
        """
        获取用户全局数据
        """
        self.global_data.setdefault(
            user_id,
            {
                "connect": None,
                "props": {}
                }
            )
        return self.global_data[user_id]

    def global_data_save(self):
        with open(self.global_data_file, "w", encoding="utf8") as f:
            json.dump(self.global_data, f, ensure_ascii=False, indent=4)

    def get_alchemy_data(self, user_id:str) -> dict:
        """
        获取用户炼金数据
        """
        self.alchemy_data.setdefault(user_id,{})
        return self.alchemy_data[user_id]

    def alchemy_data_save(self):
        with open(self.cards_data_file, "w", encoding="utf8") as f:
            json.dump(self.alchemy_data, f, ensure_ascii=False, indent=4)

    def get_user_data(self, event: GroupMessageEvent) -> Dict[str, Union[str, int]]:
        """
        获取用户数据
        :param event:
        :return:
        """
        self._init_player_data(event)
        return self._player_data[str(event.group_id)][str(event.user_id)]

    def get_current_bullet_index(self, event: GroupMessageEvent) -> int:
        """
        获取当前剩余子弹数量
        :param event: event
        """
        return self._current_player[event.group_id]["index"]

    async def rank(self, msg: str, group_id: int) -> str:
        """
        获取排行榜
        :param msg: 排行榜类型
        :param group_id: 群号
        """
        if "金币排行" in msg:
            return await rank(self._player_data, group_id, "gold_rank")
        if "胜场排行" in msg or "胜利排行" in msg:
            return await rank(self._player_data, group_id, "win_rank")
        if "败场排行" in msg or "失败排行" in msg:
            return await rank(self._player_data, group_id, "lose_rank")
        if "欧洲人排行" in msg:
            return await rank(self._player_data, group_id, "make_gold")
        if "慈善家排行" in msg:
            return await rank(self._player_data, group_id, "lose_gold")

    def check_game_is_start(self, group_id: int) -> bool:
        """
        检测群内游戏是否已经开始
        :param group_id: 群号
        """
        return self._current_player[group_id][1] != 0

    def reset_sign(self):
        """
        刷新签到
        """
        for group in self._player_data.keys():
            for user_id in self._player_data[group].keys():
                self._player_data[group][user_id]["is_sign"] = False
        else:
            self.save()

    def reset_security(self):
        """
        刷新补贴
        """
        for group in self._player_data.keys():
            for user_id in self._player_data[group].keys():
                self._player_data[group][user_id]["security"] = 0
        else:
            self.save()

    def save(self):
        """
        保存数据
        """
        with open(self.file, "w", encoding="utf8") as f:
            json.dump(self._player_data, f, ensure_ascii=False, indent=4)

    def _init_player_data(self, event: GroupMessageEvent):
        """
        初始化用户数据
        :param event: event
        """
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        nickname = event.sender.card or event.sender.nickname
        if group_id not in self._player_data.keys():
            self._player_data[group_id] = {}
        if user_id not in self._player_data[group_id].keys():
            self._player_data[group_id][user_id] = {
                "user_id": user_id,
                "group_id": group_id,
                "nickname": nickname,
                "gold": 0,
                "make_gold": 0,
                "lose_gold": 0,
                "win_count": 0,
                "lose_count": 0,
                "is_sign": None,
                "revolution": None,
                "security":0,
                "Achieve_revolution":0,
                "Achieve_victory":0,
                "Achieve_lose":0,
                "stock": {
                    "value": 0
                    },
                "props": {}
                }
        self._player_data[group_id][user_id]["nickname"] = nickname
        self.save()

    async def end_game(self, bot: Bot, event: GroupMessageEvent):
        """
        游戏结束结算
        :param bot: Bot
        :param event: event
        :return:
        """
        player1_name = self._current_player[event.group_id]["player1"]
        player2_name = self._current_player[event.group_id]["player2"]

        if self._current_player[event.group_id]["game"] == "russian":
            if self._current_player[event.group_id]["next"]== self._current_player[event.group_id][1]:
                win_user_id = self._current_player[event.group_id][2]
                lose_user_id = self._current_player[event.group_id][1]
                win_name = player2_name
                lose_name = player1_name
            else:
                win_user_id = self._current_player[event.group_id][1]
                lose_user_id = self._current_player[event.group_id][2]
                win_name = player1_name
                lose_name = player2_name
        elif self._current_player[event.group_id]["game"] == "dice":
            win_user_id = self._current_player[event.group_id]["win"]
            lose_user_id = self._current_player[event.group_id]["lose"]
            win_name = self._current_player[event.group_id]["win_name"]
            lose_name = self._current_player[event.group_id]["lose_name"]
        elif self._current_player[event.group_id]["game"] == "poker":
            if self._current_player[event.group_id]["status1"]["HP"] > self._current_player[event.group_id]["status2"]["HP"]:
                win_user_id = self._current_player[event.group_id][1]
                lose_user_id = self._current_player[event.group_id][2]
                win_name = player1_name
                lose_name = player2_name
            else:
                win_user_id = self._current_player[event.group_id][2]
                lose_user_id = self._current_player[event.group_id][1]
                win_name = player2_name
                lose_name = player1_name
        else:
            pass

        flag = self._player_data[str(event.group_id)][str(win_user_id)]["props"].get("42001",0)
        gold = self._current_player[event.group_id]["money"]
        if flag > 0:
            rand = -1
            fee = 0
        else:
            rand = random.randint(0, 5)
            fee = int(gold * float(rand) / 100)

        end_info = self._end_data_handle(win_user_id, lose_user_id, event.group_id, gold, fee)

        extra = end_info["extra"]
        security = end_info["security"]
        off = end_info["off"]

        win_user = self._player_data[str(event.group_id)][str(win_user_id)]
        lose_user = self._player_data[str(event.group_id)][str(lose_user_id)]
        
        game_str = ""
        if self._current_player[event.group_id]["game"] == "russian":
            logger.info(f"俄罗斯轮盘：胜者：{win_name} - 败者：{lose_name} - 金币：{gold}")
            for x in self._current_player[event.group_id]["bullet"]:
                game_str += "__ " if x == 0 else "| "
            game_str = f"子弹排列：\n{game_str[:-1]}"
        elif self._current_player[event.group_id]["game"] == "dice":
            logger.info(f"摇骰子：胜者：{win_name} - 败者：{lose_name} - 金币：{gold}")
            game_str = (
                "排列：\n"+
                self._current_player[event.group_id]["player1"]+"\n"+
                self.dice_list(self._current_player[event.group_id]["dice_array1"])+"\n"
                "——————————\n"+
                self._current_player[event.group_id]["player2"]+"\n"+
                self.dice_list(self._current_player[event.group_id]["dice_array2"])
                )
        else:
            pass

        self._current_player[event.group_id] = {}
        message=(
            f"结算：\n"
            "——————————————\n"+
            self.Achieve_list(win_user)+
            (f"◆『{props_library['52002']['name']}』\n"if extra != 0 else "")+
            f"◆胜者：{win_name}\n"
            f'◆结算：{win_user["gold"]}（+{gold + extra - fee}）\n'
            f'◆胜场∶败场：{win_user["win_count"]}∶{win_user["lose_count"]}\n'
            f'◆胜率：{str(win_user["win_count"]/(win_user["win_count"] + win_user["lose_count"])*100)[:5]}%\n'
            "——————————————\n" +
            self.Achieve_list(lose_user)+
            (f"◇『金币补贴』\n"if security != 0 else "")+
            (f"◇『{props_library['52001']['name']}』\n"if off != 0 else "")+
            f"◇败者：{lose_name}\n"
            f'◇结算：{lose_user["gold"] - security}（-{gold - off}）\n'+
            (f"◇已领取补贴：{security}\n"if security else "")+
            f'◇胜场∶败场：{lose_user["win_count"]}∶{lose_user["lose_count"]}\n'
            f'◇胜率：{str(lose_user["win_count"]/(lose_user["win_count"] + lose_user["lose_count"])*100)[:5]}%\n'
            "——————————————\n"+
            f"手续费：{fee} " + (f"『{props_library['42001']['name']}』"if rand == -1 else f"({float(rand)}%)")
            )
        
        output = text_to_png(message)
        await bot.send(event,MessageSegment.image(output))

        if game_str:
            output = text_to_png(game_str,20)
            await bot.send(event,MessageSegment.image(output))

    def _end_data_handle(
        self,
        win_user_id: int,
        lose_user_id,
        group_id: int,
        gold: int,
        fee: int,
        ):
        """
        结算数据处理保存
        :param win_user_id: 胜利玩家id
        :param lose_user_id: 失败玩家id
        :param group_id: 群聊
        :param gold: 赌注金币
        :param fee: 手续费
        """
        end_info={}
        win_user_id = str(win_user_id)
        lose_user_id = str(lose_user_id)
        group_id = str(group_id)

        self._player_data[group_id][win_user_id]["gold"] += gold - fee
        self._player_data[group_id][win_user_id]["make_gold"] += gold - fee
        self._player_data[group_id][win_user_id]["win_count"] += 1
        self._player_data[group_id][win_user_id]["Achieve_victory"] += 1
        self._player_data[group_id][win_user_id]["Achieve_lose"] = 0

        flag = self._player_data[group_id][win_user_id]["props"].get("52002",0)
        if flag > 0:
            extra = int(gold *0.2)
            self._player_data[group_id][win_user_id]["gold"] += extra
        else:
            extra = 0
            

        self._player_data[group_id][lose_user_id]["gold"] -= gold
        self._player_data[group_id][lose_user_id]["lose_gold"] += gold
        self._player_data[group_id][lose_user_id]["lose_count"] += 1
        self._player_data[group_id][lose_user_id]["Achieve_victory"] = 0
        self._player_data[group_id][lose_user_id]["Achieve_lose"] += 1

        if self._player_data[group_id][lose_user_id]["gold"] <= 0 and self._player_data[group_id][lose_user_id]["security"] < 3:
            self._player_data[group_id][lose_user_id]["security"] += 1
            security = random.randint(security_gold[0], security_gold[1])
            self._player_data[group_id][lose_user_id]["gold"] += security
        else:
            security = 0

        
        flag = self._player_data[group_id][lose_user_id]["props"].get("52001",0)
        if flag > 0:
            off = int(gold *0.2)
            self._player_data[group_id][lose_user_id]["gold"] += off
        else:
            off = 0

        self.save()

        end_info["extra"] = extra
        end_info["security"] = security
        end_info["off"] = off

        return end_info

    def total_gold(self, group_id: str,number:int) ->int:
        """
        金币总数
        """
        player_data = self._player_data
        all_user = list(player_data.get(group_id,{}).keys())
        sum = 0
        if all_user:
            all_user_gold = [player_data[group_id][i]["gold"] + player_data[group_id][i]["stock"]["value"] for i in all_user]
            for _ in range(len(all_user) if len(all_user) < number else number):
                _max_gold = max(all_user_gold)
                sum = sum + int(_max_gold)
                all_user_gold.remove(_max_gold)
            return sum
        else:
            return -1
        
    def revlot(self, group_id: int) -> str:
        """
        发起革命
        :param group_id: 群号
        """
        player_data = self._player_data
        group_id = str(group_id)
        all_user = list(player_data[group_id].keys())
        all_user_data = [player_data[group_id][i]["gold"] + player_data[group_id][i]["stock"]["value"] for i in all_user]
        first = max(all_user_data)
        first_id = all_user[all_user_data.index(first)]
        first_name = player_data[group_id][first_id]["nickname"]
        if all_user:
            sum = self.total_gold(group_id,10)
            if first > (5 * max_bet_gold) and first >= sum - first:
                for _ in range(len(all_user) if len(all_user) < 10 else 10):
                    _max = max(all_user_data)
                    _max_id = all_user[all_user_data.index(_max)]
                    player_data[group_id][_max_id]["gold"] = 0
                    for company_name in player_data[group_id][_max_id]["stock"].keys():
                        if company_name == "value":
                            continue
                        else:
                            stock = player_data[group_id][_max_id]["stock"][company_name]
                            player_data[group_id][_max_id]["stock"][company_name] -= stock
                            market_manager._market_data[company_name]["stock"] += stock
                    all_user_data.remove(_max)
                    all_user.remove(_max_id)
                for user_id in player_data[group_id].keys():
                    player_data[group_id][user_id]["revolution"] = False
                player_data[group_id][first_id]["Achieve_revolution"] += 1
                self.save()
                market_manager.market_data_save()
                return f"重置成功\n恭喜{first_name}进入路灯挂件榜~☆！"
            else:
                return f"{first_name}的金币需要达到{round((5 * max_bet_gold) if sum - first < (5 * max_bet_gold) else sum - first, 2)}才可以发起重置。"
        else:
            return None

    async  def _init_at_player_data(self,bot: Bot, event: GroupMessageEvent,at_player_id:int):
        """
        初始化at用户数据
        :param event: event
        """
        user_id = str(at_player_id)
        group_id = str(event.group_id)
        at_player_data = await bot.get_group_member_info(group_id=event.group_id, user_id=at_player_id)
        nickname = at_player_data["card"] or at_player_data["nickname"]
        if group_id not in self._player_data.keys():
            self._player_data[group_id] = {}
            self.save()
        if user_id not in self._player_data[group_id].keys():
            self._player_data[group_id][user_id] = {
                "user_id": user_id,
                "group_id": group_id,
                "nickname": nickname,
                "gold": 0,
                "make_gold": 0,
                "lose_gold": 0,
                "win_count": 0,
                "lose_count": 0,
                "slot":0,
                "is_sign": None,
                "revolution": None,
                "security":0,
                "Achieve_revolution":0,
                "Achieve_victory":0,
                "Achieve_lose":0,
                "stock": {
                    "value": 0
                    },
                "props": {}
                }
            self.save()

    def transfer_accounts(
        self,
        event: GroupMessageEvent,
        at_player_id: int,
        unsettled: int,
        ) -> str:
        """
        转账数据处理保存
        :param event: event
        :param at_player_id: 转入账户玩家id
        :param unsettled: 转账金额
        """
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        at_player_id = str(at_player_id)
        flag = self._player_data[group_id][user_id]["props"].get("42001",0)
        if flag > 0:
            fee = 0
        else:
            fee = int(unsettled * 0.02)

        self._player_data[group_id][user_id]["gold"] -= unsettled
        self._player_data[group_id][at_player_id]["gold"] += unsettled - fee
        self.save()
        return (
            f"{self._player_data[group_id][user_id]['nickname']} 向 {self._player_data[group_id][at_player_id]['nickname']} 转账{unsettled}金币\n"+
            (f"『{props_library['42001']['name']}』免手续费" if flag > 0 else f"扣除2%手续费：{fee}，实际到账金额{unsettled - fee}")
            )

    def give_props(
        self,
        event: GroupMessageEvent,
        at_player_id: int,
        props: str,
        count: int,
        ) -> str:
        """
        送道具
        :param event: event
        :param at_player_id: 接收道具玩家id
        :param props: 道具名
        :param count: 道具数量
        """
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        at_player_id = str(at_player_id)

        user_data = self._player_data[group_id][user_id]
        at_user_data = self._player_data[group_id][at_player_id]

        global_props = self.get_global_data(user_id)["props"]
        at_global_props = self.get_global_data(at_player_id)["props"]

        prop_code = props_index.get(props)
        if not prop_code:
            return f"没有【{props}】这种道具。"

        if prop_code == "02101":    # 路灯挂件的特例
            n = user_data["Achieve_revolution"] + user_data["props"].setdefault(prop_code,0)
        elif prop_code[1] == "3":
            n = global_props.get(prop_code,0)
        else:
            n = user_data["props"].get(prop_code,0)

        if n < count:
            return "数量不足"
        else:
            if prop_code[1] == "3":
                global_props[prop_code] -= count
                at_global_props.setdefault(prop_code,0)
                at_global_props[prop_code] += count
                self.global_data_save()
            else:
                user_data["props"][prop_code] -= count
                at_user_data["props"].setdefault(prop_code,0)
                at_user_data["props"][prop_code] += count
                self.save()
            return f"{count} 个 {props} 已送出"

    class Use_props:
        def __init__(self):
            pass
        def main(
            self,
            event:MessageEvent,
            props:str,
            count:int,
            ) -> str:
            """
            使用道具
            :param event: event
            :param props: 道具名
            :param count: 道具数量
            """
            prop_code = props_index.get(props)
            if not prop_code:
                return f"没有【{props}】这种道具。"
            elif prop_code == "03101":
                return self.use_03101(event,count)
            elif prop_code == "33101":
                return self.use_33101(event,count)
            elif prop_code == "42101":
                return self.use_42101(event)
            elif prop_code == "52101":
                return self.use_52101(event)
            elif prop_code == "52102":
                return self.use_52102(event,count)
            else:
                return f"【{props}】不是可用道具。"

        def use_03101(
            self,
            event: MessageEvent,
            count: int,
            ) -> str:
            """
            使用道具：被冻结的资产
            """
            user_data, group_id, user_id = russian_manager.try_get_user_data(event)
            if user_data == None:
                return "私聊未关联账户，请发送【关联账户】关联群内账户。"
            else:
                pass

            global_props = russian_manager.get_global_data(user_id)["props"]
            n = global_props.get("03101",0)
            if n < count:
                return "数量不足"
            else:
                global_props["03101"] -= count
                gold = count * max_bet_gold
                user_data["gold"] += gold
                russian_manager.save()
                russian_manager.global_data_save()
                return f"你获得了{gold}金币。"

        def use_33101(
            self,
            event: MessageEvent,
            count: int,
            ) -> str:
            """
            使用道具：初级元素
            """
            user_data, group_id, user_id = russian_manager.try_get_user_data(event)
            if user_data == None:
                return "私聊未关联账户，请发送【关联账户】关联群内账户。"
            else:
                pass

            global_props = global_data["props"]
            n = global_props.get("33101",0)
            if n < count:
                return "数量不足"
            else:
                global_props["03101"] -= count
                alchemy_data = russian_manager.get_alchemy_data(user_id)
                for i in range(4 * count):
                    element_code = f"0{random.randint(1,4)}01"
                    alchemy_data.setdefault(element_code,0)
                    alchemy_data[element_code] += 1

                russian_manager.alchemy_data_save()
                russian_manager.global_data_save()
                return "ok"

        def use_42101(
            self,
            event: MessageEvent,
            ) -> str:
            """
            使用道具：调查凭证
            """
            user_data, group_id, user_id = russian_manager.try_get_user_data(event)
            if user_data == None:
                return "私聊未关联账户，请发送【关联账户】关联群内账户。"
            else:
                pass

            n = user_data["props"].get("42101",0)
            if n < 1:
                return "数量不足"
            else:
                at = get_message_at(event.json())
                if at:
                    at = str(at[0])
                    if at in russian_manager._player_data[group_id].keys():
                        at_data = russian_manager._player_data[group_id][at]
                        user_data["props"]["42101"] -= 1
                        N = random.randint(0,50)
                        gold = int(at_data["gold"] * N / 1000)
                        user_data["gold"] += gold
                        at_data["gold"] -= gold

                        info = f"你获得了{gold}枚金币\n"

                        for stock, count in at_data["stock"].items():
                            if stock == "value":
                                pass
                            else:
                                t = int(count * N / 100)
                                if t > 0:
                                    user_data["stock"].setdefault(stock,0)
                                    user_data["stock"][stock] += t
                                    at_data["stock"][stock] -= t
                                    if at in market_manager.Stock_Exchange[stock]:
                                        del market_manager.Stock_Exchange[stock][at]
                                    info += f"{stock}：{t}\n"
                                else:
                                    pass
                        else:
                            info += f"（{N/10}%）" 
                        return info
                    else:
                        return "对方没有账户。"
                else:
                    return "没有指定用户。"

        def use_52101(
            self,
            event: MessageEvent,
            ) -> str:
            """
            使用道具：神秘天平
            """
            user_data, group_id, user_id = russian_manager.try_get_user_data(event)
            if user_data == None:
                return "私聊未关联账户，请发送【关联账户】关联群内账户。"
            else:
                pass

            n = user_data["props"].get("52101",0)
            if n < 1:
                return "数量不足"
            else:
                user_data["props"]["52101"] -= 1
                group_data = russian_manager._player_data[group_id]
                data = sorted(group_data.items(),key=lambda x:x[1]["gold"],reverse = True)
                target_id = random.choice(data[:20])[0]

                if target_id == user_id:
                    return f"道具使用失败，你损失了一个『{props_library['52101']['name']}』"
                target_data = group_data[target_id]
                user_data["gold"]
                sum = target_data["gold"] + user_data["gold"]
                gold = int(sum/2)
                fee = int(gold/20)

                flag = target_data["props"].get("42001",0)
                if flag > 0:
                    target_data["gold"] = gold
                    msg1 = f"\n对方获得了{gold}金币『{props_library['42001']['name']}』。"
                else:
                    target_data["gold"] = gold - fee
                    msg1 = f"\n对方获得了{gold - fee}金币(扣除5%手续费：{fee})。"

                flag = user_data["props"].get("42001",0)
                if flag > 0:
                    user_data["gold"] = gold
                    msg2 = f"\n你获得了{gold}金币『{props_library['42001']['name']}』。"
                else:
                    user_data["gold"] = gold - fee
                    msg2 = f"\n你获得了{gold - fee}金币(扣除5%手续费：{fee})。"

                russian_manager.save()

                return f"你与{target_data['nickname']}平分了金币。" + msg1 + msg2

        def use_52102(
            self,
            event: MessageEvent,
            count: int,
            ) -> str:
            """
            使用道具：幸运硬币
            """
            user_data, group_id, user_id = russian_manager.try_get_user_data(event)
            if user_data == None:
                return "私聊未关联账户，请发送【关联账户】关联群内账户。"
            else:
                pass

            n = user_data["props"].get("52102",0)
            if n < 1:
                return "数量不足"
            else:
                user_data["props"]["52102"] -= 1
                gold = user_data["gold"]
                if count == 2:
                    n = user_data["props"].get("62101",0)
                    if n > 1:
                        user_data["props"]["62101"] -= 1
                    else:
                        return "钻石数量不足"
                else:
                    gold = gold if gold < (50 * max_bet_gold) else (50 * max_bet_gold)

                if random.randint(0,1) == 1:
                    user_data["gold"] += gold
                    st = "获得"
                else:
                    user_data["gold"] -= gold
                    st = "失去"
                russian_manager.save()
                return f"你{st}了{gold}金币"

    use_props = Use_props()

    def Achieve_list(self,user_data):
        """
        成就列表
        :param user_data: russian_manager.get_user_data(event)
        """
        rank = ""
        count = user_data["Achieve_revolution"] + user_data["props"].get("02101",0)
        if count > 0:
            if count <= 4:
                rank += f"{(4-count)*'  '}{count*'☆'}  路灯挂件  {count*'☆'}{(4-count)*'  '}\n"
            else: 
                rank += f"☆☆☆☆☆路灯挂件☆☆☆☆☆\n"
            rank += "——————————————\n"
        count = user_data["props"].get("32001",0)   # 四叶草标记
        if count > 0:
            rank += f"{lucky_clover}\n"
            rank += "——————————————\n"
        count = user_data["gold"]
        if count > max_bet_gold:
            count = int(count/max_bet_gold)
            count = str(count) if count < 1000 else "MAX"
            level =f"Lv.{count}"
            rank += f"◆◇ 金库 {level}{(6-len(level))*' '} ◆◇\n"
        count = user_data["Achieve_victory"]
        if count >1:
            count = str(count) if count < 1000 else "MAX"
            level =f"Lv.{count}"
            rank += f"◆◇ 连胜 {level}{(6-len(level))*' '} ◆◇\n"
        count = user_data["Achieve_lose"]
        if count >1:
            count = str(count) if count < 1000 else "MAX"
            level =f"Lv.{count}"
            rank += f"◆◇ 连败 {level}{(6-len(level))*' '} ◆◇\n"

        return rank

    def my_props(self, event: MessageEvent):
        user_data, group_id, user_id = self.try_get_user_data(event)

        if user_data == None:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        else:
            pass

        group_props = user_data["props"]
        
        global_props = self.get_global_data(user_id)["props"]

        special_props = {"02101":(user_data["Achieve_revolution"])} # 路灯挂件的特例

        props = Counter(group_props) + Counter(global_props) + Counter(special_props)

        data = sorted(props.items(),key=lambda x:int(x[0]))

        props_info = ""
        for seg in data:
            prop_code = seg[0]
            n = seg[1]
            quant = "天" if prop_code[2] == 0 else "个"
            prop = props_library.get(prop_code,{"name": prop_code, "color": "black","rare": 1,"intro": "未知","des": "未知"})
            props_info += (
                f"[size=60][align=left][color={prop['color']}]【{prop['name']}】{prop['rare']*'☆'}[/align][align=right]{n}{quant}\n[/color][/align][/size]"
                f"[size=60][align=left][color=gray]——————————————\n[/color][/align][/size]"
                f"[size=40][align=left][color=gray]{set_type(prop['intro'],38)}[/color][/align][/size]"
                f"[size=40][align=right][color=gray]{set_type(prop['des'],38)}[/color][/align][/size]"
                f"[size=60][align=left][color=gray]——————————————\n[/color][/align][/size]"
                )
        if props_info:
            output = bbcode_to_png(props_info)
            return MessageSegment.image(output)
        else:
            return "您的仓库空空如也。"

    def my_info(self, event: MessageEvent) -> str:
        """
        资料卡
        :param event: event
        """
        user_data, group_id, user_id = self.try_get_user_data(event)

        if user_data == None:
            return None
        else:
            pass

        nickname = user_data["nickname"]
        gold = user_data["gold"]
        make_gold = user_data["make_gold"]
        lose_gold = user_data["lose_gold"]
        is_sign = user_data["is_sign"]
        security = user_data["security"]
        win_count = user_data["win_count"]
        lose_count = user_data["lose_count"]
        stock = user_data["stock"]
        stock["value"] = market_manager.value_update(group_id, user_id)
        my_stock = []
        stock_info = ""
        for x in stock.keys():
            if x == "value" or  stock[x] == 0 :
                continue
            else:
                my_stock.append([x,round(market_manager._market_data[x]["float_gold"] * stock[x] / 20000,2)])
        else:
            my_stock.sort(key = lambda x:x[1],reverse = True)
            for x in my_stock:
                stock_info += f'【{x[0]}】\n持有：{stock[x[0]]} 株\n价值：{x[1]} 金币\n'

        output_nickname = ""
        flag = 0
        end = 0
        for x in nickname:
            if flag == 0:
                output_nickname += "\n【"
            output_nickname += x

            if ord(x) < 0x200:
                flag += 1
            else:
                flag += 2

            if flag > 22:
                output_nickname += f'{(24-flag)*" "}】'
                flag = 0
                end = 1
        else:
            output_nickname = output_nickname[1:]
            if end == 1 and flag != 0:
                output_nickname += (24-flag)*" " + "】"
            elif end != 1:
                output_nickname += "】"
            else:
                pass

        info = (
            f'{output_nickname}\n'
            "——————————————\n"
            + ("" if self.Achieve_list(user_data) == "" else self.Achieve_list(user_data) + "——————————————\n") +
            f'金    币：{gold}\n'
            f'持有价值：{round(stock["value"],2)}\n'
            f'赚取金币：{make_gold}\n'
            f'输掉金币：{lose_gold}\n'
            "——————————————\n"
            f'胜败场次：{win_count}∶{lose_count}\n'
            f'胜    率：{str((win_count/(win_count + lose_count) if win_count + lose_count > 0 else 0 ) * 100 )[:5]}%\n'
            "——————————————\n"
            f'今日签到：{"已签到"if is_sign else "未签到"}\n'
            f'今日补贴：还剩 {3 - security} 次\n'
            "——————————————\n" +
            stock_info
            )
        return info

    def slot(self, event: PrivateMessageEvent, gold:int):
        """
        幸运花色
        :param event: event
        :param gold: 金币
        """
        user_data = self.try_get_user_data(event)[0]
        if user_data == None:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        else:
            pass

        if gold < 50:
            return '抽取幸运花色每次至少50金币。'
        elif gold > max_bet_gold:
            return f'抽取幸运花色每次最多{max_bet_gold}金币。'
        elif gold > user_data["gold"]:
            return f'你没有足够的金币，你的金币：{user_data["gold"]}。'

        suit_dict = {
            1:"♤",
            2:"♡",
            3:"♧",
            4:"♢"
            }
        x = random.randint(1,4)
        y = random.randint(1,4)
        z = random.randint(1,4)

        suit = f"| {suit_dict[x]} | {suit_dict[y]} | {suit_dict[z]} |"
        lst=[x,y,z]
        lst0=list(set(lst))
        if len(lst0)==1:
            user_data["gold"] += gold *7
            user_data["make_gold"] += gold *7
            msg =(
                f"你抽到的花色为：\n"+
                suit+
                f"\n恭喜你获得了{gold * 7}金币，祝你好运~"
                )
        elif len(lst0) != len(lst):
            msg =(
                f"你抽到的花色为：\n"+
                suit+
                f"\n祝你好运~"
                )
        else:
            user_data["gold"] -= gold
            user_data["lose_gold"] += gold
            msg =(
                f"你抽到的花色为：\n"+
                suit+
                f"\n你失去了{gold}金币 ，祝你好运~"
                )

        self.save()
        return msg

    def gacha(self, event:MessageEvent, N:int):
        """
        抽卡
        """
        user_data, group_id, user_id = self.try_get_user_data(event)

        if user_data == None:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        else:
            pass

        props_data = self.get_global_data(user_id)["props"]

        if user_data["gold"] < N * gacha_gold:
            return f'{N}连抽卡需要{N * gacha_gold}金币，你的金币：{user_data["gold"]}。'
        else:
            user_data["gold"] -= N * gacha_gold
            res = {}
            for i in range(N):
                code = random.randint(1,100)
                if 0 < code <= 30:
                    rare = 3
                elif 30 < code <= 40:
                    rare = 4
                elif 40 < code <= 50:
                    rare = 5
                elif code == 90:
                    rare = 0
                elif code == 100:
                    rare = 6
                else:
                    rare = 1
                prop_code = self.random_props(rare)
                res.setdefault(prop_code,0)
                res[prop_code] += 1
            else:
                data = sorted(res.items(),key=lambda x:int(x[0]),reverse=True)
                nickname = event.sender.card or event.sender.nickname
                msg = f"[size=60][align=left]{nickname}\n{N}连抽卡结果：\n[color=gray]——————————————\n[/color][/align][/size]"
                for seg in data:
                    prop_code = seg[0]
                    n = seg[1]
                    if prop_code[1] == "2":
                        user_data["props"].setdefault(prop_code,0)
                        user_data["props"][prop_code] += n
                        if prop_code[2] == "0":
                            quant =  "天"
                            user_data["props"][prop_code] = 7 if user_data["props"][prop_code] > 7 else user_data["props"][prop_code]
                        else:
                            quant =  "个"
                            if prop_code[0] not in ["0","6"]:
                                user_data["props"][prop_code] = 10 if user_data["props"][prop_code] > 10 else user_data["props"][prop_code]
                    elif prop_code[1] == "3":
                        props_data.setdefault(prop_code,0)
                        props_data[prop_code] += n
                        quant =  "个"
                    else:
                        quant =  "次"

                    prop = props_library.get(prop_code,{"name": prop_code, "color": "black","rare": 1,"intro": "未知","des": "未知"})
                    msg += (
                        f"[size=60][align=left][color={prop['color']}]【{prop['name']}】{prop['rare']*'☆'}[/align][align=right]{n}{quant}[/color][/align][/size]\n"
                        f"[size=60][align=left][color=gray]——————————————[/color][/align][/size]\n"
                        )
                self.save()
                self.global_data_save()
                output = bbcode_to_png(msg)
                return MessageSegment.image(output)

    def random_props(self, rare:int) -> str:
        """
        根据稀有度随机获取道具。
        param: rare: 稀有度
        return: 道具代码
        道具代码规则：
        第1位：稀有度
        第2位：道具性质：
            1：空气
            2：群内道具
            3：全局道具
        第3位：道具时效：
            0：时效道具
            1：永久道具
        4,5位：本稀有度下的道具编号
        """
        if rare == 3:
            props = random.choice([31001,32001,32002,33101])
        elif rare == 4:
            props = random.choice([41001,42001,42101])
        elif rare == 5:
            props = random.choice([51001,51002,52001,52002,52101,52102])
        elif rare == 6:
            props = random.choice([61001,62101])
        else:
            props = 11001
        return str(props)



russian_manager = GameManager()



class MarketManager:

    def __init__(self):
        self._market_data = {}
        self.market_index = {}  # 市场指数
        file = russian_path / "data" / "russian" / "market_data.json"
        self.file = file

        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                self._market_data = json.load(f)

        self.Stock_Exchange = {}
        file = russian_path / "data" / "russian" / "Stock_Exchange.json"
        self.Stock_Exchange_file = file

        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                self.Stock_Exchange = json.load(f)

        self.market_history = {}
        file = russian_path / "data" / "russian" / "market_history.json"
        self.market_history_file = file

        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                self.market_history = json.load(f)

        self.ohlc_temp = [[],1]

    def _init_market_data(self, event: GroupMessageEvent,company_name: str):
        """
        初始化市场数据
        :param event: event
        :param company_name:公司名
        """
        group_id = str(event.group_id)
        if group_id in self._market_data.keys():
            return f"群号：{group_id}已注册"
        if company_name in self._market_data.keys():
            return f"名称：{company_name}已注册"

        self._market_data[group_id] = {
            "group_id":event.group_id,
            "company_name":company_name,
            "stock":20000,
            "gold":0.0,
            "time":time.time()
            }
        self._market_data[company_name] = {
            "group_id":event.group_id,
            "company_name":company_name,
            "stock":20000,
            "gold":0.0,
            "group_gold":0.0,
            "float_gold":0.0,
            "intro":""
            }
        return None

    def market_data_save(self):
        """
        保存市场数据
        """
        with open(self.file, "w", encoding="utf8") as f:
            json.dump(self._market_data, f, ensure_ascii=False, indent=4)

    def Stock_Exchange_save(self):
        """
        保存交易数据
        """
        with open(self.Stock_Exchange_file, "w", encoding="utf8") as f:
            json.dump(self.Stock_Exchange, f, ensure_ascii=False, indent=4)

    def market_history_save(self):
        """
        保存市场历史数据
        """
        with open(self.market_history_file, "w", encoding="utf8") as f:
            json.dump(self.market_history, f, ensure_ascii=False, indent=4)

    def Market_sell(self, event:MessageEvent, company_name: str, quote:float, stock:int) -> str:
        """
        市场卖出
        :param event: event
        :param company_name:公司名
        :param quote:报价
        :param stock:数量
        """
        user_data, group_id, user_id = russian_manager.try_get_user_data(event)
        if user_data == None:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        else:
            pass

        my_stock = user_data["stock"].get(company_name,0)

        if not company_name in self.Stock_Exchange.keys():
            return f"【{company_name}】未注册"
        elif my_stock < stock:
            return (
                "你的账户中没有足够的股票。\n"
                f'{company_name}剩余：{russian_manager._player_data[group_id][user_id]["stock"][company_name]} 株'
                )
        elif self.cheak_market(company_name,user_id):
            self.Stock_Exchange[company_name][user_id]["quote"] = quote
            self.Stock_Exchange[company_name][user_id]["stock"] = stock
            self.Stock_Exchange[company_name][user_id]["group_id"] = group_id
            self.Stock_Exchange_save()
            return (
                f"【{company_name}】\n"
                "——————————————\n"
                f'报价：{self.Stock_Exchange[company_name][user_id]["quote"]} 金币\n'
                f'数量：{self.Stock_Exchange[company_name][user_id]["stock"]} 株\n'
                "——————————————\n"
                "信息已修改。"
                )
        else:
            self.Stock_Exchange[company_name].setdefault(user_id,{})
            self.Stock_Exchange[company_name][user_id].update(
                {
                    "quote":quote,
                    "stock":stock,
                    "group_id":group_id
                    }
                )
            self.Stock_Exchange_save()
            return (
                f"【{company_name}】\n"
                "——————————————\n"
                f'报价：{quote} 金币\n'
                f'数量：{stock} 株\n'
                "——————————————\n"
                "发布成功！"
                )

    def Market_buy(self, event:MessageEvent, company_name: str, stock:int):
        """
        市场买入
        :param company_name:公司名
        :param stock:数量
        """
        user_data, group_id, user_id = russian_manager.try_get_user_data(event)
        if user_data == None:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        else:
            pass

        my_gold = user_data["gold"]

        if self.Stock_Exchange.get(company_name) == None:
            return f"【{company_name}】未注册"
        else:
            lst = sorted(self.Stock_Exchange[company_name].items(),key = lambda x:x[1]["quote"])
            i = 0
            count = 0
            while i < len(lst):
                if lst[i][0] == user_id or lst[i][1]["stock"] == 0:
                    lst.remove(lst[i])
                else:
                    count += lst[i][1]["stock"]
                    i += 1
            if lst == []:
                return f"市场上没有【{company_name}】"
            else:
                stock = stock if count > stock else count
                TL = {}
                gold = 0.0
                for seller in lst:
                    # 报价
                    _quote = seller[1]["quote"]
                    # 数量
                    _stock = seller[1]["stock"]
                    _count = _stock if _stock < stock else stock
                    stock -= _count
                    # 群组
                    _group_id = seller[1]["group_id"]
                    # 交易日志
                    TL.update({seller[0]:[_quote,_count,_group_id]})
                    # 统计金额
                    gold += _quote * _count
                if gold > my_gold:
                    return (
                        "金币不足：\n"
                        f'你的金币：{my_gold}'
                        f"需要金币：{int(gold)}"
                        )
                else:
                    count = 0
                    for seller in lst:
                        seller_group = TL[seller[0]][2]
                        seller_id = seller[0]
                        N = TL[seller_id][1]
                        unsettled = int (TL[seller_id][0] * N)
                        
                        russian_manager._player_data[group_id][user_id]["gold"] -= unsettled
                        russian_manager._player_data[seller_group][seller_id]["gold"] += unsettled
                        
                        russian_manager._player_data[group_id][user_id]["stock"]["value"] = self.value_update(group_id,user_id)
                        russian_manager._player_data[seller_group][seller_id]["stock"]["value"] = self.value_update(seller_group,seller_id)
                        
                        russian_manager._player_data[group_id][user_id]["stock"].setdefault(company_name,0)
                        russian_manager._player_data[group_id][user_id]["stock"][company_name] += N
                   
                        russian_manager._player_data[seller_group][seller_id]["stock"].setdefault(company_name,0)
                        russian_manager._player_data[seller_group][seller_id]["stock"][company_name] -= N
                        
                        self.Stock_Exchange[company_name][seller_id]["stock"] -= N
                        count += N
                    else:
                        russian_manager.save()
                        self.Stock_Exchange_save()
                    return (
                        "交易成功！\n"
                        "——————————————\n"
                        f"【{company_name}】\n" 
                        f"数量：{count}\n"
                        f"价格：{round(gold/count,2)}\n"
                        f"总计：{gold}"
                        )

    def company_buy(self,event:MessageEvent, company_name:str ,stock:int) -> str:
        """
        购买公司发行股票
        :param event: event
        :param company_name:公司名
        :param stock: 购买的股票数量
        """
        user_data, group_id, user_id = russian_manager.try_get_user_data(event)
        if user_data == None:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        else:
            pass

        my_gold = user_data["gold"]

        company = self._market_data.get(company_name)

        if company == None:
            return f"公司名：{company_name} 未注册"
        elif company["gold"] <= (5 * max_bet_gold) or company["float_gold"] <= 0:
            return f"【{company_name}】 被冻结，无法买入。"
        else:
            stock = stock if stock < company["stock"] else company["stock"]
            if stock > 0:
                value = 0.0
                _gold = company["gold"] if  company["gold"] > company["float_gold"] else company["float_gold"]
                for _ in range(stock):
                    tmp = _gold/ 20000
                    tmp = 0.1 if tmp < 0.1 else tmp
                    _gold += tmp * 0.65
                    value += tmp
                else:
                    if value > my_gold:
                        return (
                            "你的金币不足...\n"
                            f"你的金币：{my_gold}\n"
                            "——————————————\n"
                            f"【{company_name}】\n"
                            f"数量：{stock}\n"
                            f"单价：{round(value/stock,2)}\n"
                            f"总计：{int(value)}"
                            )
                    else:
                        self._market_data[company_name]["stock"] -= stock
                        russian_manager._player_data[group_id][user_id]["stock"].setdefault(company_name,0)
                        russian_manager._player_data[group_id][user_id]["stock"][company_name] += stock
                        self._market_data[company_name]["gold"] += value
                        russian_manager._player_data[group_id][user_id]["gold"] -= int(value)
                        self._market_data[company_name]["group_gold"] = float(russian_manager.total_gold(str(self._market_data[company_name]["group_id"]),1000))
                        self._market_data[company_name]["float_gold"] += value * 0.65
                        russian_manager._player_data[group_id][user_id]["stock"]["value"] = self.value_update(group_id,user_id)
                        self.market_data_save()
                        russian_manager.save()
                        return (
                            "交易成功！\n"
                            "——————————————\n"
                            f"【{company_name}】\n" 
                            f"数量：{stock}\n"
                            f"单价：{round(value/stock,2)}\n"
                            f"总计：{int(value)}"
                            )
            else:
                return "已售空，请等待清算或在交易市场购买。"

    def company_clear(self,event:MessageEvent, company_name:str ,stock:int) -> str:
        """
        股权债务清算
        :param event: event
        :param company_name:公司名
        :param stock: 清算的数量
        """ 
        user_data, group_id, user_id = russian_manager.try_get_user_data(event)
        if user_data == None:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        else:
            pass

        my_stock = user_data["stock"].get(company_name)

        company = self._market_data.get(company_name)

        if company == None:
            return f"【{company_name}】未注册"
        elif my_stock == None:
            return f"未持有【{company_name}】股份"
        elif stock > my_stock:
            return f"你没有足够的股份...\n你持有【{company_name}】：{my_stock}株"
        elif self.cheak_market(company_name,user_id):
            return f"你在市场上【{company_name}】的交易未完成，无法结算。"
        else:
            value = 0.0
            _gold = company["float_gold"]
            for _ in range(stock):
                tmp = float(_gold/ 20000)
                _gold -= tmp * 0.65
                value += tmp
            else:
                self._market_data[company_name]["stock"] += stock
                russian_manager._player_data[group_id][user_id]["stock"][company_name] -= stock
                self._market_data[company_name]["gold"] -= value
                russian_manager._player_data[group_id][user_id]["gold"] += int(value * 0.998)
                self._market_data[company_name]["group_gold"] = float(russian_manager.total_gold(str(self._market_data[company_name]["group_id"]),1000))
                self._market_data[company_name]["float_gold"] = _gold
                russian_manager._player_data[group_id][user_id]["stock"]["value"] = self.value_update(group_id,user_id)
                self.market_data_save()
                russian_manager.save()
                return (
                    "交易成功！\n"
                    "——————————————\n"
                    f"【{company_name}】\n" 
                    f"数量：{stock}\n"
                    f"单价：{round(value/stock,2)}\n"
                    f"总计：{int(value * 0.998)}"
                    )

    def cheak_market(self,company_name:str,user_id:str) -> bool:
        """
        检查市场上有没有进行中的交易
        :param company_name:公司名
        :param user_id: 用户名
        """
        if company_name in self.Stock_Exchange.keys():
            if self.Stock_Exchange[company_name].get(user_id,{"stock":0})["stock"] > 0:
                return True
        return False

    global ohlc

    ohlc = subprocess.Popen(f"{python} {os.path.dirname(__file__)}/process/ohlc.py {russian_path}", shell=True)

    async def Market_info(self, event:MessageEvent, company_name:str):
        """
        市场信息
        :param company_name:公司名，为空则是总览。
        """
        if company_name in self.Stock_Exchange.keys():
            lst = sorted(self.Stock_Exchange[company_name].items(),key = lambda x:x[1]["quote"])
            i = 0
            msg = ""
            while i < (len(lst) if len(lst) < 10 else 10):
                if lst[i][1]["stock"] > 0:
                    nickname = russian_manager._player_data[lst[i][1]["group_id"]][lst[i][0]]["nickname"]
                    msg += (
                        f'{nickname}\n'
                        f'单价：{lst[i][1]["quote"]} 数量：{lst[i][1]["stock"]}\n'
                        )
                    i += 1
                else:
                    del lst[i]

            if msg:
                msg = (f'【{company_name}】\n'"——————————————\n") + msg
                msg = msg[:-1]
                output = text_to_png(msg)
                return MessageSegment.image(output)
            else:
                return f"【{company_name}】市场为空"
        else:
            lst = []
            for x in self._market_data.keys():
                if self._market_data[x].get("time") == None:
                    lst.append([x,self._market_data[x]["group_gold"]])
            else:
                lst.sort(key = lambda x:x[1],reverse = True)

            if lst:
                msg =[]
                global ohlc
                returncode = ohlc.poll()
                if company_name == "pro":
                    flag = 0
                    if self.ohlc_temp[1] > 6 and returncode == 0:
                        ohlc = subprocess.Popen(f"{python} {os.path.dirname(__file__)}/process/ohlc.py {russian_path}", shell=True)
                        self.ohlc_temp[1] = 0
                    while ohlc.poll() == None:
                        await asyncio.sleep(1)
                else:
                    flag = 1

                if flag == 0:
                    output = []
                    i = 0
                    for x in lst:
                        price = (
                            self._market_data[x[0]]["gold"]
                            if self._market_data[x[0]]["gold"] > self._market_data[x[0]]["float_gold"]
                            else self._market_data[x[0]]["float_gold"]
                            )
                        info = (
                            f'【{x[0]}】\n'
                            "——————————————\n"
                            f'固定资产：{round(self._market_data[x[0]]["gold"], 2)} 金币\n'
                            f'市场流动：{int(x[1])} 金币\n'
                            f'发行价格：{round(price/20000,2)} 金币\n'
                            f'结算价格：{round(self._market_data[x[0]]["float_gold"] / 20000, 2)} 金币\n'
                            f'剩余数量：{self._market_data[x[0]]["stock"]} 株\n'
                            )
                        if i < 3:
                            output.append(company_info_Splicing(info,[Path(linechart_cache / x[0]),Path(candlestick_cache / x[0])]))
                            i += 1
                        else:
                            msg.append(
                                {
                                    "type": "node",
                                    "data": {
                                        "name": f"{bot_name}",
                                        "uin": str(event.self_id),
                                        "content": MessageSegment.image(img_Splicing(output))
                                        }
                                    }
                                )
                            output = []
                            i = 0
                    else:
                        if i:
                            msg.append(
                                {
                                    "type": "node",
                                    "data": {
                                        "name": f"{bot_name}",
                                        "uin": str(event.self_id),
                                        "content": MessageSegment.image(img_Splicing(output))
                                        }
                                    }
                                )
                else:
                    output = ""
                    i = 0
                    for x in lst:
                        price = (
                            self._market_data[x[0]]["gold"]
                            if self._market_data[x[0]]["gold"] > self._market_data[x[0]]["float_gold"]
                            else self._market_data[x[0]]["float_gold"]
                            )
                        if i < 5:
                            output += (
                                f'【{x[0]}】\n'
                                "——————————————\n"
                                f'固定资产：{round(self._market_data[x[0]]["gold"], 2)} 金币\n'
                                f'市场流动：{int(x[1])} 金币\n'
                                f'发行价格：{round(price/20000,2)} 金币\n'
                                f'结算价格：{round(self._market_data[x[0]]["float_gold"] / 20000, 2)} 金币\n'
                                f'剩余数量：{self._market_data[x[0]]["stock"]} 株\n'
                                "——————————————\n"
                                )
                            i += 1
                        else:
                            msg.append(
                                {
                                    "type": "node",
                                    "data": {
                                        "name": f"{bot_name}",
                                        "uin": str(event.self_id),
                                        "content": MessageSegment.image(text_to_png(output[:-1]))
                                        }
                                    }
                                )
                            output = ""
                            i = 0
                    else:
                        if i:
                            msg.append(
                                {
                                    "type": "node",
                                    "data": {
                                        "name": f"{bot_name}",
                                        "uin": str(event.self_id),
                                        "content": MessageSegment.image(text_to_png(output[:-1]))
                                        }
                                    }
                                )
                return msg
            else:
                return "市场不存在..."

    def public(self, event: GroupMessageEvent,company_name: str):
        """
        公司上市
        :param event: event
        :param company_name:公司名
        """
        if company_name == "value":
            return f"公司名称不能是{company_name}"
        if "\n" in company_name:
            return f"公司名称不能含有回车"
        flag = 0
        for x in company_name:
            if ord(x) < 0x200:
                flag += 1
            else:
                flag += 2
        if flag > 24:
            return f"公司名称不能超过24字符"
        gold = float(russian_manager.total_gold(str(event.group_id),1000))
        if gold < 20000:
            return f"金币总额达到20k才可注册。\n当前群内总金币为{gold}"
        else:
            msg = self._init_market_data(event,company_name)
            if msg:
                return msg
            else:
                self._market_data[company_name]["gold"] = gold * 0.5
                self._market_data[company_name]["group_gold"] = gold
                self._market_data[company_name]["float_gold"] = gold * 0.5
                self.market_data_save()
                self.Stock_Exchange.setdefault(company_name,{})
                self.Stock_Exchange_save()
                return f'{company_name}发行成功，发行价格为每股{round((self._market_data[company_name]["gold"]/20000),2)}金币'

    async def delist(self, bot:Bot, event:MessageEvent):
        """
        清理市场
        """
        tmp = await bot.get_group_list()
        if not tmp:
            return "群组获取失败"
        else:
            market = self._market_data
            player = russian_manager._player_data
            
            # 存在的群
            live_group_list = []
            for group in tmp:
                live_group_list.append(str(group["group_id"]))

            # 已建立公司的群
            company_list = []
            for group_id in market.keys():
                if "time" in market[group_id]:
                    company_list.append(group_id)

            # 注册过的群
            group_list = set(player.keys())

            # 已注册但不存在的群
            delist_group = set(group_list) - set(live_group_list)

            msg = ""

            # 公司破产结算
            delist_list = []
            for group_id in company_list:
                if group_id in delist_group or russian_manager.total_gold(group_id,1000) < (5 * max_bet_gold):
                    company_name = market[group_id]["company_name"]
                    delist_list.append((group_id,company_name))

                    info = f'开始清算【{company_name}】'
                    msg += info + "\n"
                    logger.info(info)
                    for user_id in player[group_id].keys():
                        for stock,count in player[group_id][user_id]["stock"].items():
                            if stock != "value":
                                market[stock]["stock"] += count
                                player[group_id][user_id]["stock"][stock] = 0
                                if user_id in self.Stock_Exchange[stock]:
                                    del self.Stock_Exchange[stock][user_id]

                                info = f"账户：{group_id[0:4]}-{user_id[0:4]} 名称：{stock} 数量：{count}"
                                msg += info + "\n"
                                logger.info(info)
                    else:
                        info = "清算完成"
                        msg += info + "\n"
                        logger.info(info)

            # 删除公司
            for company,company_name in delist_list:
                info = f'删除公司【{company_name}】'
                msg += info + "\n"
                logger.info(info)
                for group_id in group_list:
                    for user_id in set(player[group_id].keys()):
                        if company_name in player[group_id][user_id]["stock"].keys():
                            del player[group_id][user_id]["stock"][company_name]
                del market[company]
                del market[company_name]
                del self.Stock_Exchange[company_name]
                try:
                    del self.market_history[company_name]
                except:
                    pass

            # 清理无效账户
            for group_id in group_list:
                if group_id in delist_group:
                    for user_id in player[group_id].keys():
                        info = f'账户：{group_id[0:4]}-{user_id[0:4]} 金币：{player[group_id][user_id]["gold"]}'
                        msg += info + "\n"
                        logger.info(info)
                        for stock, count in player[group_id][user_id]["stock"].items():
                            if stock == "value":
                                pass
                            else:
                                market[stock]["stock"] += count
                                player[group_id][user_id]["stock"][stock] = 0
                                if user_id in self.Stock_Exchange[stock]:
                                    del self.Stock_Exchange[stock][user_id]

                                info = f'账户：{group_id[0:4]}-{user_id[0:4]} 名称：{stock} 数量：{count}'
                                msg += info + "\n"
                                logger.info(info)
                    del player[group_id]
                else:
                    tmp = await bot.get_group_member_list(group_id = int(group_id), no_cache = True)
                    if tmp:
                        live_group_member_list = []
                        repurchase_member_list = []
                        for group_member in tmp:
                            user_id = str(group_member["user_id"])
                            live_group_member_list.append(user_id)
                            if group_member["last_sent_time"] < time.time() - 604800:
                                repurchase_member_list.append(user_id)
                        # 注册过的账户
                        group_member_list = set(player[group_id].keys())
                        # 股票回收账户
                        repurchase_member_list = group_member_list & set(repurchase_member_list)
                        repurchase_member_list -= {str(event.self_id)}
                        # 已注册但不存在的账户
                        logoff_group_member = group_member_list - set(live_group_member_list)
                        logoff_group_member -= {str(event.self_id)}
                        # 回收股票
                        for user_id in repurchase_member_list|logoff_group_member:
                            for stock, count in player[group_id][user_id]["stock"].items():
                                if stock != "value":
                                    market[stock]["stock"] += count
                                    player[group_id][user_id]["stock"][stock] = 0
                                    if user_id in self.Stock_Exchange[stock]:
                                        del self.Stock_Exchange[stock][user_id]
                                    info = f"账户：{group_id[0:4]}-{user_id[0:4]} 名称：{stock} 数量：{count}"
                                    msg += info + "\n"
                                    logger.info(info)
                        # 删除账户
                        for user_id in logoff_group_member:
                            info = f'账户：{group_id[0:4]}-{user_id[0:4]} 金币：{player[group_id][user_id]["gold"]}'
                            msg += info + "\n"
                            logger.info(info)
                            del player[group_id][user_id]
            if msg:
                russian_manager.save()
                self.market_data_save()
                self.Stock_Exchange_save()
                self.market_history_save()
                with open(Path(russian_path/"清理账户列表.txt"),"w") as f:
                    f.write(msg)
                return "清理完成"
            else:
                return "没有待清理的账户"

    async def survey(self, bot:Bot, event:MessageEvent, at:str = None):
        """
        资产调查
        """
        survey_dict = {}
        data = russian_manager._player_data
        for group_id in data.keys():
            for user_id in data[group_id].keys():
                player = data[group_id][user_id]
                survey_dict.setdefault(user_id,{"gold":0,"stock":Counter(),"all":0,"DIST":[]})
                survey_dict[user_id]["gold"] += player["gold"]
                survey_dict[user_id]["stock"] += Counter(player["stock"])
                sum = (player["gold"] + player["stock"]["value"])
                survey_dict[user_id]["all"] += sum
                survey_dict[user_id]["DIST"].append([group_id,0 if sum < 0 else sum])

        data = sorted(survey_dict.items(),key=lambda x:x[1]["all"],reverse=True)
        
        if at:
            user_id = at
            result = survey_dict[user_id]
            result["rank"] = data.index((user_id,survey_dict[user_id])) + 1
            try:
                tmp = await bot.get_stranger_info(user_id = int(user_id))
                nickname = tmp["nickname"]
            except:
                nickname = data[i][0]
            result["user_id"] = user_id
            result["nickname"] = nickname
            n = 1
            for seg in result["DIST"]:
                if seg[0] in self._market_data.keys():
                    seg[0] = self._market_data[seg[0]]["company_name"]
                else:
                    seg[0] = f"未注册{n}（{seg[0][-4:]}）"
                    n += 1
            return MessageSegment.image(await survey_result(result))
        else:
            msg = []
            for i in range(10):
                user_id = data[i][0]
                result = survey_dict[user_id]
                result["rank"] = i+1
                try:
                    tmp = await bot.get_stranger_info(user_id = int(user_id))
                    nickname = tmp["nickname"]
                except:
                    nickname = data[i][0]

                result["user_id"] = user_id
                result["nickname"] = nickname
            

                n = 1
                for seg in result["DIST"]:
                    if seg[0] in self._market_data.keys():
                        seg[0] = self._market_data[seg[0]]["company_name"]
                    else:
                        seg[0] = f"未注册{n}（{seg[0][-4:]}）"
                        n += 1

                msg.append(
                    {
                        "type": "node",
                        "data": {
                            "name": f"{bot_name}",
                            "uin": str(event.self_id),
                            "content": MessageSegment.image(await survey_result(result))
                            }
                        }
                    )
            return msg

    def freeze(self, bot:Bot, event:MessageEvent, at:str):
        """
        冻结个人资产
        """
        data = russian_manager._player_data
        market = self._market_data
        sum = 0
        for group_id in data.keys():
            if at in data[group_id].keys():
                player = data[group_id][at]
                sum += (player["gold"] + player["stock"]["value"])
                player["gold"] = 0
                for stock, count in player["stock"].items():
                    if stock != "value":
                        market[stock]["stock"] += count
                        player["stock"][stock] = 0
                        if at in self.Stock_Exchange[stock]:
                            del self.Stock_Exchange[stock][at]
            else:
                continue

        if sum > 500 * max_bet_gold:
            Frozen_Assets = 500
        elif sum > 50 * max_bet_gold:
            Frozen_Assets = int (sum / max_bet_gold)
        else:
            Frozen_Assets = int (sum / max_bet_gold) + 1

        props_data = russian_manager.get_global_data(at)["props"]
        props_data.setdefault(prop_code,0)
        props_data[prop_code] += Frozen_Assets

        russian_manager.save()
        russian_manager.global_data_save()
        self.market_data_save()
        self.Stock_Exchange_save()

        return f"【冻结】清算完成，总价值为{int(sum)}金币"

    def company_info(self,company_name:str):
        """
        公司信息
        :param company_name:公司名。
        """ 
        if company_name in self.Stock_Exchange.keys():
            lst = sorted(self.Stock_Exchange[company_name].items(),key = lambda x:x[1]["quote"])
            i = 0
            msg = ""
            while i < (len(lst) if len(lst) < 10 else 10):
                if lst[i][1]["stock"] > 0:
                    nickname = russian_manager._player_data[lst[i][1]["group_id"]][lst[i][0]]["nickname"]
                    msg += (
                        f'{nickname if len(nickname)<=12 else (nickname[0:10] + "...")}\n'
                        f'单价：{lst[i][1]["quote"]} 数量：{lst[i][1]["stock"]}\n'
                        )
                    i += 1
                else:
                    del lst[i]

            group_id = self._market_data[company_name]["group_id"]
            group_id = str(group_id)
            price = (
                self._market_data[company_name]["gold"]
                if self._market_data[company_name]["gold"] > self._market_data[company_name]["float_gold"]
                else self._market_data[company_name]["float_gold"]
                )
            origin_intro = self._market_data[company_name]["intro"]
            intro = ""
            flag = 0
            for x in origin_intro:
                intro += x
                if x == "\n":
                    flag = 0
                elif flag > 24:
                    intro += "\n"
                    flag = 0
                else:
                    if ord(x) < 0x200:
                        flag += 1
                    else:
                        flag += 2
            else:
                intro += "\n"
                intro = re.sub('[\r\n]+', '\n', intro)
            info = (
                f"【{company_name}】\n"
                "——————————————\n"
                f"注册单位：{group_id[:4]}...\n"
                f'注册时间：{datetime.fromtimestamp(self._market_data[group_id]["time"]).strftime("%Y-%m-%d %H:%M")}\n'
                "——————————————\n"
                f'固定资产：{round(self._market_data[company_name]["gold"], 2)} 金币\n'
                f'市场流动：{int(self._market_data[company_name]["group_gold"])} 金币\n'
                f'发行价格：{round(price/20000,2)} 金币\n'
                f'结算价格：{round(self._market_data[company_name]["float_gold"] / 20000, 2)} 金币\n'
                f'剩余数量：{self._market_data[company_name]["stock"]} 株\n'
                "——————————————\n"
                "市场：\n" + msg +
                "——————————————\n"
                "简介：\n" + intro +
                "——————————————"
                )
            return info
        else:
            return None

    def update_intro(self,company_name:str,intro:str):
        """
        更新简介
        :param company_name:公司名。
        """ 
        if company_name in self.Stock_Exchange.keys():
            self._market_data[company_name]["intro"] = intro
            self.market_data_save()

    def value_update(self, group_id:str,user_id:str) -> float:
        """
        刷新持股信息
        :param group_id:账户所在群
        :param user_id:用户名
        """
        value = 0.0
        stock_data = russian_manager._player_data[group_id][user_id]["stock"]
        company_name = self._market_data.get(group_id,{"company_name": "value"})["company_name"]
        for i in stock_data.keys():
            if  i in ["value",company_name]:
                continue
            else:
                value += stock_data[i] * self._market_data[i]["float_gold"] / 20000
        return value

    def company_update(self,group_id:str):
        """
        刷新公司信息
        :param event: event
        """
        company_name = self._market_data[group_id]["company_name"]
        gold = self._market_data[company_name]["gold"]

        # 更新group_gold
        group_gold = float(russian_manager.total_gold(group_id,1000))
        self._market_data[company_name]["group_gold"] = group_gold

        # 更新gold
        company_gold = group_gold * (
            0.5 # 基础数值
            + 0.5 * ( 1 - self._market_data[company_name]["stock"]/20000) # 市场融资
            + self.market_index.get(company_name,0) # 市场指数
            )

        self._market_data[company_name]["gold"] += 0.002 * (company_gold - gold)

        # 更新float_gold
        float_gold = self._market_data[company_name]["float_gold"]
        self._market_data[company_name]["float_gold"] = (
            float_gold * (1.0 + random.uniform(-0.4, 0.4)) * 0.4 # 继承价格浮动
            + group_gold * 0.15 # 市场流动
            + gold * 0.3 # 固定资产
            )

        # 记录历史价格
        buy = self._market_data[company_name]["gold"] / 20000
        sell = self._market_data[company_name]["float_gold"] / 20000

        self.market_history.setdefault(company_name,[])
        self.market_history[company_name].append([time.time(),buy,sell])
        while len(self.market_history[company_name]) > 1200:
            del self.market_history[company_name][0]

    def reset_market_index(self):
        """
        市场指数更新
        """
        for group_id in russian_manager._player_data.keys():
            if group_id in market_manager._market_data.keys():
                company_name = self._market_data[group_id]["company_name"]
                self.market_index[company_name] = random.uniform(-0.5, 0.1)
                logger.info(f'【{company_name}】市场指数更新为 {self.market_index.get(company_name,0)}')

    def intergroup_transfer(self, event, company_name, gold) -> str:
        """
        跨群转移金币到自己的账户
        :param event:event
        :param company_name:转入公司名
        :param gold:转入金币
        """
        if company_name in self._market_data.keys():
            company_id = str(self._market_data[company_name]["group_id"])
            group_id = str(event.group_id)
            user_id = str(event.user_id)
            gold = abs(int(gold))
            my_gold = russian_manager.get_user_data(event)["gold"]
            if gold > my_gold:
                return f"您的账户没有足够的金币，你的金币：{my_gold}"
            if not user_id in russian_manager._player_data[company_id].keys():
                return f"你在【{company_name}】未注册"

            first = russian_manager.total_gold(company_id,1)
            sum = russian_manager.total_gold(company_id,10)

            if first > (5 * max_bet_gold) and first >= sum - first:
                return f"【{company_name}】不稳定，不可转入。"
            if gold > first:
                return f"【{company_name}】最多可转入 {first} 金币"

            tab = ""
            if gold <= (5 * max_bet_gold):
                flag = russian_manager._player_data[group_id][user_id]["props"].get("42001",0)
                if flag > 0:
                    fee = 0
                    tab = f"【{props_library['42001']['name']}】"
                else:
                    fee = int(gold * 0.01)
                    tab = ""
            else:
                fee = int(gold * 0.2)
                tab = ""

            russian_manager._player_data[company_id][user_id]["gold"] += gold - fee
            russian_manager._player_data[group_id][user_id]["gold"] -= gold
            russian_manager.save()
            return f"向 【{company_name}】 转移 {gold}金币，扣除手续费：{fee}{tab}，实际到账金额{gold - fee}"
        else:
            return f"【{company_name}】未注册"



market_manager = MarketManager()
