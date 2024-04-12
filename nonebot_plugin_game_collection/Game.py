from io import BytesIO
from typing import Tuple, Dict, Type
from abc import ABC, abstractmethod

import random
import time
import math
import asyncio

from .utils.chart import linecard_to_png
from .config import (
    bot_name,
    security_gold,
    bet_gold,
    max_bet_gold,
    max_player,
    min_player,
)

from .Exceptions import GameOverException
from .Processor import Event, Result, reg_command, reg_auto_event
from . import Manager
from . import Prop


class Session:
    """
    游戏场次信息
    """

    time: float = 0.0
    group_id: str = None
    at: str = None
    p1_uid: str = None
    p1_nickname: str = None
    p2_uid: str = None
    p2_nickname: str = None
    round = 0
    next: str = None
    win: str = None
    gold: str = 0
    bet_limit: int = 0

    def __init__(self, kwargs):
        self.time = time.time()
        self.group_id = kwargs["group_id"]
        self.at = kwargs["at"]
        self.p1_uid = kwargs["p1_uid"]
        self.p1_nickname = kwargs["p1_nickname"]
        if self.at:
            self.p2_uid = self.at
            self.p2_nickname = Manager.locate_user_at(self.p2_uid, self.group_id)[1].nickname
        self.gold = kwargs["gold"]

    def create_check(self, event: Event):
        """
        检查是否可以根据event创建对战场次
            如果不能创建则返回提示
            如果可以创建则返回None
        """
        overtime = time.time() - self.time
        if overtime > 60:
            return
        user_id = event.user_id
        p1_uid = self.p1_uid
        p2_uid = self.p2_uid
        if not p1_uid:
            return
        if p1_uid == user_id:
            if not p2_uid:
                return
            return "你已发起了一场对决"
        if not p2_uid:
            if overtime > 30:
                return
            return f"现在是 {self.p1_nickname} 发起的对决，请等待比赛结束后再开始下一轮..."
        if p2_uid == user_id:
            return "你正在进行一场对决"
        else:
            return f"{self.p1_nickname} 与 {self.p2_nickname} 的对决还未结束！"

    def try_join_game(self, event: Event):
        """
        根据event加入游戏
            如果加入失败则返回提示
            如果加入成功则返回None
        """
        if time.time() - self.time > 60:
            return "这场对决邀请已经过时了，请重新发起决斗..."
        user_id = event.user_id
        if self.p1_uid and self.p1_uid != user_id and not self.next:
            if not self.at or self.at == user_id:
                self.time = time.time()
                self.p2_uid = user_id
                self.p2_nickname = event.nickname
                return None
            else:
                return f"现在是 {self.p1_nickname} 发起的对决，请等待比赛结束后再开始下一轮..."
        else:
            return " "

    def leave(self):
        """
        玩家2离开游戏
        """
        self.time = time.time()
        self.p2_uid = None
        return None

    def nextround(self):
        """
        把session状态切换到下一回合
        """
        self.time = time.time()
        self.round += 1
        self.next = self.p1_uid if self.next == self.p2_uid else self.p2_uid

    def shot_check(self, user_id: str):
        """
        开枪前检查游戏是否合法
        如果不合法则返回提示
        如果合法则返回None
        """
        if time.time() - self.time > 60:
            return "这场对决邀请已经过时了，请重新发起决斗..."
        if not self.p1_uid:
            return " "
        if not self.p2_uid:
            if self.p1_uid == user_id:
                return "目前无人接受挑战哦"
            else:
                return "请这位勇士先接受挑战"
        if user_id == self.p1_uid or user_id == self.p2_uid:
            if user_id == self.next:
                return None
            else:
                return f"现在是{self.p1_nickname if self.next == self.p1_uid else self.p2_nickname}的回合"
        else:
            return f"{self.p1_nickname} v.s. {self.p2_nickname}\n正在进行中..."


