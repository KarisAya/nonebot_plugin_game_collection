from nonebot.adapters.onebot.v11 import (
    GROUP,
    PRIVATE,
    GROUP_ADMIN,
    GROUP_OWNER,
    Bot,
    MessageEvent,
    GroupMessageEvent,
    Message,
)
from nonebot.permission import SUPERUSER
from nonebot import on_command, on_regex, on_fullmatch
from nonebot.params import CommandArg, Arg
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

from .utils.utils import get_message_at, number
from .data.data import ExchangeInfo
from .config import revolt_cd, bet_gold, path, backup
from .Manager import data, company_index

from . import Manager
from . import Account
from . import Market
from . import Game
from . import Prop


try:
    from nonebot.plugin import PluginMetadata
    from .data.data import menu_data
    __plugin_meta__ = PluginMetadata(
        name = "小游戏合集",
        description = "各种群内小游戏",
        usage = "",
        extra = {
            'menu_data':menu_data,
            'menu_template':'default'
            }
        )
except ModuleNotFoundError:
    logger.info("当前nonebot版本无法使用插件元数据。")    

scheduler = require("nonebot_plugin_apscheduler").scheduler


# 赛马创建
RaceNew = on_command("赛马创建", aliases = {"创建赛马"}, permission = GROUP, priority = 20, block = True)

@RaceNew.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg()):
    gold = arg.extract_plain_text().strip()
    if gold.isdigit():
        gold = int(gold)
    else:
        gold = bet_gold
    msg =  Game.RaceNew(event, gold)
    await sign.finish(msg, at_sender = True)

# 赛马加入
RaceJoin = on_command("赛马加入", aliases = {"加入赛马"}, permission = GROUP, priority = 20, block = True)

@RaceJoin.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg()):
    msg =  Game.RaceJoin(event, arg.extract_plain_text().strip())
    await RaceJoin.finish(msg, at_sender = True)

# 赛马开始
RaceStart = on_command("赛马开始", aliases = {"开始赛马"}, permission = GROUP, priority = 20, block = True)
@RaceStart.handle()
async def _(bot:Bot, event:GroupMessageEvent):
    msg = await Game.RaceStart(bot, event)
    await RaceStart.finish(msg)

# 赛马重置
RaceReStart = on_command(
    "赛马重置",
    aliases = {"重置赛马"},
    rule = lambda event:event.group_id in current_games and current_games[event.group_id].info.get("game") == "horse race",
    permission = GROUP,
    priority = 20,
    block = True
    )

@RaceReStart.handle()

async def _(event:GroupMessageEvent):
    msg =  Game.RaceReStart(event)
    await RaceReStart.finish(msg)

# 赛马暂停
RaceStop = on_command(
    "赛马暂停",
    aliases = {"暂停赛马"},
    rule = lambda event:isinstance(event,GroupMessageEvent) and event.group_id in current_games and current_games[event.group_id].info.get("game") == "horse race",
    permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
    priority = 20,
    block = True
    )

@RaceStop.handle()
async def _(event:GroupMessageEvent):
    global current_games
    current_games[event.group_id].info["race_group"].start = 2

# GameClear
GameClear = on_command(
    "GameClear",
    aliases = {"清除游戏", "清除对局", "清除对决"},
    rule = lambda event:isinstance(event,GroupMessageEvent) and event.group_id in current_games,
    permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
    priority = 20,
    block = True
    )

@GameClear.handle()
async def _(event:GroupMessageEvent):
    global current_games
    del current_games[event.group_id]

# 获取金币
gold_create = on_command("获取金币", permission = SUPERUSER, priority = 20, block = True)

@gold_create.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    gold = arg.extract_plain_text().strip()
    if gold.isdigit():
        gold = int(gold)
    else:
        gold = 0
    msg =  Account.gold_create(event,gold)
    await gold_create.finish(msg, at_sender=True)

# 获取道具
props_create = on_command("获取道具", permission = SUPERUSER, priority = 20, block = True)

@props_create.handle()
async def _(event:MessageEvent, arg:Message = CommandArg(),):
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

    msg = Account.props_create(event, prop_name, count)
    await give_props.finish(msg, at_sender = True)

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
    target = await Manager.locate_user_at(bot, event, at)
    msg = Account.transfer_gold(event, target, gold)
    await give_gold.finish(msg, at_sender = True)

# 送道具
give_props = on_command("送道具", aliases = {"赠送道具"}, permission = GROUP, priority = 20, block = True)

@give_props.handle()
async def _(bot:Bot, event:GroupMessageEvent, arg:Message = CommandArg(),):
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

    target = await Manager.locate_user_at(bot, event, int(at))
    msg = Account.transfer_props(event, target, prop_name, count)
    await give_props.finish(msg, at_sender = True)

from .Game import current_games

