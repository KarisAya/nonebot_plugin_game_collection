from typing import Tuple,Dict
from pydantic import BaseModel
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    Message,
    MessageSegment
    )
import random
import time
import asyncio

from .utils.utils import get_message_at
from .utils.chart import text_to_png
from .data.data import props_library
from .config import bot_name, security_gold, max_bet_gold, max_player, min_player

from .HorseRace.start import load_dlcs
from .HorseRace.race_group import race_group

from .Manager import data, try_send_private_msg
from . import Manager

user_data = data.user
group_data = data.group



"""+++++++++++++++++
——————————
     赛马小游戏
——————————
+++++++++++++++++"""

def race_create_check(event:GroupMessageEvent):
    """
    检查是否可以创建赛马
    """
    global current_games
    group_id = event.group_id
    if group_id not in current_games:
        return None
    session = current_games[group_id]
    overtime = time.time() - session.time + 180
    if session.at == -1:
        race:race_group = session.info["race_group"]
        if race.start == 0:
            if overtime < 120:
                return "一场赛马正在报名中"
            else:
                return None
        else:
            return f"一场赛马正在进行中，遇到问题可以{f'在{t}秒后' if (t := int(180 - overtime)) > 0 else ''}输入【赛马重置】重置游戏"
    else:
        return session.create_check(event)

def RaceNew(event:GroupMessageEvent, gold:int ):
    """
    赛马创建
    """
    global current_games
    if msg := race_create_check(event):
        return msg
    current_games[event.group_id] =  Session(
        time = time.time() + 180,
        player1_id = event.user_id,
        at = -1,
        gold = gold,
        info = {"game":"horse race","race_group":race_group()}
        )
    return ("\n"
             "> 创建赛马比赛成功！\n"
             "> 输入 【赛马加入 名字】 即可加入赛马。")

def RaceJoin(event:GroupMessageEvent, horsename:str):
    """
    赛马加入
    """
    global current_games
    group_id = event.group_id
    if group_id not in current_games:
        return "赛马活动未开始，请输入【赛马创建】创建赛马场"
    session = current_games[event.group_id]
    if session.info["game"] != "horse race":
        return "其他对战进行中。"
    user,group_account = Manager.locate_user(event)
    user_id = user.user_id
    if (gold := group_account.gold) < session.gold:
        return f"报名赛马需要{session.gold}金币，你的金币：{gold}。"
    race:race_group = session.info["race_group"]
    if race.start != 0:
        return
    if (query_of_player := race.query_of_player()) >= max_player:
        return "加入失败！赛马场就那么大，满了满了！"
    if race.is_player_in(user_id) == True:
        return "加入失败！您已经加入了赛马场!"
    if not horsename:
        return "请输入你的马儿名字"
    horsename = horsename[:2]+"酱" if len(horsename) > 5 else horsename
    race.add_player(horsename, user_id, group_account.nickname)
    user.gold -= session.gold
    group_account.gold -= session.gold
    return  ("\n"
             "> 加入赛马成功\n"
             "> 赌上马儿性命的一战即将开始!\n"
             f"> 赛马场位置:{query_of_player + 1}/{max_player}")

events_list = load_dlcs()

async def RaceStart(bot:Bot, event:GroupMessageEvent):
    """
    赛马开始
    """
    global current_games
    group_id = event.group_id
    if group_id not in current_games or (session := current_games[event.group_id]).info["game"] != "horse race":
        return "赛马活动未开始，请输入【赛马创建】创建赛马场"
    race:race_group = session.info["race_group"]
    global events_list
    if (player_count := race.query_of_player()) == 0:
        return
    if race.start == 1:
        return
    if race.start == 0 or race.start == 2:
        if player_count >= min_player:
            race.start = 1
        else:
            return f"开始失败！赛马开局需要最少{min_player}人参与"
    session.time = time.time() + 180
    await bot.send(event,(f'> 比赛开始\n'
                          f'> 当前奖金：{session.gold * player_count}金币'))
    await asyncio.sleep(0.5)

    while race.start == 1:
        # 回合数+1
        race.round_add()
        #移除超时buff
        race.del_buff_overtime()
        #马儿全名计算
        race.fullname()
        #回合事件计算
        text = race.event_start(events_list)
        #马儿移动
        race.move()
        #场地显示
        display = race.display()
        
        output = text_to_png(display,20)

        try:
            await bot.send(event,(Message(text) + MessageSegment.image(output)))
        except:
            text = ""
            try:
                await bot.send(event,(MessageSegment.image(output)))
            except:
                pass

        await asyncio.sleep(0.5 + int(0.06 * len(text)))
            
        #全员失败计算
        if race.is_die_all():
            for x in race.player:
                uid = x.playeruid
                if uid in user_data:
                    user = user_data[uid]
                    user.gold += session.gold
                    user.group_accounts[group_id].gold += session.gold

            del current_games[group_id]
            return "比赛已结束，鉴定为无马生还"

        #全员胜利计算
        winer = race.is_win_all()
        winer_list="\n"
        if winer != []:
            await bot.send(event,(f'> 比赛结束\n'
                                  f'> {bot_name}正在为您生成战报...'))
            await asyncio.sleep(1)
            gold = int(session.gold * player_count / len(winer))
            for x in winer:
                uid = x[1]
                winer_list += "> "+ x[0] + "\n"
                if uid in user_data:
                    user = user_data[uid]
                    user.gold += gold
                    user.group_accounts[group_id].gold += gold
            del current_games[group_id]
            return (f"> 比赛已结束，胜者为：{winer_list}"
                    f"> 本次奖金：{gold} 金币")
        await asyncio.sleep(1)

def RaceReStart(event:GroupMessageEvent):
    """
    赛马重置
    """
    global current_games
    group_id = event.group_id
    session = current_games[group_id]

    overtime = time.time() - session.time + 180
    if overtime < 180:
        return f"当前赛马已创建 {int(overtime)} 秒，未超时。"
    race:race_group = session.info["race_group"]
    for x in race.player:
        uid = x.playeruid
        if uid in user_data:
            user = user_data[uid]
            user.gold += session.gold
            user.group_accounts[group_id].gold += session.gold

    del current_games[group_id]
    return "赛马场已重置。"

"""+++++++++++++++++
——————————
     其他小游戏
——————————
+++++++++++++++++"""