class AROF(ABC):
    @abstractmethod
    def start(cls, event: Event) -> Result:
        """开始"""

    @abstractmethod
    def start_tips(self, msg):
        """游戏开始的提示"""

    def accept(self, *args):
        """接受挑战"""

    def refuse(self, *args):
        """拒绝挑战"""

    def overtime(self, *args):
        """超时结算"""

    def fold(self, *args):
        """认输"""

    def session_start(self, *args):
        """回合开始"""

    def session_end(self, *args):
        """回合结束"""

    def session_action(self, *args):
        """行动"""


class Game(AROF):
    """
    对战游戏类：
    需要定义的方法：
        action：游戏进行
        start_tips：游戏开始提示信息
        session_tips：场次提示信息
        end_tips：结束提示信息
    """

    name: str = "undefined"
    max_bet_gold: int = max_bet_gold

    def __init__(self, kwargs):
        self.gold: int = 0
        self.session: Session = Session(kwargs)

    @staticmethod
    def parse_arg(event: Event) -> dict:
        return {
            "at": at[0] if (at := event.at()) else None,
            "gold": event.args_to_int(bet_gold),
            "group_id": event.group_id,
            "p1_uid": event.user_id,
        }

    @classmethod
    def start(cls, event: Event) -> Result:
        """
        开始游戏，包含创建检查
        """
        kwargs = cls.parse_arg(event)
        gold = kwargs["gold"]
        limit = cls.max_bet_gold
        if gold > limit:
            return f"对战金币不能超过{limit}"
        user, group_account = Manager.locate_user(event)
        if gold > group_account.gold:
            return f"你没有足够的金币支撑这场对决。\n——你还有{group_account.gold}枚金币。"
        kwargs["p1_nickname"] = group_account.nickname
        group_id = event.group_id
        game = current_games.get(group_id)
        if game and (msg := game.session.create_check(event)):
            return msg
        game = current_games[group_id] = cls(kwargs)
        session = game.session
        if session.at:
            p2_nickname = session.p2_nickname or f"玩家{session.p2_uid[:4]}..."
            msg = f"{session.p1_nickname} 向 {p2_nickname} 发起挑战！\n" f"请 {p2_nickname} 回复 接受挑战 or 拒绝挑战\n" "【30秒内有效】"
        else:
            msg = f"{session.p1_nickname} 发起挑战！\n" "回复 接受挑战 即可开始对局。\n" "【30秒内有效】"
        user.connect = group_id
        session.round = 1
        return game.start_tips(msg)

    def accept(self, event: Event) -> Result:
        """接受挑战"""
        session = self.session
        group_id = session.group_id
        if msg := session.try_join_game(event):
            return None if msg == " " else msg
        user, group_account = Manager.locate_user(event)
        if group_account.gold < session.gold:
            session.leave()
            return f"你的金币不足以接受这场对决！\n——你还有{group_account.gold}枚金币。"
        user.connect = group_id
        bet_limit = min(Manager.locate_user_at(session.p1_uid, group_id)[1].gold, group_account.gold)
        bet_limit = 0 if bet_limit < 0 else bet_limit
        if session.gold == -1:
            session.gold = random.randint(0, bet_limit)
            self.gold = session.gold
        session.bet_limit = bet_limit
        session.next = session.p1_uid
        return self.session_tips()

    def refuse(self, user_id: int):
        """拒绝挑战"""
        session = self.session
        group_id = session.group_id
        if time.time() - session.time > 60:
            del current_games[group_id]
        if session.at != user_id:
            return
        if session.p2_uid:
            return "对决已开始，拒绝失败。"
        else:
            del current_games[group_id]
            return "拒绝成功，对决已结束。"

    def overtime(self):
        """超时结算"""
        session = self.session
        if time.time() - session.time > 30 and session.p1_uid and session.p2_uid:
            try:
                self.end()
            except GameOverException as e:
                return e.result

    def fold(self, user_id: str):
        """认输"""
        session = self.session
        if session.p1_uid and session.p2_uid:
            if user_id == session.p1_uid:
                session.win = session.p2_uid
            elif user_id == session.p2_uid:
                session.win = session.p1_uid
            else:
                return
            try:
                self.end()
            except GameOverException as e:
                return e.result

    def restart(self):
        """
        游戏重置
        """
        session = self.session
        group_id = session.group_id
        overtime = time.time() - session.time
        if overtime < 60:
            return f"当前游戏已创建 {int(overtime)} 秒，未超时。"
        del current_games[group_id]
        return "游戏已重置。"

    @abstractmethod
    def start_tips(self, msg):
        """游戏开始的提示"""

    @abstractmethod
    def action(self, event: Event):
        """游戏进行"""

    @abstractmethod
    def session_tips(self):
        """场次提示信息"""

    def accept_tips(self, tip1, tip2):
        """
        合成接受挑战的提示信息
        """
        return (
            f"{self.session.p2_nickname}接受了对决！\n{tip1}"
            + (f"对战金额为 {self.session.gold} 金币\n" if self.session.gold else "")
            + f"请{self.session.p1_nickname}{tip2}"
        )

    def settle(self):
        """
        游戏结束结算
            return:结算界面
        """
        session = self.session
        group_id = session.group_id
        win = session.win if session.win else session.p1_uid if session.next == session.p2_uid else session.p2_uid
        winner, winner_group_account = Manager.locate_user_at(win, group_id)
        lose = session.p1_uid if session.p2_uid == win else session.p2_uid
        loser, loser_group_account = Manager.locate_user_at(lose, group_id)
        gold = session.gold
        if winner_group_account.props.get("42001", 0) > 0:
            fee = 0
            fee_tip = f'『{Prop.get_prop_name("42001")}』免手续费'
        else:
            rand = random.randint(0, 5)
            fee = int(gold * rand / 100)
            Manager.locate_group(group_id).company.bank += fee
            fee_tip = f"手续费：{fee}({rand}%)"
        maxgold = int(max_bet_gold * 5)
        if winner_group_account.props.get("52002", 0) > 0:
            if winner_group_account.props.get("42002", 0) > 0:
                extra = int(gold * 0.2)
            else:
                extra = int(gold * 0.1)
            if extra < maxgold:
                extra_tip = f'◆『{Prop.get_prop_name("52002")}』\n'
            else:
                extra = maxgold
                extra_tip = f'◆『{Prop.get_prop_name("52002")}』最大奖励\n'
        else:
            extra_tip = ""
            extra = 0

        if gold >= loser_group_account.gold and loser_group_account.security:
            loser_group_account.security -= 1
            security = random.randint(security_gold[0], security_gold[1])
            security_tip = f"◇『金币补贴』(+{security})\n"
        else:
            security = 0
            security_tip = ""

        if loser_group_account.props.get("52001", 0) > 0:
            if winner_group_account.props.get("42002", 0) > 0:
                off = int(gold * 0.2)
            else:
                off = int(gold * 0.1)
            if off < maxgold:
                off_tip = f'◇『{Prop.get_prop_name("52001")}』\n'
            else:
                off = maxgold
                off_tip = f'◇『{Prop.get_prop_name("52001")}』最大补贴\n'
        else:
            off = 0
            off_tip = ""

        win_gold = gold - fee + extra
        winner.win += 1
        winner.Achieve_win += 1
        winner.Achieve_lose = 0

        lose_gold = gold - off
        loser.lose += 1
        loser.Achieve_lose += 1
        loser.Achieve_win = 0

        msg = (
            f"结算：\n"
            "----\n"
            + extra_tip
            + (tmp + "\n" if (tmp := "\n".join(x for x in Manager.Achieve_list((winner, winner_group_account)))) else "")
            + f"◆胜者 {winner_group_account.nickname}\n"
            f"◆结算 {winner_group_account.gold}(+{win_gold})\n"
            f"◆战绩 {winner.win}:{winner.lose}\n"
            f"◆胜率 {round(winner.win * 100 / (winner.win + winner.lose), 2) if winner.win > 0 else 0}%\n"
            "----\n"
            + off_tip
            + (tmp + "\n" if (tmp := "\n".join(x for x in Manager.Achieve_list((loser, loser_group_account)))) else "")
            + f"◇败者 {loser_group_account.nickname}\n"
            f"◇结算 {loser_group_account.gold}(-{lose_gold})\n" + security_tip + f"◇战绩 {loser.win}:{loser.lose}\n"
            f"◇胜率 {round(loser.win * 100 / (loser.win + loser.lose), 2) if loser.win > 0 else 0}%\n"
            "----\n" + fee_tip
        )
        winner.gold += win_gold
        winner_group_account.gold += win_gold
        loser.gold -= lose_gold - security
        loser_group_account.gold -= lose_gold - security

        del current_games[group_id]
        return (
            f"这场对决是 {winner_group_account.nickname} 胜利了",
            linecard_to_png(msg, width=880),
            self.end_tips(),
        )

    @abstractmethod
    def end_tips(self):
        """结束附件"""

    def end(self, result: Result = None):
        """输出结算界面"""
        settle = self.settle()

        async def output():
            if result:
                if isinstance(result, (str, BytesIO, list)):
                    yield result
                else:
                    async for i in result():
                        if i:
                            yield i
                await asyncio.sleep(1)
            for i in settle:
                if i:
                    yield i
                    await asyncio.sleep(1)

        raise GameOverException(output)


