from nonebot.adapters.onebot.v11 import (
    GROUP,
    GROUP_ADMIN,
    GROUP_OWNER,
    Bot,
    MessageEvent,
    GroupMessageEvent,
    Message,
)
from nonebot import get_driver
from nonebot.permission import SUPERUSER
from nonebot import on_message, on_command, on_regex, on_fullmatch
from nonebot.params import CommandArg, Arg
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.rule import to_me
from nonebot import require
from nonebot.log import logger

try:
    import ujson as json
except ModuleNotFoundError:
    import json

import random
import time
import datetime
import re
import shutil

from . import Manager
from . import Account
from . import Market
from . import Game
from . import Prop
from . import Alchemy

from .utils.utils import get_message_at, number
from .data import ExchangeInfo,menu_data
from .config import Config, revolt_cd, bet_gold, path, backup

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name = "小游戏合集",
    description = "各种群内小游戏",
    usage = "金币签到",
    config = Config,
    extra = {'menu_data':menu_data,'menu_template':'default'})

data = Manager.data
company_index = Manager.company_index
current_games = Game.current_games

def to_int(arg:Message, default:int = bet_gold):
    num = arg.extract_plain_text().strip()
    if num.isdigit():
        return int(num)
    else:
        return default

AllGameTips = {
    "HorseRace":"赛马活动未开始，请输入【赛马创建】创建赛马场",
    "Fortress":"要塞战未开始，请输入【要塞战创建】创建要塞战游戏",
    }

# 加入游戏
AllJoinGameCommand = {
    "HorseRace":{"赛马加入","加入赛马"},
    "Fortress":{"要塞加入","堡垒加入","加入要塞","加入堡垒"},
    }

AllJoinGameCommand = {cmd: name for name, cmds in AllJoinGameCommand.items() for cmd in cmds}
async def join_game_rule(bot:Bot, event:GroupMessageEvent, state:T_State) -> bool:
    """
    规则：加入游戏
    """
    msg = event.message.extract_plain_text()
    for cmd in AllJoinGameCommand:
        if msg.startswith(cmd):
            game = current_games.get(event.group_id)
            name = AllJoinGameCommand[cmd]
            if game:
                if game.name == name:
                    state["Game"] = game
                    state["arg"] = msg[len(cmd):].strip()
                    return True
                return False
            else:
                await bot.send(event,AllGameTips[name])
                return False
    else:
        return False

join_game = on_message(rule = join_game_rule, permission = GROUP, priority = 20, block = True)

@join_game.handle()
async def _(event:GroupMessageEvent, state:T_State):
    game = state["Game"]
    msg = game.join(event,state["arg"])
    await join_game.finish(msg)

async def AROF_check(event:GroupMessageEvent, state:T_State):
    """
    本群有AROF
    """
    group_id = event.group_id
    if group_id in current_games and current_games[group_id].name in {"Fortress"}:
        state["game"] = current_games[group_id]
        return True
    else:
        return False

# 回合开始
AROF_start = on_command("回合开始", rule = AROF_check, priority = 20, block = True)

@AROF_start.handle()
async def _(bot:Bot, event:GroupMessageEvent):
    game = current_games[event.group_id]
    msg = await game.AROF_start(bot,event.user_id)
    await AROF_start.finish(msg)

# 回合结束
AROF_end = on_command("回合结束", rule = AROF_check, priority = 20, block = True)
@AROF_end.handle()
async def _(bot:Bot, event:GroupMessageEvent):
    game = current_games[event.group_id]
    msg = await game.AROF_end(bot,event.user_id)
    await AROF_end.finish(msg)

# 行动
AROF_action = on_command("行动", rule = AROF_check, priority = 20, block = True)

@AROF_action.handle()
async def _(bot:Bot, event:GroupMessageEvent, arg:Message = CommandArg()):
    game = current_games[event.group_id]
    msg = await game.AROF_action(bot,event.user_id,*arg.extract_plain_text().strip().split())
    await AROF_action.finish(msg)

# 开始游戏
AllRunGameCommand = {
    "HorseRace":{"赛马开始","开始赛马"},
    "Fortress":{"游戏开始","开始游戏"},
    }
AllRunGameCommand = {cmd: name for name, cmds in AllRunGameCommand.items() for cmd in cmds}

async def run_game_rule(bot:Bot, event:GroupMessageEvent, state:T_State) -> bool:
    """
    规则：开始游戏
    """
    msg = event.message.extract_plain_text()
    for cmd in AllRunGameCommand:
        if msg.startswith(cmd):
            game = current_games.get(event.group_id)
            name = AllRunGameCommand[cmd]
            if game:
                if game.name == name:
                    state["Game"] = game
                    return True
                return False
            else:
                await bot.send(event,AllGameTips[name])
                return False
    else:
        return False