def slot(event:MessageEvent, gold:int):
    """
    幸运花色
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    if gold > max_bet_gold:
        return f'幸运花色每次最多{max_bet_gold}金币。'
    if gold > group_account.gold:
        return f'你没有足够的金币，你的金币：{user_data["group_account.gold:"]}。'
    suit = {1:"♤",2:"♡",3:"♧",4:"♢"}
    x = random.randint(1,4)
    y = random.randint(1,4)
    z = random.randint(1,4)
    res = f"\n| {suit[x]} | {suit[y]} | {suit[z]} |\n"
    l = len(set([x,y,z]))
    if l == 1:
        gold = gold * 7
        msg =("你抽到的花色为：" +
              res +
              f"恭喜你获得了{gold}金币，祝你好运~")
    elif l == 2:
        gold = 0
        msg =("你抽到的花色为：" +
              res +
              "祝你好运~")
    else:
        gold = -gold
        msg =("你抽到的花色为：" +
              res +
              f"你失去了{-gold}金币 ，祝你好运~")
    user.gold += gold
    group_account.gold += gold
    return msg

"""+++++++++++++++++
——————————
      对战系统
——————————
+++++++++++++++++"""

class Session(BaseModel):
    """
    群内进行的游戏
    """
    time:float = 0.0
    player1_id:int = None
    player2_id:int = None
    at:int = None
    round = 0
    next:int = None
    win:int = None
    gold:int = 0
    info:dict = {}
    def create(self, event:GroupMessageEvent):
        """
        创建游戏
        """
        self.__init__(
            time = time.time(),
            player1_id = event.user_id,
            at = int(get_message_at(event.message)[0]) if get_message_at(event.message) else None
            )

    def create_check(self, event:GroupMessageEvent):
        """
        检查是否可以根据event创建游戏
        如果不能创建则返回提示
        如果可以创建则返回None
        """
        overtime = time.time() - self.time
        if overtime > 60:
            return None
        user_id = event.user_id
        if player1_id := self.player1_id:
            if player1_id == user_id:
                return "你已发起了一场对决"
            if player2_id := self.player2_id:
                if player2_id == user_id:
                    return "你正在进行一场对决"
                else:
                    player1_name = user_data[player1_id].group_accounts[event.group_id].nickname
                    player2_name = user_data[player2_id].group_accounts[event.group_id].nickname
                    return f"{player1_name} 与 {player2_name} 的对决还未结束！"
            else:
                if overtime > 30:
                    return None
                else:
                    return f'现在是 {user_data[player1_id].group_accounts[event.group_id].nickname} 发起的对决，请等待比赛结束后再开始下一轮...'

    def try_create_game(self, event:GroupMessageEvent):
        """
        根据event创建游戏
        如果创建失败则返回提示
        如果创建成功则返回None
        """
        if msg := self.create_check(event):
            return msg
        else:
            self.create(event)
    def try_join_game(self, event:GroupMessageEvent):
        """
        根据event加入游戏
        如果加入失败则返回提示
        如果加入成功则返回None
        """
        if time.time() - self.time > 60:
            return "这场对决邀请已经过时了，请重新发起决斗..."
        user_id = event.user_id
        if self.player1_id and self.player1_id != user_id and not self.next:
            if not self.at or self.at == user_id: 
                self.time = time.time()
                self.player2_id = user_id
            else:
                return f'现在是 {user_data[self.player1_id].group_accounts[event.group_id].nickname} 发起的对决，请等待比赛结束后再开始下一轮...'
        else:
            return " "
    def nextround(self):
        """
        把session状态切换到下一回合
        """
        self.time = time.time()
        self.round += 1
        self.next = self.player1_id if self.next == self.player2_id else self.player2_id
    def shot_check(self, event:GroupMessageEvent):
        """
        开枪前检查游戏是否合法
        如果不合法则返回提示
        如果合法则返回None
        """
        if time.time() - self.time > 60:
            return "这场对决邀请已经过时了，请重新发起决斗..."
        user_id = event.user_id
        if not self.player1_id:
            return " "
        if not self.player2_id:
            if self.player1_id == user_id:
                return "目前无人接受挑战哦"
            else:
                return "请这位勇士先接受挑战"
        if user_id == self.player1_id or user_id == self.player2_id:
            if user_id == self.next:
                return None
            else:
                return f"现在是{user_data[self.next].group_accounts[event.group_id].nickname}的回合"
        else:
            player1_name = user_data[self.player1_id].group_accounts[event.group_id].nickname
            player2_name = user_data[self.player2_id].group_accounts[event.group_id].nickname
            return f"{player1_name} v.s. {player2_name}\n正在进行中..."

current_games:Dict[int,Session] = {}

def accept(event:GroupMessageEvent):
    """
    接受挑战
    """
    group_id = event.group_id
    global current_games
    session = current_games[group_id]
    if msg := session.try_join_game(event):
        return None if msg == " " else msg
    group_account = Manager.locate_user(event)[1]
    if session.info["game"] == "random":
        session.gold = random.randint(0, 0 if(mingold := min(group_account.gold,session.info["gold"])) < 0 else mingold) if session.gold == -1 else session.gold
        game = random.choice(["russian","dice","lucky_number","cantrell", "Blackjack"])
        if game == "russian":
            session.info = russian_info(random.randint(1,6))
        elif game == "dice":
            session.info = dice_info(session.gold)
        elif game == "poker":
            session.info = poker_info()
        elif game == "lucky_number":
            session.info = lucky_number_info(session.gold)
        elif game == "cantrell":
            session.info = cantrell_info(session.gold)
        elif game == "Blackjack":
            session.info = Blackjack_info()
    elif group_account.gold <  session.gold:
        del current_games[group_id]
        return Message(MessageSegment.at(event.user_id) + f"你的金币不足以接受这场对决！\n——你还有{group_account.gold}枚金币。")

    bet_limit = min(
        user_data[session.player1_id].group_accounts[group_id].gold,
        user_data[session.player2_id].group_accounts[group_id].gold)
    bet_limit = bet_limit if bet_limit > 0 else 0
    session.info["bet_limit"] = bet_limit
    session.next = session.player1_id
    return acceptmessage(session)

def acceptmessage(session:Session):
    """
    生成接受挑战的提示信息
    """
    game = session.info.get("game")
    gold = session.gold
    if game == "russian":
        tip1 = "本场对决为【俄罗斯轮盘】\n"
        tip2 = "开枪！"
    elif game == "dice":
        gold = session.info["max_gold"]
        tip1 = "本场对决为【掷色子】\n"
        tip2 = "开数！"
    elif game == "poker":
        tip1 = "本场对决为【扑克对战】\n"
        tip2 = "加注！\n"
        tip2 += MessageSegment.image(text_to_png(
            "P1初始状态\n"
            f'HP {session.info["P1"]["HP"]} SP {session.info["P1"]["SP"]} DEF {session.info["P1"]["DEF"]}\n'
            "——————————————\n"
            "P2初始状态\n"
            f'HP {session.info["P2"]["HP"]} SP {session.info["P2"]["SP"]} DEF {session.info["P2"]["DEF"]}\n'
            "——————————————\n"
            "P1初始手牌\n" + 
            "".join([f'【{pokerACT.suit[suit]}{pokerACT.point[point]}】' for suit, point in session.info["P1"]["hand"]])
            ),30)
    elif game == "lucky_number":
        tip1 = "本场对决为【猜数字】\n"
        tip2 = "发送数字"
    elif game == "cantrell":
        tip1 = "本场对决为【港式五张】\n"
        tip2 = "开牌！\n"
        tip2 += MessageSegment.image(text_to_png(
                "P1初始手牌：\n"
                "|"
                + "".join([f'{cantrell_suit[suit]}{cantrell_point[point]}|' for suit, point in session.info["hand1"][0:3]]) +
                "   |   |"
                "\n——————————————\n"
                'P2初始手牌\n'
                "|"
                + "".join([f'{cantrell_suit[suit]}{cantrell_point[point]}|' for suit, point in session.info["hand2"][0:3]]) +
                "   |   |"
                ),30)
    elif game == "Blackjack":
        hand1 = session.info["hand1"][0]
        hand2 = session.info["hand2"][0]
        tip1 = "本场对决为【21点】\n"
        tip2 = "\n抽牌|停牌|双倍下注\n"
        tip2 += (
            f"P1：{Blackjack_suit[hand1[0]]}{Blackjack_point[hand1[1]]}\n"
            f"P2：{Blackjack_suit[hand2[0]]}{Blackjack_point[hand2[1]]}")
    else:
        tip1 = ""
        tip2 = ""
    return Message(
        f"{MessageSegment.at(session.player2_id)}接受了对决！\n" +
        tip1 +
        f"赌注为 {gold} 金币\n" +
        f"请{MessageSegment.at(session.player1_id)}{tip2}"
        )

def refuse(event:GroupMessageEvent):
    """
    拒绝挑战
    """
    global current_games
    group_id = event.group_id
    session = current_games[group_id]
    if time.time() - session.time > 60:
        del current_games[group_id]
        return None
    if session.at == event.user_id:
        if session.player2_id:
            return "对决已开始，拒绝失败。"
        else:
            del current_games[group_id]
            return "拒绝成功，对决已结束。"

async def overtime(bot:Bot, event:GroupMessageEvent):
    """
    超时结算
    """
    global current_games
    session = current_games[event.group_id]
    if (time.time() - session.time > 30 and
        session.player1_id and
        session.player2_id):
        await end(bot, event)

async def fold(bot:Bot, event:GroupMessageEvent):
    """
    认输
    """
    global current_games
    session = current_games[event.group_id]
    user_id = event.user_id
    if (time.time() - session.time < 60 and
        session.player1_id and
        session.player2_id and
        user_id == session.player1_id or user_id == session.player2_id):
        session.win = session.player1_id if user_id == session.player2_id else session.player2_id
        await end(bot, event)

def start(event:GroupMessageEvent, gold:int, max_bet_gold:int = max_bet_gold) -> Tuple[bool,Message]:
    """
    发起游戏
    """
    if gold > max_bet_gold:
        return  False, Message(MessageSegment.at(event.user_id) + f"对战金额不能超过{max_bet_gold}")
    group_account = Manager.locate_user(event)[1]
    if gold > group_account.gold:
        return  False, Message(MessageSegment.at(event.user_id) + f"你没有足够的金币支撑这场对决。\n——你还有{group_account.gold}枚金币。")

    global current_games
    group_id = event.group_id
    session = current_games.setdefault(group_id,Session())
    if msg := session.try_create_game(event):
        return False, msg

    if at := session.at:
        if at not in group_data[group_id].namelist:
            del current_games[group_id]
            return False, "没有对方的注册信息。"
        player1_name = user_data[session.player1_id].group_accounts[event.group_id].nickname
        player2_name = user_data[at].group_accounts[event.group_id].nickname
        msg = (f"{player1_name} 向 {player2_name} 发起挑战！\n"
               f"请 {player2_name} 回复 接受挑战 or 拒绝挑战\n"
               "【30秒内有效】")
    else:
        player1_name = user_data[session.player1_id].group_accounts[event.group_id].nickname
        msg = (f"{player1_name} 发起挑战！\n"
               "回复 接受挑战 即可开始对局。\n"
               "【30秒内有效】")
    session.round += 1
    return True, msg

"""+++++++++++++++++
——————————
     俄罗斯轮盘