class GunFight(Game):
    """
    西部枪战
    """

    name = "GunFight"
    max_bet_gold: int = max_bet_gold * 5

    def __init__(self, kwargs):
        super().__init__(kwargs)
        gold = kwargs["gold"]
        self.gold: int = gold
        self.MAG1 = 1
        self.MAG2 = 1
        self.first = None

    def action(self, event: Event):
        """
        装弹|开枪|闪避|闪避开枪|预判开枪
        """
        user_id = event.user_id
        session = self.session
        if msg := session.shot_check(user_id):
            return None if msg == " " else msg

        card = event.raw_command
        if user_id == session.p1_uid:
            if card == "装弹":
                self.MAG1 += 1
                self.MAG1 = min(self.MAG1, 6)
            elif card in {"开枪", "闪枪", "预判开枪"}:
                if self.MAG1 < 1:
                    return f"行动失败。你的子弹不足"
                self.MAG1 -= 1
            self.first = card
            session.nextround()
            return f"{session.p1_nickname}已行动，现在是{session.p2_nickname}的回合。"
        else:
            if card == "装弹":
                self.MAG2 += 1
                self.MAG2 = min(self.MAG2, 6)
            elif card in {"开枪", "闪枪", "预判开枪"}:
                if self.MAG2 < 1:
                    return f"行动失败。你的子弹不足"
                self.MAG2 -= 1
            session.nextround()
            msg = f"双方行动 {self.first} - {card}\n"
            msg += f"剩余子弹 {self.MAG1} - {self.MAG2}\n"
            if (
                self.first == "开枪"
                and card in {"装弹", "预判开枪"}
                or self.first == "闪枪"
                and card in {"装弹", "开枪"}
                or self.first == "预判开枪"
                and card in {"闪避", "闪枪"}
            ):
                session.win = session.p1_uid
                msg += f"{session.p1_nickname}赢得了对决"
            elif (
                card == "开枪"
                and self.first in {"装弹", "预判开枪"}
                or card == "闪枪"
                and self.first in {"装弹", "开枪"}
                or card == "预判开枪"
                and self.first in {"闪避", "闪枪"}
            ):
                session.win = session.p2_uid
                msg += f"{session.p2_nickname}赢得了对决"
            else:
                self.first = None
                msg += f"本轮平局。请{session.p1_nickname}开始行动！"
                return msg
            self.end(msg)

    def start_tips(self, msg):
        """
        发起游戏：西部枪战
        """
        return "场地准备完毕\n" + (f"本场金币：{self.gold}\n" if self.gold else "") + f"{msg}"

    def session_tips(self):
        tip1 = "本场对决为【西部枪战】\n"
        tip2 = "\n装弹|开枪|闪避|闪枪|预判开枪"
        return self.accept_tips(tip1, tip2)

    def end_tips(self):
        return ""


