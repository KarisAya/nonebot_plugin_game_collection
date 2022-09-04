from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent, Message, MessageSegment, Bot
from typing import Optional, Tuple, Union, List, Dict
from datetime import datetime
from nonebot.log import logger
from pathlib import Path
from io import BytesIO
from nonebot_plugin_imageutils import Text2Image
import nonebot
import asyncio
import random
import time
import os
from .config import Config
from .utils import market_linechart, market_candlestick
try:
    import ujson as json
except ModuleNotFoundError:
    import json

global_config = nonebot.get_driver().config
russian_config = Config.parse_obj(global_config.dict())

russian_path = russian_config.russian_path

# 签到金币随机范围
sign_gold = russian_config.sign_gold
revolt_sign_gold = russian_config.revolt_sign_gold
security_gold = russian_config.security_gold

# bot昵称
bot_name = list(global_config.nickname)[0] if global_config.nickname else "bot"

# 市场信息显示方式
market_info_chain = russian_config.market_info_chain
market_info_type = russian_config.market_info_type

# 赌注
max_bet_gold = russian_config.max_bet_gold
race_bet_gold = russian_config.race_bet_gold
gacha_gold = russian_config.gacha_gold

# 赌注读取2
russian_config = Config.parse_obj(nonebot.get_driver().config.dict())

max_bet_gold = russian_config.max_bet_gold
race_bet_gold = russian_config.race_bet_gold