——————————
+++++++++++++++++"""

def random_bullet(bullet_num:int):
    """
    随机子弹排列
        bullet_num:装填子弹数量
    """
    bullet_lst = [0, 0, 0, 0, 0, 0, 0]
    for i in random.sample([0, 1, 2, 3, 4, 5, 6], bullet_num):
        bullet_lst[i] = 1
    return bullet_lst

def russian_info(bullet_num):
    """
    生成俄罗斯轮盘游戏内容
    """
    return {
        "game":"russian",
        "bullet_num":bullet_num,
        "bullet":random_bullet(bullet_num),
        "index":0
        }

def russian(event:GroupMessageEvent, bullet_num:int, gold:int):
    """
    发起游戏：俄罗斯轮盘
        bullet_num:装填子弹数量
    """
    flag, msg = start(event, gold)
    if flag == False:
        return msg
    session = current_games[event.group_id]
    session.gold = gold
    session.info = russian_info(bullet_num)
    return (("咔 " * bullet_num)[:-1] + "，装填完毕\n"
            f"挑战金额：{gold}\n"
            f"第一枪的概率为：{round(bullet_num / 7.0 * 100,2)}%\n"
            f"{msg}")

async def russian_shot(bot:Bot, event:GroupMessageEvent, count:int):
    """
    开枪！！！
    """
    global current_games
    session = current_games[event.group_id]
    if msg := session.shot_check(event):
        return None if msg == " " else msg
    index = session.info["index"]
    MAG = session.info["bullet"][index:]
    count = len(MAG) if count < 1 else count
    msg = f"连开{count}枪！\n" if count > 1 else ""
    if 1 in MAG[:count]:
        session.win = session.player1_id if event.user_id == session.player2_id else session.player2_id
        await bot.send(event,(
            MessageSegment.at(event.user_id) + msg +
            random.choice(["嘭！，你直接去世了","眼前一黑，你直接穿越到了异世界...(死亡)","终究还是你先走一步..."]) +
            f"\n第 {index + MAG.index(1) + 1} 发子弹送走了你..."
            ))
        await end(bot, event)
    else:
        session.nextround()
        session.info["index"] += count
        next_name = user_data[session.next].group_accounts[event.group_id].nickname
        await bot.send(event,msg + (
            random.choice(["呼呼，没有爆裂的声响，你活了下来",
                           "虽然黑洞洞的枪口很恐怖，但好在没有子弹射出来，你活下来了",
                           f'{"咔 "*count}，看来运气不错，你活了下来']) +
            f"\n下一枪中弹的概率：{round(session.info['bullet_num'] * 100 / (len(MAG) - count),2)}%\n"
            f"轮到 {next_name}了"
            ))

"""+++++++++++++++++
——————————
       掷色子