class MultiplayerGame(AROF):
    """
    多人游戏类
    """

    name: str = "MultiplayerGame"

    def __init__(self, kwargs):
        self.session: Session = Session(kwargs)

    @classmethod
    def start(cls, event: Event) -> Result:
        """
        开始多人游戏
        """
        group_id = event.group_id
        game = current_games.get(group_id)
        if not game:
            pass
        elif isinstance(game, MultiplayerGame):
            overtime = time.time() - game.session.time
            if overtime > 180:
                pass
            elif game.world.start == 0:
                return "一场游戏正在报名中"
            else:
                return f"一场游戏正在进行中，遇到问题可以{f'在{t}秒后' if (t := int(180 - overtime)) > 0 else ''}输入【游戏重置】重置游戏"
        elif msg := game.session.create_check(event):
            return msg
        kwargs = {
            "at": " ",
            "gold": event.args_to_int(bet_gold),
            "group_id": event.group_id,
            "p1_uid": event.user_id,
            "p1_nickname": event.nickname,
        }
        game = current_games[group_id] = cls(kwargs)
        return game.start_tips(event.nickname)

    @abstractmethod
    def start_tips(self, msg):
        """游戏开始的提示"""

    @abstractmethod
    def join(self, event: Event) -> Result:
        """
        加入游戏
        """

    def restart(self):
        """
        游戏重置
        """
        session = self.session
        group_id = session.group_id
        overtime = time.time() - session.time + 180
        if overtime < 180:
            return f"当前游戏已创建 {int(overtime)} 秒，未超时。"
        del current_games[group_id]
        return "游戏已重置。"