# 定义永久道具
constant_props = ("钻石","路灯挂件标记")

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
        if not file.exists():
            old_file = Path(os.path.dirname(__file__)) / "russian_data.json"
            if old_file.exists():
                os.rename(old_file, file)
        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                self._player_data = json.load(f)

    def sign(self, event: GroupMessageEvent) -> Tuple[str, int]:
        """
        签到
        :param event: event
        """
        self._init_player_data(event)
        if self._player_data[str(event.group_id)][str(event.user_id)]["is_sign"]:
            return "你已经签过到了哦", -1
        gold = random.randint(sign_gold[0], sign_gold[1])
        self._player_data[str(event.group_id)][str(event.user_id)]["gold"] += gold
        self._player_data[str(event.group_id)][str(event.user_id)]["make_gold"] += gold
        self._player_data[str(event.group_id)][str(event.user_id)]["is_sign"] = True
        self.save()
        return (
            random.choice(["祝你好运~", "可别花光了哦~"]) + f"\n你获得了 {gold} 金币",
            gold,
        )

    def revolt_sign(self, event: GroupMessageEvent) -> Tuple[str, int]:
        """
        revolt签到
        :param event: event
        """
        self._init_player_data(event)
        if self._player_data[str(event.group_id)][str(event.user_id)]["revolution"]:
            return "你没有待领取的金币", -1
        gold = random.randint(revolt_sign_gold[0], revolt_sign_gold[1])
        self._player_data[str(event.group_id)][str(event.user_id)]["gold"] += gold
        self._player_data[str(event.group_id)][str(event.user_id)]["make_gold"] += gold
        self._player_data[str(event.group_id)][str(event.user_id)]["revolution"] = True
        self.save()
        return ("这是你重置获得的金币~"+f"\n你获得了 {gold} 金币",gold)

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
                elif self._current_player[event.group_id]["game"] == "dice":
                    money = self._current_player[event.group_id]["money_max"]
                elif self._current_player[event.group_id]["game"] == "poker":
                    money = self._current_player[event.group_id]["money"]
                else:
                    return None

                if self._player_data[str(event.group_id)][str(event.user_id)]["gold"] < money:
                    return Message(MessageSegment.at(event.user_id) + "你的金币不足以接受这场对决！")
                else:
                    player2_name = event.sender.card or event.sender.nickname
                    self._current_player[event.group_id][2] = event.user_id
                    self._current_player[event.group_id]["player2"] = player2_name
                    self._current_player[event.group_id]["time"] = time.time()
                    if self._current_player[event.group_id]["game"] == "russian":
                        return Message(
                            f"{player2_name}接受了对决！\n"
                            f"请{MessageSegment.at(self._current_player[event.group_id][1])}开枪！"
                            )
                    elif self._current_player[event.group_id]["game"] == "dice":
                        self._current_player[event.group_id]["lose"] = event.user_id
                        self._current_player[event.group_id]["lose_name"] = player2_name
                        return Message(
                            f"{player2_name}接受了对决！\n"
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
                        output = BytesIO()
                        Text2Image.from_text(message, 50, spacing = 30).to_image("white",(20,20)).save(output, format="png")
                        return MessageSegment.image(output)
                    else:
                        return Message("error")

    async def refuse(self, bot: Bot, event: GroupMessageEvent) -> Union[str, Message]:
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
            output = BytesIO()
            Text2Image.from_text(message, 50, spacing = 30).to_image("white",(20,20)).save(output, format="png")
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
        for i in range(len(st["hand"])):
            card_msg += f'【{suit_name_dict[st["hand"][i][0]]} {point_dict[st["hand"][i][1]]}】'
            if st["hand"][i][0] == 1:
                st["DEF"] += st["hand"][i][1]
                skill_msg += f'♤防御力强化了 {st["hand"][i][1]}\n'
            elif st["hand"][i][0] == 2:
                st["HP"] += st["hand"][i][1]
                skill_msg += f'♡生命值增加了 {st["hand"][i][1]}\n'
            elif st["hand"][i][0] == 3:
                st["SP"] += 2 * st["hand"][i][1]
                skill_msg += f'♧技能点增加了 {st["hand"][i][1]}\n'
            elif st["hand"][i][0] == 4:
                st["ATK"] += st["hand"][i][1]
                skill_msg += f'♢发动了攻击 {st["hand"][i][1]}\n'
            else:
                msg = "出现未知错误"
            st["SP"] = 0 if st["SP"] - st["hand"][i][1] < 0 else st["SP"] - st["hand"][i][1]
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
                    output = BytesIO()
                    Text2Image.from_text(msg, 50, spacing = 30).to_image("white",(20,60)).save(output, format="png")
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
                        output = BytesIO()
                        Text2Image.from_text(msg, 50, spacing = 30).to_image("white",(20,60)).save(output, format="png")
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
                output = BytesIO()
                Text2Image.from_text(message, 50, spacing = 30).to_image("white",(20,20)).save(output, format="png")

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

    def reset_gold(self):
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

    def interest(self):
        """
        每日利息发放
        """
        for group in self._player_data.keys():
            for user_id in self._player_data[group].keys():
                if self._player_data[group][user_id]["gold"] > 0:
                    IN = int(self._player_data[group][user_id]["gold"] * 0.02)
                    self._player_data[group][user_id]["gold"] += IN
                    self._player_data[group][user_id]["make_gold"] += IN
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

        flag = self._player_data[str(event.group_id)][str(win_user_id)]["props"].get("钻石会员卡",0)
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
            (f"『20%额外奖励』\n"if extra != 0 else "")+
            f" 胜者：{win_name}\n"
            f' 结算：{win_user["gold"]- gold + fee - extra} + {gold + extra - fee} = {win_user["gold"]}\n'
            f' 胜场:败场：{win_user["win_count"]}:{win_user["lose_count"]}\n'
            f' 胜率：{str(win_user["win_count"]/(win_user["win_count"] + win_user["lose_count"])*100)[:5]}%\n'
            "——————————————\n" +
            self.Achieve_list(lose_user)+
            (f"『金币补贴』\n"if security != 0 else "")+
            (f"『20%结算补贴』\n"if off != 0 else "")+
            f" 败者：{lose_name}\n"
            f' 结算：{lose_user["gold"] - security + gold - off} - {gold - off} = {lose_user["gold"] - security}\n'+
            (f" 已领取补贴：{security}\n"if security != 0 else "")+
            f' 胜场:败场：{lose_user["win_count"]}:{lose_user["lose_count"]}\n'
            f' 胜率：{str(lose_user["win_count"]/(lose_user["win_count"] + lose_user["lose_count"])*100)[:5]}%\n'
            "——————————————\n"+
            f"手续费：{fee} " + ("『钻石会员卡』"if rand == -1 else f"({float(rand)}%)")
            )
        
        output = BytesIO()
        Text2Image.from_text(message, 50, spacing = 10).to_image("white",(20,20)).save(output, format="png")
        await bot.send(event,MessageSegment.image(output))

        if game_str:
            output = BytesIO()
            Text2Image.from_text(game_str, 50, spacing = 20).to_image("white",(20,20)).save(output, format="png")
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

        flag = self._player_data[group_id][win_user_id]["props"].get("20%额外奖励",0)
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

        
        flag = self._player_data[group_id][lose_user_id]["props"].get("20%结算补贴",0)
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
        all_user = list(player_data[group_id].keys())
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
            if first > 8000 and first >= sum - first:
                for i in range(len(all_user) if len(all_user) < 10 else 10):
                    _max = max(all_user_data)
                    _max_id = all_user[all_user_data.index(_max)]
                    player_data[group_id][_max_id]["gold"] = int(_max*0.2)
                    for company_name in player_data[group_id][_max_id]["stock"].keys():
                        if company_name == "value":
                            continue
                        else:
                            stock = int(player_data[group_id][_max_id]["stock"][company_name] * 0.8)
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
                return f"{first_name}的金币需要达到{round(8000 if sum - first < 8000 else sum - first, 2)}才可以发起重置。"
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
        flag = self._player_data[group_id][user_id]["props"].get("钻石会员卡",0)
        if flag > 0:
            fee = 0
        else:
            fee = int(unsettled * 0.02)

        self._player_data[group_id][user_id]["gold"] -= unsettled
        self._player_data[group_id][at_player_id]["gold"] += unsettled - fee
        self.save()
        return (
            f"{self._player_data[group_id][user_id]['nickname']} 向 {self._player_data[group_id][at_player_id]['nickname']} 转账{unsettled}金币\n"+
            ("『钻石会员卡』免手续费" if flag > 0 else f"扣除2%手续费：{fee}，实际到账金额{unsettled - fee}")
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
        if props == "路灯挂件标记":
            if user_data["Achieve_revolution"] + user_data["props"].get(props,0) < count:
                return "数量不足"
            else:
                user_data["props"].setdefault(props,0)
                user_data["props"][props] -= count
                at_user_data["props"].setdefault(props,0)
                at_user_data["props"][props] += count
                self.save()
                return f"{count} 个 {props} 已送出"
        else:
            if user_data["props"].get(props,0) < count:
                return "数量不足"
            else:
                user_data["props"][props] -= count
                at_user_data["props"].setdefault(props,0)
                at_user_data["props"][props] += count
                self.save()
                return f"{count} 个 {props} 已送出"

    def Achieve_list(self,user_data):
        """
        送道具
        :param user_data: russian_manager.get_user_data(event)
        """
        rank = ""
        count = user_data["props"].get("四叶草标记",0)
        if count > 0:
            rank += "𝐿𝒰𝒞𝒦𝒴 ✤ 𝒞𝐿𝒪𝒱𝐸𝑅\n"
        count = user_data["Achieve_revolution"] + user_data["props"].get("路灯挂件标记",0)
        if count > 0:
            if count < 5:
                rank += f"{count*'☆ '}路灯挂件{count*' ☆'}\n"
            else: 
                rank += f"❀ 路灯挂件 Lv.{count} ❀\n"
        count = user_data["gold"]
        if count > max_bet_gold:
            rank += f"◆◇ 金库 Lv.{int(count/max_bet_gold)} ◆◇\n"
        count = user_data["Achieve_victory"]
        if count >1:
            rank += f"◆◇ 连胜 Lv.{count-1} ◆◇\n"
        count = user_data["Achieve_lose"]
        if count >1:
            rank += f"◆◇ 连败 Lv.{count-1} ◆◇\n"
        return rank

    def my_info(self, event: GroupMessageEvent) -> str:
        """
        资料卡
        :param event: event
        """
        user_data = self.get_user_data(event)
        nickname = user_data["nickname"]
        gold = user_data["gold"]
        make_gold = user_data["make_gold"]
        lose_gold = user_data["lose_gold"]
        is_sign = user_data["is_sign"]
        security = user_data["security"]
        win_count = user_data["win_count"]
        lose_count = user_data["lose_count"]
        stock = user_data["stock"]
        stock["value"] = market_manager.value_update(str(event.group_id),str(event.user_id))
        my_stock = []
        stock_info = ""
        for x in stock.keys():
            if x == "value" or  stock[x] == 0 :
                continue
            else:
                my_stock.append([x,round(market_manager._market_data[x]["float_gold"] * stock[x] / 20000,2)])
        else:
            my_stock.sort(key = lambda x:x[1],reverse = True)
            for i in range(len(my_stock)):
                stock_info += f'【{my_stock[i][0]}】\n持有：{stock[my_stock[i][0]]} 株\n价值：{my_stock[i][1]} 金币\n'

        info = (
            f'【{nickname}】\n'
            "——————————————\n"
            + ("" if self.Achieve_list(user_data) == "" else self.Achieve_list(user_data) + "——————————————\n") +
            f'金币：{gold}\n'
            f'持有价值：{round(stock["value"],2)}\n'
            f'赚取金币：{make_gold}\n'
            f'输掉金币：{lose_gold}\n'
            "——————————————\n"
            f'胜场:败场：{win_count}:{lose_count}\n'
            f'胜率：{str((win_count/(win_count + lose_count) if win_count + lose_count > 0 else 0 ) * 100 )[:5]}%\n'
            "——————————————\n"
            f'今日签到：{"已签到"if is_sign else "未签到"}\n'
            f'今日补贴：还剩 {3 - security} 次\n'
            "——————————————\n" +
            stock_info
            )
        return info

    def slot(self, event: GroupMessageEvent,gold:int):
        """
        抽花色
        :param event: event
        :param gold: 金币
        """
        group_id = str(event.group_id)
        user_id = str(event.user_id)
        
        if gold > self.get_user_data(event)["gold"]:
            return f'你没有足够的金币，你的金币：{self._player_data[group_id][user_id]["gold"]}。'
        if self._player_data[group_id][user_id]["slot"] > 2:
            return '你的本轮次数已用光。'

        self._player_data[group_id][user_id]["slot"] += 1
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
            self._player_data[group_id][user_id]["gold"] += gold *7
            self._player_data[group_id][user_id]["make_gold"] += gold *7
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
            self._player_data[group_id][user_id]["gold"] -= gold
            self._player_data[group_id][user_id]["lose_gold"] += gold
            msg =(
                f"你抽到的花色为：\n"+
                suit+
                f"\n你失去了{gold}金币 ，祝你好运~"
                )

        self.save()
        return msg

    def gacha(self, event: GroupMessageEvent):
        """
        十连
        :param event: event
        """
        group_id = str(event.group_id)
        user_id = str(event.user_id)
        
        if self.get_user_data(event)["gold"] < gacha_gold:
            return f'10连抽卡需要{gacha_gold}金币，你的金币：{self._player_data[group_id][user_id]["gold"]}。'
        else:
            self._player_data[group_id][user_id]["gold"] -= gacha_gold
            msg = '\n'
            for i in range(10):
                props = random.randint(1,200)
                if props in range(1,21):
                    self._player_data[group_id][user_id]["props"].setdefault("四叶草标记",0)
                    if self._player_data[group_id][user_id]["props"]["四叶草标记"] < 7:
                        self._player_data[group_id][user_id]["props"]["四叶草标记"] += 1
                    msg += "『四叶草标记』 ☆☆☆\n"
                elif props in range(21,31):
                    self._player_data[group_id][user_id]["props"].setdefault("钻石会员卡",0)
                    if self._player_data[group_id][user_id]["props"]["钻石会员卡"] < 7:
                        self._player_data[group_id][user_id]["props"]["钻石会员卡"] += 1
                    msg += "『钻石会员卡』 ☆☆☆☆\n"
                elif props in range(31,41):
                    msg += "『高级空气』 ☆☆☆☆\n"
                elif props in range(41,46):
                    self._player_data[group_id][user_id]["props"].setdefault("20%结算补贴",0)
                    if self._player_data[group_id][user_id]["props"]["20%结算补贴"] < 7:
                        self._player_data[group_id][user_id]["props"]["20%结算补贴"] += 1
                    msg += "『20%结算补贴』 ☆☆☆☆☆\n"
                elif props in range(46,51):
                    self._player_data[group_id][user_id]["props"].setdefault("20%额外奖励",0)
                    if self._player_data[group_id][user_id]["props"]["20%额外奖励"] < 7:
                        self._player_data[group_id][user_id]["props"]["20%额外奖励"] += 1
                    msg += "『20%额外奖励』 ☆☆☆☆☆\n"
                elif props in range(51,56):
                    msg += "『进口空气』 ☆☆☆☆☆\n"
                elif props in range(56,61):
                    msg += "『特级空气』 ☆☆☆☆☆\n"
                elif props in range(61,81):
                    msg += "『优质空气』 ☆☆☆\n"
                elif props == 100:
                    self._player_data[group_id][user_id]["props"].setdefault("钻石",0)
                    self._player_data[group_id][user_id]["props"]["钻石"] += 1
                    msg += "『钻石』 ☆☆☆☆☆☆\n"
                elif props == 200:
                    msg += "『纯净空气』 ☆☆☆☆☆☆\n"
                else:
                    msg += "『空气』 ☆\n"
                    pass
            else:
                msg = msg[:-1]
                self.save()
        return msg



russian_manager = GameManager()



class MarketManager:

    def __init__(self):
        self._market_data = {}
        self.market_index = {}  # 市场指数
        file = russian_path / "data" / "russian" / "market_data.json"
        self.file = file
        if not file.exists():
            old_file = Path(os.path.dirname(__file__)) / "market_data.json"
            if old_file.exists():
                os.rename(old_file, file)
        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                self._market_data = json.load(f)

        self.Stock_Exchange = {}
        file = russian_path / "data" / "russian" / "Stock_Exchange.json"
        self.Stock_Exchange_file = file
        if not file.exists():
            old_file = Path(os.path.dirname(__file__)) / "Stock_Exchange.json"
            if old_file.exists():
                os.rename(old_file, file)
        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                self.Stock_Exchange = json.load(f)

        self.market_history = {}
        file = russian_path / "data" / "russian" / "market_history.json"
        self.market_history_file = file
        if not file.exists():
            old_file = Path(os.path.dirname(__file__)) / "market_history.json"
            if old_file.exists():
                os.rename(old_file, file)
        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                self.market_history = json.load(f)

        self.info_temp = [[],0]

    def _init_market_data(self, event: GroupMessageEvent,company_name: str):
        """
        初始化市场数据
        :param event: event
        :param company_name:公司名
        """
        group_id = str(event.group_id)
        if group_id in self._market_data.keys():
            return f"群号：{group_id}已注册"
        elif company_name in self._market_data.keys():
            return f"名称：{company_name}已注册"
        else:
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

    def Market_sell(self, event: GroupMessageEvent, company_name: str, quote:float, stock:int) -> str:
        """
        市场卖出
        :param event: event
        :param company_name:公司名
        :param quote:报价
        :param stock:数量
        """
        group_id = str(event.group_id)
        user_id = str(event.user_id)
        my_stock = russian_manager.get_user_data(event)["stock"].get(company_name,0)
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

    def Market_buy(self, event: GroupMessageEvent, company_name: str, stock:int):
        """
        市场买入
        :param company_name:公司名
        :param stock:数量
        """
        group_id = str(event.group_id)
        user_id = str(event.user_id)
        my_gold = russian_manager.get_user_data(event)["gold"]
        if self.Stock_Exchange.get(company_name) == None:
            return f"【{company_name}】未注册"
        else:
            lst = sorted(self.Stock_Exchange[company_name].items(),key = lambda x:x[1]["quote"])

            count = 0
            for i in range(len(lst)):
                count += lst[i][1]["stock"]

            for i in lst:
                if i[0] == user_id:
                    lst.remove(i)

            if lst == []:
                return f"市场上没有【{company_name}】"
            else:
                stock = stock if count > stock else count
                TL = {}
                gold = 0.0
                for i in range(len(lst)):
                    _stock = lst[i][1]["stock"]
                    _quote = lst[i][1]["quote"]
                    _group_id = str(lst[i][1]["group_id"])

                    _count = 0
                    for j in range(_stock if _stock < stock else stock):
                        _count += 1

                    stock -= _count

                    TL.update({lst[i][0]:[_quote,_count,_group_id]})
                    
                    gold += _quote * _count

                if gold > my_gold:
                    return (
                        "金币不足\n"
                        f'你的金币：{my_gold}'
                        f"需要金币：{int(gold)}"
                        )
                else:
                    count = 0
                    for i in range(len(lst)):
                        unsettled = int (TL[lst[i][0]][0] * TL[lst[i][0]][1])
                        
                        russian_manager._player_data[group_id][user_id]["gold"] -= unsettled
                        russian_manager._player_data[TL[lst[i][0]][2]][lst[i][0]]["gold"] += unsettled
                        
                        russian_manager._player_data[group_id][user_id]["stock"]["value"] = self.value_update(group_id,user_id)
                        russian_manager._player_data[TL[lst[i][0]][2]][lst[i][0]]["stock"]["value"] = self.value_update(TL[lst[i][0]][2],lst[i][0])
                        
                        russian_manager._player_data[group_id][user_id]["stock"].setdefault(company_name,0)
                        russian_manager._player_data[group_id][user_id]["stock"][company_name] += TL[lst[i][0]][1]
                   
                        russian_manager._player_data[TL[lst[i][0]][2]][lst[i][0]]["stock"].setdefault(company_name,0)
                        russian_manager._player_data[TL[lst[i][0]][2]][lst[i][0]]["stock"][company_name] -= TL[lst[i][0]][1]
                        
                        self.Stock_Exchange[company_name][lst[i][0]]["stock"] -= TL[lst[i][0]][1]
                        count += TL[lst[i][0]][1]
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

    def Market_public(self, event: GroupMessageEvent,company_name: str):
        """
        公司上市
        :param event: event
        :param company_name:公司名
        """
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

    def company_buy(self,event: GroupMessageEvent, company_name:str ,stock:int) -> str:
        """
        购买公司发行股票
        :param event: event
        :param company_name:公司名
        :param stock: 购买的股票数量
        """
        group_id = str(event.group_id)
        user_id = str(event.user_id)
        my_gold = russian_manager.get_user_data(event)["gold"]
        company = self._market_data.get(company_name)
        if company == None:
            return f"公司名：{company_name} 未注册"
        else:
            stock = stock if stock < company["stock"] else company["stock"]
            if stock > 0:
                value = 0.0
                _gold = company["gold"] if  company["gold"] > company["float_gold"] else company["float_gold"]
                for i in range(stock):
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

    def company_clear(self,event: GroupMessageEvent, company_name:str ,stock:int) -> str:
        """
        股权债务清算
        :param event: event
        :param company_name:公司名
        :param stock: 清算的数量
        """ 
        group_id = str(event.group_id)
        user_id = str(event.user_id)
        my_stock = russian_manager.get_user_data(event)["stock"].get(company_name)
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
            for i in range(stock):
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

    def Market_info(self, event, company_name:str):
        """
        市场信息
        :param company_name:公司名，为空则是总览。
        """ 
        msg = ""
        if company_name in self.Stock_Exchange.keys():
            lst = sorted(self.Stock_Exchange[company_name].items(),key = lambda x:x[1]["quote"])
            for i in range(len(lst) if len(lst) < 10 else 10):
                if lst[i][1]["stock"] > 0:
                    nickname = russian_manager._player_data[lst[i][1]["group_id"]][lst[i][0]]["nickname"]
                    msg += (
                        f'{nickname}\n'
                        f'单价：{lst[i][1]["quote"]} 数量：{lst[i][1]["stock"]}\n'
                        )
            if msg:
                msg = (f'【{company_name}】\n'"——————————————\n") + msg
                msg = msg[:-1]
                output = BytesIO()
                Text2Image.from_text(msg,50,spacing = 10).to_image("white",(20,20)).save(output, format="png")
                msg = MessageSegment.image(output)
        else:
            lst = []
            for x in self._market_data.keys():
                if self._market_data[x].get("time") == None:
                    lst.append([x,self._market_data[x]["group_gold"]])
            else:
                lst.sort(key = lambda x:x[1],reverse = True)

            msg_lst = []
            n = len(lst)
            if n:
                for i in range(n):
                    price = (
                        self._market_data[lst[i][0]]["gold"]
                        if self._market_data[lst[i][0]]["gold"] > self._market_data[lst[i][0]]["float_gold"]
                        else self._market_data[lst[i][0]]["float_gold"]
                        )
                    msg_lst.append(
                        f'【{lst[i][0]}】\n'
                        "——————————————\n"
                        f'固定资产：{round(self._market_data[lst[i][0]]["gold"], 2)} 金币\n'
                        f'市场流动：{int(lst[i][1])} 金币\n'
                        f'发行价格：{round(price/20000,2)} 金币\n'
                        f'结算价格：{round(self._market_data[lst[i][0]]["float_gold"] / 20000, 2)} 金币\n'
                        f'剩余数量：{self._market_data[lst[i][0]]["stock"]} 株\n'
                        "——————————————"
                        )
                else:
                    if market_info_chain == False or isinstance(event, PrivateMessageEvent):
                        for i in range(n):
                            msg += msg_lst[i] + "\n"
                        else:
                            msg = msg[:-1]
                            if market_info_type == "image":
                                output = BytesIO()
                                Text2Image.from_text(msg,50,spacing = 10).to_image("white",(20,20)).save(output, format="png")
                                msg = MessageSegment.image(output)
                            else:
                                pass
                    else:
                        msg = []
                        if market_info_type == "image" :
                            for i in range(n):
                                output = BytesIO()
                                Text2Image.from_text(msg_lst[i],50,spacing = 10).to_image("white",(20,20)).save(output, format="png")
                                msg.append(
                                    {
                                        "type": "node",
                                        "data": {
                                            "name": f"{bot_name}",
                                            "uin": str(event.self_id),
                                            "content": MessageSegment.image(output)
                                            }
                                        }
                                    )
                        else:
                            for i in range(n):
                                msg.append(
                                    {
                                        "type": "node",
                                        "data": {
                                            "name": f"{bot_name}",
                                            "uin": str(event.self_id),
                                            "content": msg_lst[i]
                                            }
                                        }
                                    )
            else:
                msg = "市场不存在..."
        return msg

    def Market_info_pro(self, event):
        """
        市场详细信息
        """
        if self.info_temp[1] == 1:
            return self.info_temp[0]
        else:
            lst = []
            for x in self._market_data.keys():
                if self._market_data[x].get("time") == None:
                    lst.append([x,self._market_data[x]["group_gold"]])
            else:
                lst.sort(key = lambda x:x[1],reverse = True)

            if lst:
                msg = []
                for i in range(len(lst)):
                    price = (
                        self._market_data[lst[i][0]]["gold"]
                        if self._market_data[lst[i][0]]["gold"] > self._market_data[lst[i][0]]["float_gold"]
                        else self._market_data[lst[i][0]]["float_gold"]
                        )
                    msg.append(
                        {
                            "type": "node",
                            "data": {
                                "name": f"{bot_name}",
                                "uin": str(event.self_id),
                                "content": (
                                    f'【{lst[i][0]}】\n'
                                    "——————————————\n"
                                    f'固定资产：{round(self._market_data[lst[i][0]]["gold"], 2)} 金币\n'
                                    f'市场流动：{int(lst[i][1])} 金币\n'
                                    f'发行价格：{round(price/20000,2)} 金币\n'
                                    f'结算价格：{round(self._market_data[lst[i][0]]["float_gold"] / 20000, 2)} 金币\n'
                                    f'剩余数量：{self._market_data[lst[i][0]]["stock"]} 株\n'
                                    "——————————————"
                                    ) 
                                }
                            }
                        )
                    msg.append(
                        {
                            "type": "node",
                            "data": {
                                "name": f"{bot_name}",
                                "uin": str(event.self_id),
                                "content": MessageSegment.image(market_linechart((32,9), self.market_history[lst[i][0]], lst[i][0]))
                                }
                            }
                        )
                    msg.append(
                        {
                            "type": "node",
                            "data": {
                                "name": f"{bot_name}",
                                "uin": str(event.self_id),
                                "content": MessageSegment.image(market_candlestick((32,9), 6, self.market_history[lst[i][0]], lst[i][0]))
                                }
                            }
                        )
                else:
                    self.info_temp[0] = msg
                    self.info_temp[1] = 1
                    return msg
            else:
                return "市场不存在..."

    def company_info(self,company_name:str):
        """
        公司信息
        :param company_name:公司名。
        """ 
        msg = ""
        if company_name in self.Stock_Exchange.keys():
            lst = sorted(self.Stock_Exchange[company_name].items(),key = lambda x:x[1]["quote"])
            for i in range(len(lst) if len(lst) < 10 else 10):
                if lst[i][1]["stock"] > 0:
                    nickname = russian_manager._player_data[lst[i][1]["group_id"]][lst[i][0]]["nickname"]
                    msg += f'{nickname}\n单价：{lst[i][1]["quote"]} 数量：{lst[i][1]["stock"]}\n'

            group_id = self._market_data[company_name]["group_id"]
            group_id = str(group_id)
            price = (
                self._market_data[company_name]["gold"]
                if self._market_data[company_name]["gold"] > self._market_data[company_name]["float_gold"]
                else self._market_data[company_name]["float_gold"]
                )
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
                "市场：\n"+ msg +
                "——————————————\n"
                "简介：\n"f'{self._market_data[company_name]["intro"]}'
                )
            return info

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

        self._market_data[company_name]["gold"] += 0.05 * (company_gold - gold)

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
            
            flag = russian_manager._player_data[group_id][user_id]["props"].get("钻石会员卡",0)
            if flag > 0:
                fee = 0
            else:
                fee = int(gold * 0.01)

            russian_manager._player_data[company_id][user_id]["gold"] += gold - fee
            russian_manager._player_data[group_id][user_id]["gold"] -= gold
            russian_manager.save()
            
            return (
                f"向 【{company_name}】 转移 {gold}金币\n"+
                ("『钻石会员卡』免手续费" if flag > 0 else f"扣除1％手续费：{fee}，实际到账金额{gold - fee}")
                )
        else:
            return f"【{company_name}】未注册"



market_manager = MarketManager()