——————————
+++++++++++++++++"""

def dice_pt(dice_array:list) -> int:
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

def dice_pt_analyses(pt:int) -> str:
    """
    分析骰子pt
    """
    array_type = ""
    if (yiman := int(pt/10000000)) > 0:
        pt -= yiman * 10000000
        array_type += f"役满 {yiman} + "
    if (chuan := int(pt/1000000)) > 0:
        pt -= chuan * 1000000
        array_type += f"串 {chuan} + "
    if (tiao := int(pt/100000)) > 0:
        pt -= tiao * 100000
        array_type += f"条 {tiao} + "
    if (dui := int(pt/10000)) > 0:
        if dui == 1:
            pt -= 10000
            dui = int(pt/100)
            array_type += f"对 {dui} + "
        else:
            pt -= 20000
            dui = int(pt/100)
            array_type += f"两对 {dui} + "
        pt -= dui * 100
    if pt>0:
        array_type += f"散 {pt} + "
    return array_type[:-3]

def dice_list(dice_array:list) -> str:
    """
    把骰子列表转成字符串
    """
    lst_dict = {0:"〇",1:"１",2:"２",3:"３",4:"４",5:"５",6:"６",7:"７",8:"８",9:"９"}
    return " ".join(lst_dict[x] for x in dice_array)

def dice_info(gold):
    """
    生成掷色子游戏内容
    """
    return {
        "game":"dice",
        "max_gold":gold,
        "dice_array1":[random.randint(1,6) for i in range(5)],
        "dice_array2":[random.randint(1,6) for i in range(5)],
        }

def dice(event:GroupMessageEvent, gold:int):
    """
    发起游戏：掷色子
    """
    flag, msg = start(event, gold, max_bet_gold * 10)
    if flag == False:
        return msg
    session = current_games[event.group_id]
    session.gold = int(gold/10)
    session.info = dice_info(gold)
    return ("哗啦哗啦~，骰子准备完毕\n"
            f"挑战金额：{gold}\n"
            f"{msg}")

async def dice_open(bot:Bot, event:GroupMessageEvent):
    """
    开数！！！
    """
    group_id = event.group_id
    global current_games
    session = current_games[group_id]
    if msg := session.shot_check(event):
        return None if msg == " " else msg

    session.gold = int(session.info["max_gold"] * session.round/10)

    player1_id = session.player1_id
    player2_id = session.player2_id

    dice_array1 = (session.info["dice_array1"][:int(session.round/2+0.5)] + [0, 0, 0, 0, 0])[:5]
    dice_array2 = (session.info["dice_array2"][:int(session.round/2)] + [0, 0, 0, 0, 0])[:5]
    
    dice_array1.sort(reverse=True)
    dice_array2.sort(reverse=True)

    pt1 = dice_pt(dice_array1)
    pt2 = dice_pt(dice_array2)

    session.win = player1_id if pt1 > pt2 else player2_id
    session.nextround()

    next_name = "结算" if session.round > 10 else user_data[session.next].group_accounts[group_id].nickname
    msg = (
        f'玩家：{user_data[player1_id].group_accounts[group_id].nickname}\n'
        f"组合：{dice_list(dice_array1)}\n"
        f"点数：{dice_pt_analyses(pt1)}\n"
        "———————————\n"
        f'玩家：{user_data[player2_id].group_accounts[group_id].nickname}\n'
        f"组合：{dice_list(dice_array2)}\n"
        f"点数：{dice_pt_analyses(pt2)}\n"
        "———————————\n"
        f"结算金额：{session.gold}\n"
        f'领先：{user_data[session.win].group_accounts[group_id].nickname}\n'
        f'下一回合：{next_name}'
        )
    await bot.send(event,message = MessageSegment.image(text_to_png(msg,30)))
    if session.round > 10:
        await end(bot, event)

"""+++++++++++++++++
——————————
      扑克对战