from .horse_race.start import load_dlcs
from .horse_race.race_group import race_group as RaceWorld


class HorseRace(MultiplayerGame):
    """
    赛马小游戏
    """

    name: str = "HorseRace"

    events_list = load_dlcs()

    def __init__(self, kwargs):
        super().__init__(kwargs)
        self.world = RaceWorld()

    def join(self, event: Event) -> Result:
        """
        赛马加入
        """
        if self.name != "HorseRace":
            return "其他游戏进行中。"
        session = self.session
        user, group_account = Manager.locate_user(event)
        user_id = user.user_id
        if (gold := group_account.gold) < session.gold:
            return f"报名赛马需要{self.session.gold}金币，你的金币：{gold}。"
        race = self.world
        if race.start != 0:
            return
        if (query_of_player := race.query_of_player()) >= max_player:
            return "加入失败！赛马场就那么大，满了满了！"
        if race.is_player_in(user_id) == True:
            return "加入失败！您已经加入了赛马场!"
        horsename = event.single_arg("")
        if not horsename:
            return "请输入你的马儿名字"
        horsename = horsename[:2] + "酱" if len(horsename) > 7 else horsename
        race.add_player(horsename, user_id, group_account.nickname)
        return f"{event.nickname}\n" "> 加入赛马成功\n" "> 赌上马儿性命的一战即将开始!\n" f"> 赛马场位置:{query_of_player + 1}/{max_player}"

    def run(self):
        """
        赛马开始
        """
        events_list = self.events_list
        race = self.world
        if (player_count := race.query_of_player()) == 0:
            return
        if race.start == 1:
            return
        if race.start == 0 or race.start == 2:
            if player_count >= min_player:
                race.start = 1
            else:
                return f"开始失败！赛马开局需要最少{min_player}人参与"

        session = self.session
        group_id = session.group_id
        session.time = time.time() + 180
        empty_race = ["[  ]" for _ in range(max_player - player_count)]

        async def result():
            yield f"> 比赛开始\n> 当前奖金：{session.gold * player_count}金币" if session.gold else "比赛开始！"
            await asyncio.sleep(1)
            while race.start == 1:
                # 回合数+1
                race.round_add()
                # 移除超时buff
                race.del_buff_overtime()
                # 马儿全名计算
                race.fullname()
                # 回合事件计算
                text = race.event_start(events_list)
                # 马儿移动
                race.move()
                # 场地显示
                output = linecard_to_png("\n".join(race.display() + empty_race), font_size=30)
                yield [text, output]
                await asyncio.sleep(0.5 + int(0.06 * len(text)))
                # 全员失败计算
                if race.is_die_all():
                    for x in race.player:
                        user_id = x.playeruid
                        if user_id in Manager.user_data:
                            user, group_accounts = Manager.locate_user_at(user_id, group_id)
                            user.gold -= session.gold
                            group_accounts.gold -= session.gold
                    del current_games[group_id]
                    yield "比赛已结束，鉴定为无马生还"
                    return

                # 全员胜利计算
                winer = race.is_win_all()
                winer_list = "\n"
                if winer != []:
                    yield f"> 比赛结束\n> {bot_name}正在为您生成战报..."
                    await asyncio.sleep(1)
                    gold = int(session.gold * player_count / len(winer))
                    for x in race.player:
                        user_id = x.playeruid
                        if user_id in Manager.user_data:
                            user, group_accounts = Manager.locate_user_at(user_id, group_id)
                            user.gold -= session.gold
                            group_accounts.gold -= session.gold
                    for user_name, user_id in winer:
                        winer_list += f"> {user_name}\n"
                        if user_id in Manager.user_data:
                            user, group_accounts = Manager.locate_user_at(user_id, group_id)
                            user.gold += gold
                            group_accounts.gold += gold
                    del current_games[group_id]
                    yield f"> 比赛已结束，胜者为：{winer_list}" + (f"> 本次奖金：{gold} 金币" if gold else "> 祝贺！")
                    return
                await asyncio.sleep(1)

        return result

    def start_tips(self, msg):
        """
        发起游戏：赛马
        """
        return (
            f"{msg}\n"
            "> 创建赛马比赛成功！\n"
            + (f"> 本场金额：{self.session.gold}金币\n" if self.session.gold else "")
            + "> 输入 【赛马加入 名字】 即可加入赛马。"
        )