# 俄罗斯轮盘
russian = on_command("俄罗斯轮盘", aliases={"装弹", "俄罗斯转盘"}, permission = GROUP, priority = 20, block = True)

@russian.handle()
async def _(bot:Bot, event:GroupMessageEvent, arg:Message = CommandArg()):
    if not (msg := arg.extract_plain_text().strip().split()):
        bullet_num = 1
        gold = bet_gold
    if len(msg) == 1:
        msg = msg[0]
        if not msg.isdigit():
            return
        if 0 < (msg := int(msg)) < 7:
            bullet_num = msg
            gold = bet_gold
        else:
            bullet_num = 1
            gold = int(msg)
    else:
        if not (msg[0].isdigit() and msg[1].isdigit()):
            return
        bullet_num = int(msg[0])
        gold = int(msg[1])
        if 0 < bullet_num < 7:
            pass
        elif 0 < gold < 7:
            bullet_num ,gold = gold, bullet_num
        else:
            return
    msg = Game.russian(event,bullet_num,gold)
    await russian.finish(msg)

# 开枪
russian_shot = on_command(
    "开枪",
    aliases = {"咔", "嘭", "嘣"},
    rule = lambda event:event.group_id in current_games and current_games[event.group_id].info.get("game") == "russian",
    permission = GROUP,
    priority = 20,
    block = True
    )

@russian_shot.handle()
async def _(bot:Bot, event:GroupMessageEvent, arg:Message = CommandArg()):
    count = arg.extract_plain_text().strip()
    if count.isdigit():
        count = int(count)
    else:
        count = 1
    msg = await Game.russian_shot(bot, event, count)
    await russian_shot.finish(msg)

# 掷色子
dice = on_command("掷色子", aliases={"摇色子", "掷骰子", "摇骰子"}, permission = GROUP, priority = 20, block = True)

@dice.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg()):
    gold = arg.extract_plain_text().strip()
    if gold.isdigit():
        gold = int(gold)
    else:
        gold = bet_gold
    msg = Game.dice(event, gold)
    await dice.finish(msg)

# 开数
dice_open = on_command(
    "取出",
    aliases={"开数", "开点"},
    rule = lambda event:event.group_id in current_games and current_games[event.group_id].info.get("game") == "dice",
    permission = GROUP,
    priority = 20,
    block = True
    )
@dice_open.handle() 
async def _(bot:Bot, event:GroupMessageEvent):
    msg = await Game.dice_open(bot, event)
    await dice_open.finish(msg)

# 扑克对战
poker = on_command("扑克对战",aliases={"扑克对决", "扑克决斗"}, permission = GROUP, priority = 20, block = True)

@poker.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg()):
    gold = arg.extract_plain_text().strip()
    if gold.isdigit():
        gold = int(gold)
    else:
        gold = bet_gold
    msg = Game.poker(event, gold)
    await poker.finish(msg)

# 出牌
poker_play = on_command(
    "出牌",
    rule = lambda event:event.group_id in current_games and current_games[event.group_id].info.get("game") == "poker",
    permission = GROUP,
    priority = 20,
    block = True
    )

@poker_play.handle()
async def _(bot:Bot, event:GroupMessageEvent, arg:Message = CommandArg()):
    msg = await Game.poker_play(bot, event, arg.extract_plain_text())
    await poker_play.finish(msg)

# 猜数字
lucky_number = on_command("猜数字", permission = GROUP, priority = 20, block = True)

@lucky_number.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg()):
    gold = arg.extract_plain_text().strip()
    if gold.isdigit():
        gold = int(gold)
    else:
        gold = int(bet_gold/10)
    msg = Game.lucky_number(event, gold)
    await lucky_number.finish(msg)

# 报数
guess_number = on_regex(
    r"^\d{1,3}$",
    rule = lambda event:event.group_id in current_games and current_games[event.group_id].info.get("game") == "lucky_number",
    permission = GROUP,
    priority = 20,
    block = True
    )

@guess_number.handle()
async def _(bot:Bot, event:GroupMessageEvent):
    msg = await Game.guess_number(bot, event, int(event.get_plaintext()))
    await guess_number.finish(msg)

# 港式五张
cantrell = on_command("同花顺", aliases = {"五张牌","港式五张","梭哈"}, permission = GROUP, priority = 20, block = True)

@cantrell.handle()
async def _(event:GroupMessageEvent, arg:Message = CommandArg()):
    arg = arg.extract_plain_text().strip().split()
    if not arg:
        gold = bet_gold
        times = 1
    else:
        test = len(arg)
        if test == 1:
            gold = arg[0]
            if gold.isdigit():
                gold = int(arg)
            else:
                gold = bet_gold
            times = 1
        else:
            gold = arg[0]
            if gold.isdigit():
                gold = int(gold)
            else:
                gold = bet_gold
            times = arg[1]
            if gold.isdigit():
                times = int(times)
            else:
                times = 1

    msg = Game.cantrell(event, gold, times)
    await cantrell.finish(msg)