——————————
+++++++++++++++++"""

def random_poker():
    """
    生成随机牌库
    """
    poker_deck = [[i,j] for i in range(1,5) for j in range(1,14)]
    random.shuffle(poker_deck)
    return poker_deck

def poker_info():
    """
    生成扑克对战游戏内容
    """
    deck = random_poker()
    hand = deck[0:3].copy()
    del deck[0:3]
    return {
        "game":"poker",
        "deck":deck + [[0,0],[0,0],[0,0],[0,0]],
        "ACT":1,
        "P1":{"hand":hand,"HP":20,"ATK":0,"DEF":0,"SP":0},
        "P2":{"hand":[],"HP":25,"ATK":0,"DEF":0,"SP":2}
        }

def poker(event:GroupMessageEvent, gold:int):
    """
    发起游戏：扑克对战
    """
    flag, msg = start(event, gold)
    if flag == False:
        return msg
    session = current_games[event.group_id]
    session.gold = gold
    session.info = poker_info()
    return ("唰唰~，随机牌库已生成\n"
            f"挑战金额：{gold}\n"
            f"{msg}")

class pokerACT():
    suit = {0:"结束",1:"防御",2:"恢复",3:"技能",4:"攻击"}
    point = {0:"0",1:"A",2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",10:"10",11:"11",12:"12",13:"13"}
    @classmethod
    def action_ACE(cls, Active:dict, roll:int = 1) -> str:
        '''
        手牌全部作为技能牌（ACE技能）
            Active:行动牌生效对象
        '''
        card_msg = "技能牌为"
        skill_msg = "\n"
        for card in Active["hand"]:
            suit = card[0]
            point = roll if card[1] == 1 else card[1]
            card_msg += f'【{cls.suit[suit]} {cls.point[point]}】'
            if suit == 1:
                Active["DEF"] += point
                skill_msg += f'♤防御力强化了 {point}\n'
            elif suit == 2:
                Active["HP"] += point
                skill_msg += f'♡生命值增加了 {point}\n'
            elif suit == 3:
                Active["SP"] += point + point
                skill_msg += f'♧技能点增加了 {point}\n'
            elif suit == 4:
                Active["ATK"] += point
                skill_msg += f'♢发动了攻击 {point}\n'
            else:
                return "出现未知错误"
            Active["SP"] -= point
            Active["SP"] = 0 if Active["SP"] < 0 else Active["SP"]
        return card_msg + skill_msg[:-1]
    @classmethod
    def action(cls, index:int, Active:dict) -> str:
        '''
        行动牌生效
            index:手牌序号
            Active:行动牌生效对象
        '''
        card = Active["hand"][index]
        suit = card[0]
        point = card[1]
        if point == 1:
            roll = random.randint(1,6)
            msg = f'发动ACE技能！六面骰子判定为 {roll}\n'
            msg += cls.action_ACE(Active, roll)
        else:
            if suit == 1:
                Active["ATK"] += point
                msg = f"♤发动了攻击{point}"
            elif suit == 2:
                Active["HP"] += point
                msg = f"♡生命值增加了{point}"
            elif suit == 3:
                Active["SP"] += point
                msg = f"♧技能点增加了{point}...\n"
                roll = random.randint(1,20)
                if Active["SP"] < roll:
                    msg += f'二十面骰判定为{roll}点，当前技能点{Active["SP"]}\n技能发动失败...'
                else:
                    del Active["hand"][index]
                    msg += f'二十面骰判定为{roll}点，当前技能点{Active["SP"]}\n技能发动成功！\n'
                    msg += cls.action_ACE(Active)
            elif suit == 4:
                Active["ATK"] = point
                msg = f"♢发动了攻击{point}"
            else:
                msg = "出现未知错误"
        return msg
    @classmethod
    def skill(cls, card:list, Player:dict) -> str:
        '''
        技能牌生效
            card:技能牌
            Player:技能牌生效对象
        '''
        suit = card[0]
        point = card[1]
        msg = f'技能牌为【{cls.suit[suit]} {cls.point[point]}】\n'
        if suit == 1:
            Player["DEF"] += point
            msg += f"♤发动了防御 {point}"
        elif suit == 2:
            Player["HP"] += point
            msg += f"♡生命值增加了 {point}"
        elif suit == 3:
            Player["SP"] += point + point
            msg += f"♧技能点增加了 {point}"
        elif suit == 4:
            Player["ATK"] += point
            msg += f"♢发动了反击 {point}"
        else:
            msg += "启动结算程序"
        Player["SP"] -= point
        Player["SP"] = 0 if Player["SP"] < 0 else Player["SP"]
        return msg

async def poker_play(bot:Bot, event:GroupMessageEvent, index:str):
    """
    出牌
    """
    group_id = event.group_id
    global current_games
    session = current_games[group_id]
    if session.info["ACT"] == 0:
        return
    if msg := session.shot_check(event):
        return None if msg == " " else msg
    if index not in ["1","2","3"]:
        return "请发送【出牌 1/2/3】打出你的手牌。"

    session.info["ACT"] = 0
    session.nextround()

    deck = session.info["deck"]

    if event.user_id == session.player1_id:
        Active = session.info["P1"]
        Passive = session.info["P2"]
    else:
        Active = session.info["P2"]
        Passive = session.info["P1"]  
        
    # 出牌判定
    msg = pokerACT.action(int(index) - 1,Active)
    try:
        await bot.send(event,message = msg,at_sender=True)
    except:
        await bot.send(event,message = MessageSegment.image(text_to_png(msg,30)))

    await asyncio.sleep(0.03*len(msg))

    # 敌方技能判定
    next_name = user_data[session.next].group_accounts[group_id].nickname
    if Passive["SP"] > 0:
        roll = random.randint(1,20)
        if  Passive["SP"] < roll:
            msg = f'{next_name} 二十面骰判定为{roll}点，当前技能点{Passive["SP"]}\n技能发动失败...'
        else:
            msg = f'{next_name} 二十面骰判定为{roll}点，当前技能点{Passive["SP"]}\n技能发动成功！\n'
            msg += pokerACT.skill(deck[0], Passive)
            del deck[0]

        try:
            await bot.send(event,message = msg)
        except:
            await bot.send(event,message = MessageSegment.image(text_to_png(msg,30)))

    # 回合结算
    Active["HP"] += Active["DEF"] - Active["ATK"] if Active["DEF"] < Passive["ATK"] else 0
    Passive["HP"] += Passive["DEF"] - Active["ATK"] if Passive["DEF"] < Active["ATK"] else 0

    Active["ATK"] = 0
    Passive["ATK"] = 0

    # 防御力强化保留一回合
    Passive["DEF"] = 0 

    # 下回合准备
    hand = deck[0:3].copy()
    Passive["hand"] = hand
    del deck[0:3]

    next_name = "游戏结束" if Active["HP"] < 1 or Passive["HP"] < 1 or Passive["HP"] >= 40 or [0,0] in hand else next_name

    msg = (
        f'玩家：{user_data[session.player1_id].group_accounts[group_id].nickname}\n'
        "状态：\n"
        f'HP {session.info["P1"]["HP"]} SP {session.info["P1"]["SP"]} DEF {session.info["P1"]["DEF"]}\n'
        "——————————————\n"
        f'玩家：{user_data[session.player2_id].group_accounts[group_id].nickname}\n'
        "状态：\n"
        f'HP {session.info["P2"]["HP"]} SP {session.info["P2"]["SP"]} DEF {session.info["P2"]["DEF"]}\n'
        "——————————————\n"
        f'当前回合：{next_name}\n'
        "手牌：\n" + 
        "".join([f'【{pokerACT.suit[suit]}{pokerACT.point[point]}】' for suit, point in Passive["hand"]])
        )
    await asyncio.sleep(0.5)
    await bot.send(event, message = MessageSegment.image(text_to_png(msg,30)))

    if next_name == "游戏结束":
        Passive["HP"] = Passive["HP"] + 100 if Passive["HP"] >= 40 else Passive["HP"]
        session.win = session.player1_id if session.info["P1"]["HP"] > session.info["P2"]["HP"] else session.player2_id
        await end(bot, event)
    else:
        session.info["ACT"] = 1

"""+++++++++++++++++
——————————
      猜数字