from .Fortress.core import World as FortressWorld


class Fortress(MultiplayerGame):
    """
    要塞战
    """

    name: str = "Fortress"

    def __init__(self, kwargs):
        super().__init__(kwargs)
        self.world = FortressWorld()

    def join(self, event: Event) -> Result:
        """
        要塞战加入
        """
        if self.name != "Fortress":
            return "其他游戏进行中。"
        session = self.session
        user, group_account = Manager.locate_user(event)
        user_id = user.user_id
        if (gold := group_account.gold) < session.gold:
            return f"报名要塞战需要{self.session.gold}金币，你的金币：{gold}。"
        world: FortressWorld = self.world
        if world.start != 0:
            return
        if user_id in world.ids:
            return "你已经加入了游戏"
        if len(world.players) > 14:
            return "人满了"
        index = None
        team = None
        args = event.args
        if args:
            if len(args) == 1:
                args = args[0]
                if args.isdigit():
                    index = int(args)
                else:
                    team = args
            else:
                index = args[0]
                team = args[1]
                if index.isdigit():
                    index = int(args)
                else:
                    team = index
                    index = None
        if index:
            if 0 < index <= 14:
                if index in world.players:
                    return f"{index}号位置已经有人了\n请选择\n{','.join(i for i in range(1,15) if i not in world.castles)}"
            else:
                return f"位置不存在。请选择\n{','.join(i for i in range(1,15) if i not in world.castles)}"
        else:
            index = random.choice([i for i in range(1, 15) if i not in world.castles])

        world.add_player(group_account, index, team or user_id)
        return (
            f"{event.nickname}\n"
            "> 要塞战加入成功\n"
            "> 战争即将开始!\n"
            f"> 你的位置是 {index} 号城\n"
            f"> 你的队伍是 {team if team else '个人'}"
        )

    def run(self):
        """
        要塞战开始
        """
        world: FortressWorld = self.world
        N = len(world.players)
        if N == 0:
            return
        if world.start != 0:
            return
        if N >= min_player:
            world.start = 1
        else:
            return f"开始失败！要塞战需要最少{min_player}人参与"
        group_id = self.session.group_id

        async def result():
            yield world.draw()
            await asyncio.sleep(1)
            yield f"请{world.players[world.ids[0]].group_account.nickname}开始行动"

        return result

    def session_start(self, event: Event) -> Result:
        """
        开始行动
        """
        world: FortressWorld = self.world
        start = world.start
        if start == 0:
            return
        start -= 1
        if world.ids[start] != event.user_id:
            return "现在不是你的回合。"
        if world.act != 0:
            return "你的回合已开始。"
        world.act = 1
        world.round += 1
        msg = ""
        for index in range(0, 15):
            if (castle := world.castles.get(index)) and castle.user_id == world.ids[start]:
                msg += f"你的{index}号城获得了：\n{castle.turntable()}\n"

        async def result():
            yield msg[:-1]
            await asyncio.sleep(1)
            yield world.draw()

        return result

    def session_end(self, event: Event) -> Result:
        """
        结束行动
        """
        world: FortressWorld = self.world
        start = world.start
        if start == 0:
            return
        start -= 1
        if world.ids[start] != event.user_id:
            return "现在不是你的回合。"
        world.act = 0
        msg = ""
        world.start += 1
        if world.start > (len(world.ids)):
            world.start = 1
            world.round += 1
        return f"请{world.players[world.ids[world.start - 1]].group_account.nickname}开始行动"

    def session_action(self, event: Event) -> Result:
        """
        行动
        """
        world: FortressWorld = self.world
        start = world.start
        if start == 0:
            return
        start -= 1
        if world.ids[start] != event.user_id:
            return "现在不是你的回合。"

        async def result():
            if world.act == 0:
                async for x in self.session_start(event)():
                    yield x
                await asyncio.sleep(1)
            yield "|".join(event.args)

        return result

    def start_tips(self, msg):
        """
        发起游戏：要塞战
        """
        return (
            f"{msg}\n"
            "> 要塞战创建成功！\n"
            + (f"> 本场金额：{self.session.gold}金币\n" if self.session.gold else "")
            + "> 输入 【要塞加入 编号 队伍】 即可加入要塞战。"
        )