run_game = on_message(rule = run_game_rule, permission = GROUP, priority = 20, block = True)

@run_game.handle()
async def _(bot:Bot, state:T_State):
    game = state["Game"]
    msg = await game.run(bot)
    await run_game.finish(msg)

# 赛马暂停
RaceStop = on_command(
    "赛马暂停",
    aliases = {"暂停赛马"},
    rule = lambda event:isinstance(event,GroupMessageEvent) and event.group_id in current_games and current_games[event.group_id].name == "HorseRace",
    permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
    priority = 20,
    block = True
    )
@RaceStop.handle()
async def _(event:GroupMessageEvent):
    current_games[event.group_id].race_group.start = 2

# GameClear
GameClear = on_command(
    "GameClear",
    aliases = {"清除游戏", "清除对局", "清除对决", "清除对战"},
    rule = lambda event:isinstance(event,GroupMessageEvent) and event.group_id in current_games,
    permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
    priority = 20,
    block = True
    )

@GameClear.handle()
async def _(event:GroupMessageEvent):
    del current_games[event.group_id]

# 获取金币
gain_gold = on_command("获取金币", permission = SUPERUSER, priority = 20, block = True)

@gain_gold.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    gold = to_int(arg,bet_gold)
    msg =  Account.gain_gold(event,gold)
    await gain_gold.finish(msg, at_sender=True)

# 获取道具
gain_prop = on_command("获取道具", permission = SUPERUSER, priority = 20, block = True)

@gain_prop.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    arg = arg.extract_plain_text().strip().split()
    test = len(arg)
    if test == 1:
        prop_name = arg[0]
        count = 1
    elif test >1:
        prop_name = arg[0]
        count = number(arg[1])
        if count < 1:
            count = 1
    else:
        return
    msg = Account.gain_prop(event, prop_name, count)
    await gain_prop.finish(msg, at_sender = True)

# 新建道具
prop_create = on_command("新建道具",rule = to_me(), permission = SUPERUSER, priority = 20, block = True)

@prop_create.handle()
async def _(matcher:Matcher, name:Message = CommandArg()):
    await prop_create.send("开始制作新道具！输入【取消】中止对话。", at_sender = True)

@prop_create.got("name", prompt = "请输入道具名")
async def _(matcher:Matcher, name:Message = Arg()):
    name = name.extract_plain_text().strip()
    if name == "取消":
        await prop_create.finish("新建道具已取消")
    matcher.set_arg("name",name)

from matplotlib.colors import is_color_like

@prop_create.got("color", prompt = "请输入主题色")
async def _(matcher:Matcher, color:Message = Arg()):
    color = color.extract_plain_text().strip()
    if color == "取消":
        await prop_create.finish("新建道具已取消")
    if is_color_like(color):
        matcher.set_arg("color",color)
    else:
        await prop_create.reject("请输入合法的颜色，例如\"red\",\"#123456\"")

@prop_create.got("rare", prompt = "请输入稀有度，范围0-6")
async def _(matcher:Matcher, rare:Message = Arg()):
    rare = rare.extract_plain_text().strip()
    if rare == "取消":
        await prop_create.finish("新建道具已取消")
    if rare.isdigit() and 0 <= int(rare) <= 6:
        matcher.set_arg("rare",int(rare))
    else:
        await prop_create.reject("请输入0-6")

@prop_create.got("code1", prompt = "请输入道具性质，可选【群内道具】或【全局道具】。")
async def _(matcher:Matcher, code1:Message = Arg()):
    code1 = code1.extract_plain_text().strip()
    if code1 == "取消":
        await prop_create.finish("新建道具已取消")
    if code1 := {"群内道具":"2","全局道具":"3"}.get(code1):
        matcher.set_arg("code1",code1)
    else:
        await prop_create.reject("请输入\"群内道具\"或\"全局道具\"")

@prop_create.got("code2", prompt = "请输入道具时效，可选【时效道具】或【永久道具】。")
async def _(matcher:Matcher, code2:Message = Arg()):
    code2 = code2.extract_plain_text().strip()
    if code2 == "取消":
        await prop_create.finish("新建道具已取消")
    if code2 := {"时效道具":"0","永久道具":"1"}.get(code2):
        matcher.set_arg("code2",code2)
    else:
        await prop_create.reject("请输入\"时效道具\"或\"永久道具\"")