——————————
+++++++++++++++++"""

def lucky_number_info(gold):
    """
    生成猜数字游戏内容
    """
    return {
        "game":"lucky_number",
        "gold":gold,
        "number":random.randint(1,100),
        }

def lucky_number(event:GroupMessageEvent, gold:int):
    """
    发起游戏：猜数字
    """
    flag, msg = start(event, gold)
    if flag == False:
        return msg
    session = current_games[event.group_id]
    session.gold = gold
    session.info = lucky_number_info(gold)
    return (f"随机 1-100 数字已生成。"
            f"挑战金额：{gold}/次\n"
            f"{msg}")

async def guess_number(bot:Bot, event:GroupMessageEvent, N:int):
    """
    猜数字
    """
    group_id = event.group_id
    global current_games
    session = current_games[group_id]
    if msg := session.shot_check(event):
        return None if msg == " " else msg
    session.gold = min(session.info["gold"] * session.round, session.info["bet_limit"])
    session.nextround()
    TrueN = session.info["number"]
    if N > TrueN:
        return f"{N}比这个数字大\n金额：{session.gold}"
    if N < TrueN:
        return f"{N}比这个数字小\n金额：{session.gold}"
    session.win = event.user_id
    await end(bot, event)

"""+++++++++++++++++
——————————
       梭哈
——————————
+++++++++++++++++"""

cantrell_suit = {4:"♠",3:"♥",2:"♣",1:"♦"}
cantrell_point = {1:"2",2:"3",3:"4",4:"5",5:"6",6:"7",7:"8",8:"9",9:"10",10:"J",11:"Q",12:"K",13:"A"}

def is_straight(points):
    """
    判断是否为顺子
    """
    points = sorted(points)
    for i in range(1, len(points)):
        if points[i] - points[i-1] != 1:
            return False
    return True

def cantrell_pt(hand:list) -> Tuple[int,str]:
    """
    牌型点数
    """
    pt = 0
    name = ""

    suits = [x[0] for x in hand]
    points = [x[1] for x in hand]

    setpoints = set(points)

    # 判断同花
    if len(set(suits)) == 1:
        pt += suits[0]
        if is_straight(points):
            point = max(points)
            pt += point * (100**9)
            name += f"同花顺 {cantrell_suit[suits[0]]}{cantrell_point[point]} "
        else:
            point = sum(points)
            pt += point * (100**6)
            name += f"同花 {cantrell_suit[suits[0]]}{point + 5} "
    else:
        pt += sum(suits)
        # 判断顺子
        if is_straight(points):
            point = max(points)
            pt += point * (100**5)
            name += f"顺子 {cantrell_point[point]} "
        else:
            # 判断四条或葫芦
            if len(setpoints) == 2:
                for point in setpoints:
                    if points.count(point) == 4:
                        pt += point * (100**8)
                        name += f"四条 {cantrell_point[point]} "
                    if points.count(point) == 3:
                        pt += point * (100**7)
                        name += f"葫芦 {cantrell_point[point]} "
            else:
                # 判断三条，两对，一对
                exp = 1
                tmp = 0
                for point in setpoints:
                    if points.count(point) == 3:
                        pt += point * (100**4)
                        name += f"三条 {cantrell_point[point]} "
                        break
                    if points.count(point) == 2:
                        exp += 1
                        tmp += point
                        name += f"对{cantrell_point[point]} "
                else:
                    pt += tmp * (100**exp)

            tmp = 0
            for point in setpoints:
                if points.count(point) == 1:
                    pt += point * (100)
                    tmp += point + 1
            if tmp:
                name += f"散{tmp} "

    return pt,name[:-1]

def max_hand(hands) -> Tuple[list,Tuple[int,str]]:
    """
    返回一组牌中最大的牌
    """
    max_pt = 0
    for hand in hands:
        result = cantrell_pt(hand)
        if result[0] > max_pt:
            max_pt = result[0]
            max_name = result[1]
            max_hand = hand
    return max_hand,(max_pt,max_name)

def cantrell_info(gold):
    """
    生成港式五张游戏内容
    """
    deck = random_poker()
    return {
        "game":"cantrell",
        "round_gold":gold,
        "hand1":deck[0:5],
        "pt1":cantrell_pt(deck[0:5]),
        "hand2":deck[5:10],
        "pt2":cantrell_pt(deck[5:10])
        }

def happy_cantrell_info(gold, level = 2):
    """
    生成快乐港式五张游戏内容
        level:抽牌次数，1次到5次。
    """
    deck = random_poker()
    deck = [deck[i:i+5] for i in range(0, 50, 5)]

    hand1,pt1 = max_hand(deck[0:level])
    hand2,pt2 = max_hand(deck[level:2*level])

    return {
        "game":"cantrell",
        "round_gold":gold,
        "hand1":hand1,
        "pt1":pt1,
        "hand2":hand2,
        "pt2":pt2
        }

def cantrell(event:GroupMessageEvent, gold:int ,level:int = 1):
    """
    发起游戏：港式五张
    """
    flag, msg = start(event, gold, max_bet_gold * 10)
    if flag == False:
        return msg
    group_id = event.group_id
    session = current_games[group_id]
    session.gold = gold
    if level == 1:
        session.info = cantrell_info(gold)
    else:
        level = 1 if level < 1 else level
        level = 5 if level > 5 else level
        session.info = happy_cantrell_info(gold,level)
    return (f"随机牌堆已生成\n"
            f"开局金额：{gold}\n"
            + (f"等级：Lv.{level}\n" if level > 1 else "") +
            f"{msg}")

async def cantrell_check(bot:Bot, event:GroupMessageEvent):
    """
    看牌
    """
    group_id = event.group_id
    global current_games
    session = current_games[group_id]
    if msg := session.shot_check(event):
        return None if msg == " " else msg
    session.time = time.time() + 120
    expose = int(round((session.round  + 0.5)/ 2)) + 3
    expose = min(expose,5)
    if event.user_id == session.player1_id:
        hand = "hand1"
    else:
        hand = "hand2"
    msg = (
        "你的手牌：\n"
        + ("|" + "".join([f'{cantrell_suit[suit]}{cantrell_point[point]}|' for suit, point in session.info[hand][0:expose]]) + (5 - expose)*"   |")
        )
    if not await try_send_private_msg(user_id = event.user_id, message = MessageSegment.image(text_to_png(msg,30))):
        await bot.send(event,f"私聊发送失败，请检查是否添加{bot_name}为好友。\n游戏继续！")

async def cantrell_play(bot:Bot, event:GroupMessageEvent, gold:int, max_bet_gold:int = max_bet_gold * 10):
    """
    加注
    """
    group_id = event.group_id
    global current_games
    session = current_games[group_id]
    if msg := session.shot_check(event):
        return None if msg == " " else msg
    if gold > max_bet_gold:
        return MessageSegment.at(event.user_id) + f"加注金额不能超过{max_bet_gold}"
    if session.gold + gold > session.info["bet_limit"]:
        gold = session.info["bet_limit"] - session.gold
    expose = session.round / 2
    if expose == int(expose):
        session.nextround()
        session.time += 120
        expose = int(expose) + 3
        gold = max(gold,session.info["round_gold"])
        session.gold += gold
        msg = (
            f'玩家：{user_data[session.player1_id].group_accounts[group_id].nickname}\n'
            "手牌：\n"
            "|"
            + "".join([f'{cantrell_suit[suit]}{cantrell_point[point]}|' for suit, point in session.info["hand1"][0:expose]]) + (5 - expose)*"   |"
            "\n——————————————\n"
            f'玩家：{user_data[session.player2_id].group_accounts[group_id].nickname}\n'
            "手牌：\n"
            "|"
            + "".join([f'{cantrell_suit[suit]}{cantrell_point[point]}|' for suit, point in session.info["hand2"][0:expose]]) + (5 - expose)*"   |"
            )
        if expose == 5:
            if session.info["pt1"][0] > session.info["pt2"][0]:
                session.win = session.player1_id
            else:
                session.win = session.player2_id
            await end(bot, event)
        else:
            return MessageSegment.image(text_to_png(f"您已跟注{gold}金币\n" + msg,30))
    else:
        session.nextround()
        session.time += 120
        session.info["round_gold"] = gold
        return MessageSegment.at(event.user_id) + f"您已加注{gold}金币"

"""+++++++++++++++++
——————————
        21点