current_games: Dict[str, AROF] = {}

# 开始游戏

GAMES_DICT: Dict[str, Type[AROF]] = {
    "Russian": Russian,
    "Dice": Dice,
    "Poker": Poker,
    "LuckyNumber": LuckyNumber,
    "Cantrell": Cantrell,
    "Blackjack": Blackjack,
    "ABCard": ABCard,
    "GunFight": GunFight,
    "HorseRace": HorseRace,
    "Fortress": Fortress,
}

StartGameCommand = {
    "Russian": {"俄罗斯轮盘", "装弹"},
    "Dice": {"掷色子", "摇色子", "掷骰子", "摇骰子"},
    "Poker": {"扑克对战", "卡牌对战"},
    "LuckyNumber": {"猜数字"},
    "Cantrell": {"同花顺", "港式五张", "梭哈"},
    "Blackjack": {"21点"},
    "ABCard": {"AB牌", "ab牌"},
    "GunFight": {"西部枪战", "西部对战", "牛仔对战", "牛仔对决"},
    "HorseRace": {"赛马创建", "创建赛马"},
    "Fortress": {"堡垒战创建", "要塞战创建", "创建堡垒战", "创建要塞战"},
}

for event_name, commands in StartGameCommand.items():

    @reg_auto_event(f"{event_name}:Start", commands, need_extra_args={"at"})
    async def _(event: Event) -> str:
        if event.is_private():
            return
        game = GAMES_DICT[event.event_name[:-6]]
        return game.start(event)


@reg_command("random_game", {"随机对战"})
async def _(event: Event) -> str:
    gold = event.args_to_int(-1)
    group_account = Manager.locate_user(event)[1]
    if group_account.props.get("32002", 0) < 1:
        return f"你未持有持有【{Prop.get_prop_name('32002')}】，无法发起随机对战。"
    game = random.choice([Russian, Dice, Poker, LuckyNumber, Cantrell, Blackjack, ABCard, GunFight])
    return game.start(event, gold=gold)