# 看牌
cantrell_check = on_command(
    "看牌",
    rule = lambda event:event.group_id in current_games and current_games[event.group_id].info.get("game") == "cantrell",
    permission = GROUP,
    priority = 20,
    block = True
    )

@cantrell_check.handle()
async def _(bot:Bot, event:GroupMessageEvent):
    msg = await Game.cantrell_check(bot, event)
    await cantrell_check.finish(msg)

# 加注
cantrell_play = on_command(
    "加注",
    aliases = {"跟注","开牌"},
    rule = lambda event:event.group_id in current_games and current_games[event.group_id].info.get("game") == "cantrell",
    permission = GROUP,
    priority = 20,
    block = True
    )

@cantrell_play.handle()
async def _(bot:Bot, event:GroupMessageEvent, arg:Message = CommandArg()):
    gold = arg.extract_plain_text().strip()
    if gold.isdigit():
        gold = int(gold)
    else:
        gold =  current_games[event.group_id].info["round_gold"]
    msg = await Game.cantrell_play(bot, event, gold)
    await cantrell_play.finish(msg)

# 随机对战
random_game = on_command("随机对战", permission = GROUP, priority = 5, block = True)

@random_game.handle()
async def _(bot:Bot, event:GroupMessageEvent, arg:Message = CommandArg()):
    gold = arg.extract_plain_text().strip()
    if gold.isdigit():
        gold = int(gold)
    else:
        gold = -1
    msg = Game.random_game(event, gold)
    await random_game.finish(msg)

async def session_check(event:GroupMessageEvent):
    """
    本群有对局
    """
    return event.group_id in current_games

# 接受挑战
accept = on_command("接受挑战", aliases = {"接受决斗", "接受对决"}, rule = session_check, permission = GROUP, priority = 20, block = True)

@accept.handle()
async def _(event:GroupMessageEvent):
    msg = Game.accept(event)
    await accept.finish(msg)

# 拒绝挑战
refuse = on_command("拒绝挑战", aliases={"拒绝决斗", "拒绝对决"}, rule = session_check, permission = GROUP, priority = 20, block = True)

@refuse.handle()
async def _(event:GroupMessageEvent):
    msg = Game.refuse(event)
    await refuse.finish(msg)

# 超时结算
overtime = on_command("超时结算", rule = session_check, permission = GROUP, priority = 20, block = True)

@overtime.handle()
async def _(bot:Bot, event:GroupMessageEvent):
    msg = await Game.overtime(event)
    await overtime.finish(msg)

# 认输结算
fold = on_fullmatch(("认输", "投降", "结束"), rule = session_check, permission = GROUP, priority = 20, block = True)

@fold.handle()
async def _(bot:Bot, event:GroupMessageEvent):
    await Game.fold(bot, event)

# 幸运花色
slot = on_command("幸运花色", aliases = {"抽花色"}, permission = PRIVATE, priority = 20, block = True)

@slot.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    gold = arg.extract_plain_text().strip()
    if gold.isdigit():
        gold = int(gold)
    else:
        gold = bet_gold
    msg = Game.slot(event, gold)
    await slot.finish(msg, at_sender=True)

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
    if len(msg) == 1:
        prop_name = msg[0]
        count = 1
    elif len(msg) == 2 and msg[1].isdigit():
        prop_name = msg[0]
        count = int(msg[1])
    else:
        return
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

# 我的道具
my_props = on_command("我的道具", aliases = {"我的仓库"}, priority = 20, block = True)

@my_props.handle()
async def _(event:MessageEvent):
    msg = Account.my_props(event)
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
    r"^(总金币|总资产|金币|资产|财富|胜率|胜场|败场|路灯)(排行|榜)",
    permission = GROUP,
    priority = 20,
    block = True
    )

@russian_rank.handle()
async def _(event:GroupMessageEvent):
    cmd = event.get_plaintext().strip().split()
    title = re.search(r"^(总金币|总资产|金币|资产|财富|胜率|胜场|败场|路灯)(排行|榜)",cmd[0]).group(1)
    msg = Manager.group_rank(event.group_id, title)
    await russian_rank.finish(msg)

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

def arg_check(msg:str):
    if len(msg) == 2:
        if msg[0].isdigit():
            count = int(msg[0])
            company_name = msg[1]
        elif msg[1].isdigit():
            count = int(msg[1])
            company_name = msg[0]
        else:
            return None
    else:
        return None
    if count > 0:
        return count,company_name
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
    else:
        buy, company_name = info
    msg = Market.buy(event,buy,company_name)
    await Market_buy.finish(msg)

# 官方结算
Market_settle = on_command("结算", aliases = {"官方结算"}, priority = 20, block = True)