——————————
+++++++++++++++++"""

Blackjack_suit = {4:"♠",3:"♥",2:"♣",1:"♦"}
Blackjack_point = {1:"A",2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",10:"10",11:"J",12:"Q",13:"K"}

def Blackjack_info():
    """
    生成21点游戏内容
    """
    deck = random_poker()
    return {
        "game":"Blackjack",
        "deck":deck[2:],
        "hand1":[deck[0],],
        "hand2":[deck[1],],
        }

def Blackjack(event:GroupMessageEvent, gold:int):
    """
    发起游戏：21点
    """
    flag, msg = start(event, gold, max_bet_gold * 10)
    if flag == False:
        return msg
    group_id = event.group_id
    session = current_games[group_id]
    session.gold = gold
    session.info = Blackjack_info()
    return ("唰唰~，随机牌库已生成\n"
            f"挑战金额：{gold}\n"
            f"{msg}")

def Blackjack_pt(hand:list) -> int:
    """
    返回21点牌组点数。
    """
    pts = [x[1] if x[1] < 10 else 10 for x in hand]
    pt = sum(pts)
    if 1 in pts and pt <= 11:
        pt += 10
    return pt

async def Blackjack_Hit(bot:Bot, event:GroupMessageEvent):
    """
    抽牌
    """
    group_id = event.group_id
    global current_games
    session = current_games[group_id]
    if msg := session.shot_check(event):
        return None if msg == " " else msg
    session.time = time.time()

    if event.user_id == session.player1_id:
        hand = "hand1"
        session.win = session.player2_id
    else:
        hand = "hand2"
        session.win = session.player1_id
    deck = session.info["deck"]
    card = deck[0]
    del deck[0]
    hand = session.info[hand]
    hand.append(card)
    pt = Blackjack_pt(hand)
    if pt > 21:
        await end(bot, event)
    else:
        msg = (
            "你的手牌：\n"
            + ("|" + "".join([f'{Blackjack_suit[suit]}{Blackjack_point[point]}|' for suit, point in hand]))
            + f'\n合计:{pt}点'
            )
        if not await try_send_private_msg(user_id = event.user_id, message = MessageSegment.image(text_to_png(msg,30))):
            await bot.send(event,f"私聊发送失败，请检查是否添加{bot_name}为好友。\n游戏继续！")

async def Blackjack_stand(bot:Bot, event:GroupMessageEvent):
    """
    停牌
    """
    group_id = event.group_id
    global current_games
    session = current_games[group_id]
    if msg := session.shot_check(event):
        return None if msg == " " else msg
    session.time = time.time()
    session.nextround()
    if session.round == 2:
        return Message(f"请{MessageSegment.at(session.player2_id)}\n抽牌|停牌|双倍下注")
    else:
        hand1 = session.info["hand1"]
        hand2 = session.info["hand2"]
        if Blackjack_pt(hand1) > Blackjack_pt(hand2):
            session.win = session.player1_id
        else:
            session.win = session.player2_id
        await end(bot, event)

async def Blackjack_DoubleDown(bot:Bot, event:GroupMessageEvent):
    """
    双倍下注
    """
    group_id = event.group_id
    global current_games
    session = current_games[group_id]
    if msg := session.shot_check(event):
        return None if msg == " " else msg
    session.time = time.time()
    gold = session.gold
    bet_limit = session.info["bet_limit"]
    gold = gold*2
    gold = min(bet_limit, gold)
    session.gold = gold
    if event.user_id == session.player1_id:
        hand = "hand1"
        session.win = session.player2_id
    else:
        hand = "hand2"
        session.win = session.player1_id
    deck = session.info["deck"]
    card = deck[0]
    del deck[0]
    hand = session.info[hand]
    hand.append(card)
    pt = Blackjack_pt(hand)
    if pt > 21:
        await end(bot, event)
    else:
        msg = (
            "你的手牌：\n"
            + ("|" + "".join([f'{Blackjack_suit[suit]}{Blackjack_point[point]}|' for suit, point in hand]))
            + f'\n合计:{pt}点'
            )
        if not await try_send_private_msg(user_id = event.user_id, message = MessageSegment.image(text_to_png(msg,30))):
            await bot.send(event,f"私聊发送失败，请检查是否添加{bot_name}为好友。\n游戏继续！")
        session.nextround()
        if session.round == 2:
            return Message(f"请{MessageSegment.at(session.player2_id)}\n抽牌|停牌|双倍下注")
        else:
            hand1 = session.info["hand1"]
            hand2 = session.info["hand2"]
            if Blackjack_pt(hand1) > Blackjack_pt(hand2):
                session.win = session.player1_id
            else:
                session.win = session.player2_id
            await end(bot, event)

"""+++++++++++++++++
——————————
      随机对战