PlayGameCommand = {
    "Russian": {"开枪", "咔", "嘭", "嘣"},
    "Dice": {"取出", "开数", "开点"},
    "Poker": {"出牌"},
    "LuckyNumber": r"^\d{1,3}$",
    "Cantrell": {"看牌", "开牌"},
    "Blackjack": {"停牌", "抽牌", "双倍停牌"},
    "ABCard": {"A", "a", "B", "b", "1", "2", "3"},
    "GunFight": {"装弹", "开枪", "闪避", "闪枪", "预判开枪"},
}

# 进行对战游戏

for event_name, commands in PlayGameCommand.items():

    @reg_auto_event(f"{event_name}:Play", commands)
    async def _(event: Event) -> str:
        group_id = Manager.get_user(event.user_id).connect if event.is_private() else event.group_id
        game = current_games.get(group_id)
        if not game or game.name != event.event_name[:-5]:
            return
        try:
            result = game.action(event)
        except GameOverException as e:
            result = e.result
        if event.is_private():
            event.group_id = group_id

            @event.got()
            async def _(event: Event):
                event.finish()
                return result

            return "请在群内回复 确认 以完成操作"
        else:
            return result


# 加入多人游戏

MultiplayerGameTips = {
    "HorseRace": "赛马活动未开始，请输入【赛马创建】创建赛马场",
    "Fortress": "要塞战未开始，请输入【要塞战创建】创建要塞战游戏",
}

JoinMultiplayerGameCommand = {
    "HorseRace": {"赛马加入", "加入赛马"},
    "Fortress": {"要塞加入", "堡垒加入", "加入要塞", "加入堡垒"},
}

for event_name, commands in JoinMultiplayerGameCommand.items():

    @reg_auto_event(f"{event_name}:Join", commands)
    async def _(event: Event) -> str:
        game = current_games.get(event.group_id)
        game_name = event.event_name[:-5]
        if not game or game.name != game_name:
            return MultiplayerGameTips[game_name]
        return game.join(event)


# 开始多人游戏

RunMultiplayerGameCommand = {
    "HorseRace": {"赛马开始", "开始赛马"},
    "Fortress": {"游戏开始", "开始游戏"},
}

for event_name, commands in RunMultiplayerGameCommand.items():

    @reg_auto_event(f"{event_name}:Run", commands)
    async def _(event: Event) -> str:
        game = current_games.get(event.group_id)
        game_name = event.event_name[:-4]
        if not game or game.name != game_name:
            return MultiplayerGameTips[game_name]
        return game.run()


# AROF环节


@reg_command("GameAccept", {"接受挑战", "接受决斗", "接受对决"})
async def _(event: Event) -> str:
    if game := current_games.get(event.group_id):
        return game.accept(event)


@reg_command("GameRefuse", {"拒绝挑战", "拒绝决斗", "拒绝对决"})
async def _(event: Event) -> str:
    if game := current_games.get(event.group_id):
        return game.refuse(event.user_id)


@reg_command("GameOvertime", {"超时结算"})
async def _(event: Event) -> str:
    if game := current_games.get(event.group_id):
        return game.overtime()


@reg_command("GameFold", {"认输", "投降", "结束"})
async def _(event: Event) -> str:
    if game := current_games.get(event.group_id):
        return game.fold(event.user_id)


@reg_command("GameClear", {"清除游戏", "清除对局", "清除对决", "清除对战"}, need_extra_args={"permission"})
async def _(event: Event) -> str:
    if event.permission() and event.group_id in current_games:
        del current_games[event.group_id]


@reg_command("session_start", {"回合开始"})
async def _(event: Event) -> str:
    if game := current_games.get(event.group_id):
        return game.session_start(event)


@reg_command("session_end", {"回合结束"})
async def _(event: Event) -> str:
    if game := current_games.get(event.group_id):
        return game.session_end(event)


@reg_command("session_action", {"行动"})
async def _(event: Event) -> str:
    if game := current_games.get(event.group_id):
        return game.session_action(event)