@prop_create.got("info", prompt = "请输入两段介绍，用空格隔开")
async def _(matcher:Matcher, info:Message = Arg()):
    info = info.extract_plain_text().strip().split(maxsplit = 2)
    if info[0] == "取消":
        await prop_create.finish("新建道具已取消")
    intro = info[0]
    if len(info) < 2:
        des = ""
    else:
        des = info[1]
    rare = matcher.get_arg('rare')
    msg = Prop.prop_create(
        f"{rare}{matcher.get_arg('code1')}{matcher.get_arg('code2')}",
        matcher.get_arg('name'),
        matcher.get_arg('color'),
        matcher.get_arg('rare'),
        intro,
        des
        )
    await prop_create.finish(msg)
# 删除道具
prop_delete = on_command("删除道具", permission = SUPERUSER, priority = 20, block = True)

@prop_delete.handle()
async def _(arg:Message = CommandArg()):
    msg = Prop.prop_delete(arg.extract_plain_text().strip())
    await prop_delete.finish(msg, at_sender = True)

# 银行存取

async def bank_rule(bot:Bot, event:GroupMessageEvent, state:T_State ,permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER) -> bool:
    """
    规则：银行存取
    """
    msg = event.message.extract_plain_text()
    if msg.startswith("存金币"):
        sign = -1
    elif msg.startswith("取金币"):
        if await permission(bot,event):
            sign = 1
        else:
            return False
    elif msg in {"查看群金库","群金库查看","查看群资产","群资产查看"}:
        sign = 0
    else:
        return False
    gold = msg[3:].strip()
    if gold.isdigit():
        gold = int(gold)
    elif sign:
        return False
    state["args"] = sign,gold
    return True

bank = on_message(rule = bank_rule, permission = GROUP, priority = 20, block = True)

@bank.handle()
async def _(event:GroupMessageEvent, state:T_State):
    msg = Market.bank(event,*state["args"])
    await bank.finish(msg, at_sender = True)

# 资产存取

async def invest_rule(bot:Bot, event:GroupMessageEvent, state:T_State ,permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER) -> bool:
    """
    规则：资产存取
    """
    msg = event.message.extract_plain_text()
    if msg.startswith("存股票"):
        sign = -1
    elif msg.startswith("取股票"):
        if await permission(bot,event):
            sign = 1
        else:
            return False
    else:
        return False
    info = arg_check(msg[3:].strip().split())
    if not info:
        return False
    count,company_name,_ = info
    state["args"] = sign,count,company_name
    return True

invest = on_message(rule = invest_rule, permission = GROUP, priority = 20, block = True)

@invest.handle()
async def _(event:GroupMessageEvent, state:T_State):
    msg = Market.invest(event,*state["args"])
    await invest.finish(msg, at_sender = True)

# 金币签到
sign = on_command("金币签到", aliases = {"轮盘签到"}, priority = 20, block = True)

@sign.handle()
async def _(event:MessageEvent):
    msg =  Account.sign(event)
    await sign.finish(msg, at_sender = True)

# 重置签到
revolt_sign = on_command("重置签到", aliases = {"revolt签到"}, priority = 20, block = True)

@revolt_sign.handle()
async def _(event:MessageEvent):
    msg = Account.revolt_sign(event)
    await revolt_sign.finish(msg, at_sender = True)

# 发动革命

from .config import revolt_cd

if revolt_cd:
    revolution = on_command("发起重置", permission = GROUP, priority = 20, block = True)

    @revolution.handle()
    async def _(event:GroupMessageEvent):
        msg = Account.revolution(event.group_id)
        await revolution.finish(msg)
else:
    logger.info("重置已被禁用")

# 发红包
give_gold = on_command("打钱", aliases = {"发红包", "赠送金币"}, permission = GROUP, priority = 20, block = True)

@give_gold.handle()
async def _(bot:Bot, event:GroupMessageEvent, arg:Message = CommandArg()):
    gold = arg.extract_plain_text().strip()
    if gold.isdigit():
        gold = int(gold)
    else:
        return
    if at := get_message_at(event.message):
        at = int(at[0])
    else:
        return
    target = Manager.locate_user_at(event, at)
    msg = Account.transfer_gold(event, target, gold)
    await give_gold.finish(msg, at_sender = True)

# 送道具
give_props = on_command("送道具", aliases = {"赠送道具"}, permission = GROUP, priority = 20, block = True)

@give_props.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg(),):
    arg = arg.extract_plain_text().strip().split()
    at = get_message_at(event.message)
    test = len(arg)
    if test and at:
        at = at[0]
        if test == 1:
            prop_name = arg[0]
            count = 1
        elif test >1:
            prop_name = arg[0]
            count = number(arg[1])
            if count < 1:
                count = 1
    else:
        return

    target = Manager.locate_user_at(event, int(at))
    msg = Account.transfer_props(event, target, prop_name, count)
    await give_props.finish(msg, at_sender = True)