——————————
+++++++++++++++++"""

def random_game(event:GroupMessageEvent, gold:int):
    """
    发起游戏：随机对战
    """
    group_account = Manager.locate_user(event)[1]
    if group_account.props.get("32002",0) < 1:
        return f"你未持有持有【{props_library['32002']['name']}】，无法发起随机对战。"
    flag, msg = start(event, gold)
    if flag == False:
        return msg
    session = current_games[event.group_id]
    session.gold = gold
    session.info = {
        "game":"random",
        "gold":group_account.gold if gold == -1 else gold
        }
    return ("随机对战已生成\n"
            f"挑战金额：{gold if gold > 0 else '随机'}\n"
            f"{msg}")

"""+++++++++++++++++
——————————
      游戏结束
——————————
+++++++++++++++++"""

def settle(group_id:int):
    """
    游戏结束结算
        return:结算界面
    """
    global current_games
    session = current_games[group_id]
    win = session.win if session.win else session.player1_id if session.next == session.player2_id else session.player2_id
    lose = session.player1_id if session.player2_id == win else session.player2_id
    winner = user_data[win]
    winner_group_account = winner.group_accounts[group_id]
    loser = user_data[lose]
    loser_group_account = loser.group_accounts[group_id]

    gold = session.gold
    if winner_group_account.props.get("42001",0) > 0:
        fee = 0
        fee_tip = f"『{props_library['42001']['name']}』免手续费"
    else:
        rand = random.randint(0, 5)
        fee = int(gold * rand / 100)
        fee_tip = f"手续费：{fee}({rand}%)"

    maxgold = int(max_bet_gold/5)

    if winner_group_account.props.get("52002",0) > 0:
        extra = int(gold *0.1)
        if extra < maxgold:
            extra_tip = f"◆『{props_library['52002']['name']}』\n"
        else:
            extra = maxgold
            extra_tip = f"◆『{props_library['52002']['name']}』最大奖励\n"
    else:
        extra_tip = ""
        extra = 0

    if gold == loser_group_account.gold and loser_group_account.security < 3:
        loser_group_account.security += 1
        security = random.randint(security_gold[0], security_gold[1])
        security_tip1 = "◇『金币补贴』\n"
        security_tip2 = f"◇已领取补贴：{security}\n"
    else:
        security = 0
        security_tip1 = ""
        security_tip2 = ""

    if loser_group_account.props.get("52001",0) > 0:
        off = int(gold * 0.1)
        if off < maxgold:
            off_tip = f"◇『{props_library['52001']['name']}』\n"
        else:
            off = maxgold
            off_tip = f"◇『{props_library['52001']['name']}』最大补贴\n"

    else:
        off = 0
        off_tip = ""

    win_gold = gold - fee + extra
    lose_gold = gold - off
    winner.win += 1
    winner.Achieve_win += 1
    winner.Achieve_lose = 0
    loser.lose += 1
    loser.Achieve_lose += 1
    loser.Achieve_win = 0
    msg = (
        f"结算：\n"
        "——————————————\n" +
        (tmp + "\n" if (tmp := "\n".join(x for x in Manager.Achieve_list((winner,winner_group_account)))) else "") +
        extra_tip +
        f"◆胜者：{winner_group_account.nickname}\n"
        f"◆结算：{winner_group_account.gold}（+{win_gold}）\n"
        f"◆战绩：{winner.win}:{winner.lose}\n"
        f"◆胜率：{round(winner.win * 100 / (winner.win + winner.lose), 2) if winner.win > 0 else 0}%\n"
        "——————————————\n" +
        (tmp + "\n" if (tmp := "\n".join(x for x in Manager.Achieve_list((loser,loser_group_account)))) else "") +
        security_tip1 +
        off_tip +
        f"◇败者：{loser_group_account.nickname}\n"
        f"◇结算：{loser_group_account.gold}（-{lose_gold}）\n" +
        security_tip2 +
        f"◇战绩：{loser.win}:{loser.lose}\n"
        f"◇胜率：{round(loser.win * 100 / (loser.win + loser.lose), 2) if loser.win > 0 else 0}%\n"
        "——————————————\n" + 
        fee_tip
        )
    winner.gold += win_gold
    winner_group_account.gold += win_gold
    loser.gold -= lose_gold - security
    loser_group_account.gold -= lose_gold - security
    res = game_str(session)
    del current_games[group_id]
    return f"这场对决是 {winner_group_account.nickname} 胜利了", msg, res

def game_str(session:Session):
    """
    结束附件
    """
    game = session.info["game"]
    if game == "russian":
        return " ".join(("—" if x == 0 else "|") for x in session.info["bullet"])
    if game == "dice":
        return (
            f'玩家 1\n'
            f'组合：{" ".join(str(x) for x in session.info["dice_array1"])}\n'
            f'玩家 2\n'
            f'组合：{" ".join(str(x) for x in session.info["dice_array2"])}')
    if game == "cantrell":
        return MessageSegment.image(text_to_png((
            "P1手牌：\n"
            "|" + "".join([f'{cantrell_suit[suit]}{cantrell_point[point]}|' for suit, point in session.info["hand1"]]) +
            f"\n牌型：\n{session.info['pt1'][1]}"
            "\n——————————————\n"
            "P2手牌：\n"
            "|" + "".join([f'{cantrell_suit[suit]}{cantrell_point[point]}|' for suit, point in session.info["hand2"]]) +
            f"\n牌型：\n{session.info['pt2'][1]}"),30))
    if game == "Blackjack":
        hand1 = session.info["hand1"]
        hand2 = session.info["hand2"]
        return MessageSegment.image(text_to_png((
            "P1手牌：\n"
            + ("|" + "".join([f'{Blackjack_suit[suit]}{Blackjack_point[point]}|' for suit, point in hand1]))
            + f'\n合计:{Blackjack_pt(hand1)}点'
            "\n——————————————\n"
            "P2手牌：\n"
            + ("|" + "".join([f'{Blackjack_suit[suit]}{Blackjack_point[point]}|' for suit, point in hand2]))
            + f'\n合计:{Blackjack_pt(hand2)}点'),30))
    else:
        return ""

async def end(bot:Bot, event:GroupMessageEvent):
    """
    输出结算界面
    """
    end_info = settle(event.group_id)
    tmp = MessageSegment.image(text_to_png(end_info[1]))
    await bot.send(event,end_info[0])
    await bot.send(event,tmp)
    await asyncio.sleep(0.5)
    await bot.send(event,end_info[2])