@Market_settle.handle()
async def _(event:MessageEvent, arg:Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    info = arg_check(msg)
    if not info:
        return
    else:
        settle, company_name = info
    msg = Market.settle(event,settle,company_name)
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
        buy, company_name = info
    msg = Market.Exchange_buy(event,buy,company_name)
    await Exchange_buy.finish(msg)

# 市场出售
Exchange_sell = on_command("出售", aliases = {"市场出售", "发布交易信息"}, priority = 20, block = True)

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
    if len(info) == 2 and info[1].isdigit():
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
Market_info_0 = on_command("市场信息",aliases={"查看市场"}, priority = 20, block = True)

@Market_info_0.handle()
async def _(bot:Bot, event:MessageEvent, arg:Message = CommandArg()):
    company_name = arg.extract_plain_text().strip()
    if company_name:
        if company_name in company_index:
            company_id = company_index[company_name]
            msg = await Market.group_info(bot,event,company_id)
        else:
            msg = f"没有 {company_name} 的注册信息"
        await Market_info_0.send(msg)
    else:
        if msg := Market.Market_info_All(event,False):
            if len(msg) == 1:
                await Market_info_0.send(msg[0]["data"]["content"])
            elif isinstance(event, GroupMessageEvent):
                await bot.send_group_forward_msg(group_id = event.group_id, messages = msg)
            else:
                await bot.send_private_forward_msg(user_id = event.user_id, messages = msg)
        else:
            await Market_info_0.send("市场为空")

#Market_info_1 = on_command("市场行情",aliases={"市场走势"}, priority = 20, block = True)

#@Market_info_1.handle()
#async def _(bot:Bot, event:MessageEvent, arg:Message = CommandArg()):
#    msg = Market.Market_info_All(event,True)
#    await Market_info_1.finish(msg)

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
        gold, company_name = info
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

    confirm = random.randint(1000,9999)
    matcher.set_arg("freeze", (int(at),str(confirm)))
    nickname = (await bot.get_group_member_info(group_id = event.group_id, user_id = at))["nickname"]
    await freeze.send(f"您即将冻结 {nickname}（{at}），请输入{confirm}来确认。")

@freeze.got("code")

async def _(bot:Bot, event:MessageEvent, matcher:Matcher, code :Message = Arg()):
    at,confirm = matcher.get_arg("freeze")
    if confirm == str(code):
        target = await Manager.locate_user_at(bot, event, at)
        msg = Account.freeze(target[0])
        await freeze.finish(msg)
    else:
        await freeze.finish("【冻结】已取消。")

# 清理无效账户
delist = on_command("清理无效账户", rule = to_me(), permission = SUPERUSER, priority = 20, block = True)

@delist.handle()
async def _(bot:Bot):
    await delist.send("正在启动清理程序。")
    log = await Account.delist(bot)
    logger.info("\n" + log)
    with open(path / "delist.log","a",encoding = "utf8") as f:
        f.write(
            f"\n{datetime.datetime.fromtimestamp(time.time()).strftime('%Y 年 %m 月 %d 日 %H:%M:%S')}\n"
            "——————————————\n"
            + log + "\n"
            "——————————————\n"
            )
    await delist.finish("清理完成！")

# 股市更新
@scheduler.scheduled_job("cron", minute = "0,*/5")
async def _():
    log = Market.update()
    if log:
        logger.info("\n" + log)

# 市场指数更新和数据备份
Backup = on_command("Backup", aliases = {"数据备份", "游戏备份"}, permission = SUPERUSER, priority = 20, block = True)

@Backup.handle()
@scheduler.scheduled_job("cron", hour = "0,*/4")
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
@scheduler.scheduled_job("cron", hour = 0)
async def _():
    log = Manager.Newday()
    logger.info("\n" + log)
    with open(path / "Newday.log","a",encoding = "utf8") as f:
        f.write(
            f"\n{datetime.datetime.fromtimestamp(time.time()).strftime('%Y 年 %m 月 %d 日 %H:%M:%S')}\n"
            "——————————————\n"
            + log + "\n"
            "——————————————\n"
            )

    folders = [f for f in backup.iterdir() if f.is_dir()]
    for folder in folders:
        if time.time() - folder.stat().st_ctime > 604800:
            folder.unlink(True)
            logger.info(f'备份 {folder} 已删除！')

# 保存数据
DataSave = on_command("DataSave", aliases = {"保存数据", "保存游戏"},permission = SUPERUSER, priority = 20, block = True)

@DataSave.handle()
@scheduler.scheduled_job("cron", minute = "0,*/10")
async def _():
    data.save()
    with open(Market.market_history_file, "w", encoding = "utf8") as f:
        json.dump(Market.market_history, f, ensure_ascii = False, indent = 4)
    logger.info(f'游戏数据已保存！！')