from .Game import current_games

# 创建游戏

AllCreateGameCommand = {
    "Russian":{"俄罗斯轮盘","装弹"},
    "Dice":{"掷色子", "摇色子", "掷骰子", "摇骰子"},
    "Poker":{"扑克对战", "扑克对决", "扑克决斗"},
    "LuckyNumber":{"猜数字"},
    "Cantrell":{"同花顺","港式五张","梭哈"},
    "Blackjack":{"21点"},
    "ABCard":{"AB牌","ab牌"},
    "GunFight":{"西部枪战","西部对战","牛仔对战","牛仔对决"},
    "HorseRace":{"赛马创建","创建赛马"},
    "Fortress":{"堡垒战创建","要塞战创建","创建堡垒战","创建要塞战"},
    }

AllCreateGameCommand = {cmd: name for name, cmds in AllCreateGameCommand.items() for cmd in cmds}

AllGames = {
    "Russian":Game.Russian,
    "Dice":Game.Dice,
    "Poker":Game.Poker,
    "LuckyNumber":Game.LuckyNumber,
    "Cantrell":Game.Cantrell,
    "Blackjack":Game.Blackjack,
    "ABCard":Game.ABCard,
    "GunFight":Game.GunFight,
    "HorseRace":Game.HorseRace,
    "Fortress":Game.Fortress,
    }

def create_game_rule(event:GroupMessageEvent, state:T_State)-> bool:
    """
    规则：创建对局
    """
    msg = event.message.extract_plain_text()

    for cmd in AllCreateGameCommand:
        if msg.startswith(cmd):
            state["Game"] = AllGames[AllCreateGameCommand[cmd]]
            state["arg"] = msg[len(cmd):].strip()
            return True
    else:
        return False

create_game = on_message(rule = create_game_rule, permission = GROUP, priority = 20, block = True)

@create_game.handle()
async def _(event:GroupMessageEvent, state:T_State):
    game = state["Game"]
    kwargs = game.parse_arg(state["arg"])
    msg = game.creat(event,**kwargs)
    await create_game.finish(msg)

# 进行游戏

AllPlayGameCommand = {
    "Russian":{"开枪","咔", "嘭", "嘣"},
    "Dice":{"取出","开数", "开点"},
    "Poker":{"出牌"},
    "LuckyNumber":{"^\d{1,3}$"},
    "Cantrell":{"看牌","加注","跟注","开牌"},
    "Blackjack":{"停牌","抽牌","双倍下注"},
    "ABCard":{"A","a","B","b","1","2","3"},
    "GunFight":{"装弹","开枪","闪避","闪枪","预判开枪"},
    }

def game_play_rule(event:MessageEvent, state:T_State)-> bool:
    """
    规则：游戏进行
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return False
    group_id = user.connect
    game = current_games.get(group_id)
    if game and (Name := game.name) not in {"HorseRace"}:
        cmdlst = AllPlayGameCommand.get(Name)
        if not cmdlst:
            return False
        msg = event.message.extract_plain_text()
        state["game"] = game
        if Name == "LuckyNumber":
            if msg.isdigit() and 0 < (N := int(msg)) <= 100:
                state["arg"] = (N,)
                return True
        elif Name in {"Blackjack","ABCard","GunFight"}:
            if msg in cmdlst:
                state["arg"] = (msg,)
                return True
        else:
            for cmd in cmdlst:
                if msg.startswith(cmd):
                    msg = msg[len(cmd):].strip()
                    if Name == "Cantrell":
                        if msg.isdigit():
                            gold = int(msg)
                        else:
                            gold = None
                        state["arg"] = ({"看牌":0,"加注":1,"跟注":1,"开牌":1}[cmd], gold)
                    elif msg.isdigit():
                        state["arg"] = (int(msg),)
                    else:
                        state["arg"] = (None,)

                    return True
    return False

game_play = on_message(rule = game_play_rule, priority = 15, block = True)

@game_play.handle()
async def _(bot:Bot, event:MessageEvent, state:T_State):
    game = state["game"]
    msg = await game.play(bot, event.user_id, *state["arg"])
    await game_play.finish(msg)

# 随机对战
random_game = on_command("随机对战", permission = GROUP, priority = 5, block = True)

@random_game.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg()):
    gold = to_int(arg,-1)
    msg = Game.random_game(event, gold)
    await random_game.finish(msg)

async def session_check(event:GroupMessageEvent, state:T_State):
    """
    本群有对局
    """
    group_id = event.group_id
    if group_id in current_games:
        state["game"] = current_games[group_id]
        return True
    else:
        return False

# 接受挑战
accept = on_command("接受挑战", aliases = {"接受决斗", "接受对决"}, rule = session_check, permission = GROUP, priority = 20, block = True)

@accept.handle()
async def _(event:GroupMessageEvent, state:T_State):
    game = state["game"]
    msg = game.accept(event)
    await accept.finish(msg)

# 拒绝挑战
refuse = on_command("拒绝挑战", aliases={"拒绝决斗", "拒绝对决"}, rule = session_check, permission = GROUP, priority = 20, block = True)

@refuse.handle()
async def _(event:GroupMessageEvent, state:T_State):
    game = state["game"]
    msg = game.refuse(event.user_id)
    await refuse.finish(msg)

# 超时结算
overtime = on_command("超时结算", rule = session_check, permission = GROUP, priority = 20, block = True)

@overtime.handle()
async def _(bot:Bot, state:T_State):
    game = state["game"]
    msg = await game.overtime(bot)
    await overtime.finish(msg)

# 认输结算
fold = on_fullmatch(("认输", "投降", "结束"), rule = session_check, permission = GROUP, priority = 20, block = True)

@fold.handle()
async def _(bot:Bot, event:GroupMessageEvent, state:T_State):
    game = state["game"]
    await game.fold(bot, event.user_id)

# 游戏重置
restart = on_command("游戏重置", aliases={"重置游戏"}, rule = session_check, permission = GROUP, priority = 20, block = True)

@restart.handle()
async def _(state:T_State):
    game = state["game"]
    msg = game.restart()
    await restart.finish(msg)

# 抽卡
gacha = on_regex("^.+连抽?卡?|单抽", rule = to_me(), priority = 20, block = True)

@gacha.handle()
async def _(bot:Bot, event:MessageEvent):
    cmd = event.get_plaintext()
    N = re.search(r"^(.*)连抽?卡?$",cmd)
    if N:
        N = N.group(1)
        N = number(N)
    else:
        N = 1
    if N and 0 < N <= 200:
        msg = Prop.gacha(event,N)
        await gacha.finish(msg)

# 使用道具
use_prop = on_command("使用道具", priority = 20, block = True)

@use_prop.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    prop_name = msg[0]
    count = 1
    if len(msg) > 1 and msg[1].isdigit():
        count = int(msg[1])
    else:
        count = 1
    msg = Prop.use_prop(event, prop_name, count)
    await use_prop.finish(msg, at_sender=True)

# 关联账户
connect = on_command("连接账户", aliases = {"关联账户"}, rule = to_me(), priority = 20, block = True)

@connect.handle()
async def _(event:MessageEvent, matcher:Matcher):
    if isinstance(event,GroupMessageEvent):
        matcher.set_arg("group_id", str(event.group_id))
    else:
        group_accounts = Manager.locate_user(event)[0].group_accounts
        msg = "你的账户\n"
        for group_id in group_accounts:
            msg += f'{group_id} 金币：{group_accounts[group_id].gold}枚\n'
        msg += "请输入你要关联的群号"
        await connect.send(msg)

@connect.got("group_id")

async def _(event:MessageEvent, group_id:Message = Arg()):
    group_id = str(group_id).strip()
    msg = Account.connect(event,group_id)
    await connect.finish(msg)

# 我的金币
my_gold = on_command("我的金币", priority = 20, block = True)

@my_gold.handle()
async def _(event:MessageEvent):
    msg = Account.my_gold(event)
    await my_gold.finish(msg, at_sender = True)

# 我的资料卡
my_info = on_command("我的信息", aliases = {"我的资料"}, priority = 20, block = True)

@my_info.handle()
async def _(event:MessageEvent):
    msg = await Account.my_info(event)
    await my_info.finish(msg)

# 我的交易信息
my_exchange = on_fullmatch(("我的交易信息","我的报价","我的股票"), priority = 20, block = True)

@my_exchange.handle()
async def _(event:MessageEvent):
    msg = await Account.my_exchange(event)
    await my_exchange.finish(msg)

# 元素精炼
alchemy_refine = on_command("元素精炼", priority = 20, block = True)

@alchemy_refine.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    Products = arg.extract_plain_text().strip().split()
    msg = Alchemy.alchemy_refine(event,Products)
    await alchemy_refine.finish(msg)

# 道具精炼
props_refine = on_command("道具精炼", priority = 20, block = True)

@props_refine.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    if len(msg) == 1:
        prop_name = msg[0]
        count = 1
    elif len(msg) == 2 and msg[1].isdigit():
        prop_name = msg[0]
        count = int(msg[1])
    else:
        return
    msg = Prop.props_refine(event, prop_name, count)
    await props_refine.finish(msg, at_sender = True)

# 炼金资料卡
alchemy_info = on_command("炼金账户", aliases = {"炼金资料"}, priority = 20, block = True)

@alchemy_info.handle()
async def _(event:MessageEvent):
    msg = await Alchemy.my_info(event)
    await alchemy_info.finish(msg)

# 查看元素订单
alchemy_order = on_command("查看元素订单", priority = 20, block = True)

@alchemy_order.handle()
async def _(event:MessageEvent):
    msg = Market.alchemy_order(event)
    await alchemy_order.finish(msg)

# 完成元素订单
complete_order = on_command("完成元素订单", priority = 20, block = True)

@complete_order.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    msg = Market.complete_order(event,arg.extract_plain_text().strip())
    await complete_order.finish(msg)

# 我的道具
my_props = on_command("我的道具", aliases = {"我的仓库"}, priority = 20, block = True)

@my_props.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    msg = Account.my_props(event, arg.extract_plain_text().strip())
    await my_props.finish(msg)


# 设置背景图片
add_BG_image = on_command("设置背景图片", aliases = {"add_BG"}, priority = 20, block = True)

@add_BG_image.handle()
async def _(event:MessageEvent):
    msg = await Manager.add_BG_image(event)
    await add_BG_image.finish(msg, at_sender = True)

# 删除背景图片
del_BG_image = on_command("删除背景图片", aliases = {"del_BG"}, priority = 20, block = True)

@del_BG_image.handle()
async def _(event:MessageEvent):
    msg = await Manager.del_BG_image(event)
    await del_BG_image.finish(msg, at_sender = True)

# 查看排行榜
russian_rank = on_regex(
    r"^(总金币|总资产|金币|资产|财富|胜率|胜场|败场|路灯挂件)(排行|榜)",
    priority = 20,
    block = True
    )

@russian_rank.handle()
async def _(event:MessageEvent):
    cmd = event.get_plaintext().strip().split()
    title = re.search(r"^(总金币|总资产|金币|资产|财富|胜率|胜场|败场|路灯挂件)(排行|榜)",cmd[0]).group(1)
    msg = await Account.group_rank(event, title)
    await russian_rank.finish(msg)

# 查看总排行
russian_All_rank = on_regex(
    r"^(金币|资产|财富|胜率|胜场|败场|路灯挂件)(总排行|总榜)",
    priority = 20,
    block = True
    )

@russian_All_rank.handle()
async def _(bot:Bot, event:MessageEvent):
    cmd = event.get_plaintext().strip().split()
    title = re.search(r"^(金币|资产|财富|胜率|胜场|败场|路灯挂件)(总排行|总榜)",cmd[0]).group(1)
    msg = await Account.All_rank(event, title)
    await russian_All_rank.finish(msg)

# 公司上市
Market_public = on_command(
    "市场注册",
    aliases = {"公司注册","注册公司"},
    rule = to_me(),
    permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
    priority = 20,
    block = True
    )

@Market_public.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg()):
    company_name = arg.extract_plain_text().strip()
    msg = Market.public(event,company_name)
    await Market_public.finish(msg)

# 公司重命名
Market_rename = on_command(
    "公司重命名",
    rule = to_me(),
    permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
    priority = 20,
    block = True
    )

@Market_rename.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg()):
    company_name = arg.extract_plain_text().strip()
    msg = Market.rename(event,company_name)
    await Market_rename.finish(msg)

def arg_check(msg:list):
    l = len(msg)
    if l > 1:
        if msg[1].isdigit():
            count = int(msg[1])
            company_name = msg[0]
        elif msg[0].isdigit():
            count = int(msg[0])
            company_name = msg[1]
        else:
            return None
        limit = None
        if l == 3:
            try:
                limit = float(msg[2])
            except:
                pass
    else:
        return None
    if count > 0:
        return count,company_name,limit
    else:
        return None

# 发行购买
Market_buy = on_command("购买", aliases = {"发行购买"}, priority = 20, block = True)

@Market_buy.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    info = arg_check(msg)
    if not info:
        return
    msg = Market.buy(event,*info)
    await Market_buy.finish(msg)

# 官方结算
Market_settle = on_command("结算", aliases = {"官方结算"}, priority = 20, block = True)

@Market_settle.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    info = arg_check(msg)
    if not info:
        return
    msg = Market.settle(event,*info)
    await Market_settle.finish(msg)

# 市场购买
Exchange_buy = on_command("市场购买", priority = 20, block = True)

@Exchange_buy.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    info = arg_check(msg)
    if not info:
        return
    else:
        buy = info[0]
        company_name = info[1]
    msg = Market.Exchange_buy(event,buy,company_name)
    await Exchange_buy.finish(msg)

# 市场出售
Exchange_sell = on_command("出售", aliases = {"市场出售", "卖出", "上架", "发布交易信息"}, priority = 20, block = True)

@Exchange_sell.handle()
async def _(matcher:Matcher, event:MessageEvent, arg:Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    if msg and (company_id := company_index.get(msg[0])):
        if len(msg) == 3:
            if msg[1].isdigit():
                quote = msg[2]
                n = int(msg[1])
            elif msg[2].isdigit():
                quote = (msg[1])
                n = int(msg[2])
            else:
                await Exchange_sell.finish()
            try:
                quote = float(quote)
            except:
                await Exchange_sell.finish()
            info = (company_id, ExchangeInfo(quote = quote, n = n))
            msg = Market.Exchange_sell(event,info)
            await Exchange_sell.finish(msg)
        else:
            matcher.set_arg("company_id", company_id)
    else:
        await Exchange_sell.finish()

@Exchange_sell.got("info", prompt = "请输入出售数量和单价，用空格隔开。")
async def _(matcher:Matcher, event:MessageEvent, info:Message = Arg()):
    info = info.extract_plain_text().strip().split()
    if len(info) == 2 and info[0].isdigit():
        n = int(info[0])
    elif info[0] == "取消":
        await Exchange_sell.finish()
    else:
        await Exchange_sell.reject("格式错误，请重新输入正确格式或输入【取消】中止对话。")
    try:
        quote = float(info[1])
    except:
        await Exchange_sell.reject("格式错误，请重新输入正确格式或输入【取消】中止对话。")
    company_id = matcher.get_arg("company_id")
    info = (company_id, ExchangeInfo(quote = quote, n = n))
    msg = Market.Exchange_sell(event,info)
    await Exchange_sell.finish(msg)

# 群资料卡
group_info = on_command("群资料卡", priority = 20, block = True)

@group_info.handle()
async def _(bot:Bot, event:MessageEvent, arg:Message = CommandArg()):
    group_id = arg.extract_plain_text().strip()
    if group_id.isdigit():
        group_id = int(group_id)
    elif isinstance(event,GroupMessageEvent):
        group_id = event.group_id
    else:
        return
    msg = await Market.group_info(bot,event,group_id)
    await group_info.finish(msg)

# 市场信息
Market_info = on_command("市场信息",aliases={"查看市场"}, priority = 20, block = True)

@Market_info.handle()
async def _(bot:Bot, event:MessageEvent, arg:Message = CommandArg()):
    company_name = arg.extract_plain_text().strip()
    if company_name:
        if company_name in company_index:
            company_id = company_index[company_name]
            msg = await Market.group_info(bot,event,company_id)
        else:
            msg = f"没有 {company_name} 的注册信息"
        await Market_info.finish(msg)
    else:
        if msg := Market.Market_info_All():
            await Market_info.finish(msg)
        else:
            await Market_info.finish("市场为空")

# 市场价格表
Market_pricelist = on_command("市场价格表",aliases={"股票价格表"}, priority = 20, block = True)

@Market_pricelist.handle()
async def _(event:MessageEvent):
    msg = Market.pricelist(event.user_id)
    await Market_pricelist.finish(msg)

# 更新公司简介
update_intro = on_command(
    "更新公司简介",
    aliases = {"添加公司简介", "修改公司简介"},
    permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
    priority = 20,
    block = True
    )

@update_intro.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg()):
    intro = arg.extract_plain_text().strip()
    msg = Market.update_intro(str(event.group_id), intro)
    await group_info.finish(msg)

# 管理公司简介
update_intro_superuser = on_command("管理公司简介", permission = SUPERUSER, priority = 20, block = True)

@update_intro_superuser.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split(" ",1)
    if len(msg) == 2:
        msg = Market.update_intro(msg[0], msg[1])
        await update_intro_superuser.finish(msg)

# 跨群转移金币到自己的账户
transfer_gold = on_command("金币转移", priority = 20, block = True)

@transfer_gold.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    info = arg_check(msg)
    if not info:
        return
    else:
        gold = info[0]
        company_name = info[1]
    msg = Account.intergroup_transfer_gold(event,gold,company_name)
    await transfer_gold.finish(msg, at_sender = True)

# 冻结个人资产
freeze = on_command("冻结资产", permission = SUPERUSER, priority = 20, block = True)

@freeze.handle()
async def _(bot:Bot, event:MessageEvent, matcher:Matcher, arg:Message = CommandArg()):
    at = get_message_at(event.message)
    if at:
        at = at[0]
    elif (at := arg.extract_plain_text().strip()) and at.isdigit():
        at = int(at)
        if at not in data.user:
            await freeze.finish(f"用户 {at} 不存在。")
    else:
        await freeze.finish("没有选择冻结对象。")

    confirm = f"{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}"
    matcher.set_arg("freeze", (int(at),confirm))
    nickname = (await bot.get_group_member_info(group_id = event.group_id, user_id = at))["nickname"]
    await freeze.send(f"您即将冻结 {nickname}（{at}），请输入{confirm}来确认。")

@freeze.got("code")

async def _(event:MessageEvent, matcher:Matcher, code :Message = Arg()):
    at,confirm = matcher.get_arg("freeze")
    if confirm == code.extract_plain_text().split():
        target = Manager.locate_user_at(event, at)
        msg = Account.freeze(target[0])
        await freeze.finish(msg)
    else:
        await freeze.finish("【冻结】已取消。")

# 清理无效账户
delist = on_fullmatch("清理无效账户", rule = to_me(), permission = SUPERUSER, priority = 20, block = True)

@delist.handle()
async def _():
    await delist.send("正在启动清理程序。")
    log = await Account.delist()
    logger.info("\n" + log)
    with open(path / "delist.log","a",encoding = "utf8") as f:
        f.write(
            f"\n{datetime.datetime.fromtimestamp(time.time()).strftime('%Y 年 %m 月 %d 日 %H:%M:%S')}\n"
            "——————————————\n"
            + log + "\n"
            "——————————————\n"
            )
    log = data.verification()
    logger.info(f"\n{log}")
    await delist.finish("清理完成！")

# 市场重置
Market_reset = on_fullmatch("市场重置", permission = SUPERUSER, priority = 20, block = True)

@Market_reset.handle()
async def _():
    Market.reset()
    Market.update()
    await Market_reset.finish("市场已重置。")

# 数据验证
DataVerif = on_command("数据验证", aliases = {"数据校验"},permission = SUPERUSER, priority = 20, block = True)

@DataVerif.handle()
async def _():
    log = data.verification()
    logger.info(f"\n{log}")

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

# 市场更新
@scheduler.scheduled_job("cron", minute = "*/5", misfire_grace_time = 120)
async def _():
    log = Market.update()
    if log:
        logger.info("\n" + log)

# 数据备份
Backup = on_command("Backup", aliases = {"数据备份", "游戏备份"}, permission = SUPERUSER, priority = 20, block = True)

@Backup.handle()
@scheduler.scheduled_job("cron", hour = "*/4", misfire_grace_time = 120)
async def _():
    now = time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(time.time()))
    now = now.split()
    backup_today = backup / now[0]
    if not backup_today.exists():
        backup_today.mkdir()
    data.save()
    shutil.copy(f"{path}/russian_data.json",f"{backup_today}/russian_data {now[1]}.json")
    logger.info(f'russian_data.json 备份成功！')

# 刷新每日
Newday = on_command("Newday", aliases = {"刷新每日", "刷新签到"}, permission = SUPERUSER, priority = 20, block = True)

@Newday.handle()
@scheduler.scheduled_job("cron", hour = 0, misfire_grace_time = 120)
async def _():
    Manager.update_company_index()
    log = data.verification()
    logger.info(f"\n{log}")
    Market.new_order()
    data.Newday()
    with open(path / "Newday.log","a",encoding = "utf8") as f:
        f.write(f"\n{datetime.datetime.fromtimestamp(time.time()).strftime('%Y 年 %m 月 %d 日 %H:%M:%S')}\n"
                "——————————————\n"
                f"{log}\n"
                "——————————————\n")
    folders = [f for f in backup.iterdir() if f.is_dir()]
    for folder in folders:
        if time.time() - folder.stat().st_ctime > 604800:
            shutil.rmtree(folder)
            logger.info(f'备份 {folder} 已删除！')

# 保存数据
DataSave = on_command("DataSave", aliases = {"保存数据", "保存游戏"},permission = SUPERUSER, priority = 20, block = True)

@DataSave.handle()
@scheduler.scheduled_job("cron", minute = "*/10", misfire_grace_time = 120)
async def _():
    data.save()
    with open(Market.market_history_file, "w", encoding = "utf8") as f:
        json.dump(Market.market_history, f, ensure_ascii = False, indent = 4)
    logger.info(f'游戏数据已保存！！')