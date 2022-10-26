from nonebot import on_command, on_fullmatch, require
from nonebot.adapters.onebot.v11 import (
    GROUP,
    GROUP_ADMIN,
    GROUP_OWNER,
    PRIVATE,
    Bot,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    Message,
    MessageSegment
)
from nonebot.internal.adapter import Bot as BaseBot
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.log import logger
from nonebot.permission import SUPERUSER

import math
import time
import asyncio
import random

import shutil
import os

from .utils import is_number, get_message_at, text_to_png
from .data_source import (
    bot_name,
    russian_manager,
    market_manager,
    max_bet_gold,
    race_bet_gold,
    russian_path,
    cache
    )
from .data_source import constant_props
from .utils import company_info_Splicing

from .start import *
from .race_group import race_group
from .setting import  *

scheduler = require("nonebot_plugin_apscheduler").scheduler

data_file = russian_path / "data" / "russian"
if not data_file.exists():
    data_file.mkdir(exist_ok=True, parents=True)

#开场加载

events_list = []

driver = get_driver()
@driver.on_startup
async def events_read():
    global events_list
    events_list = await load_dlcs()
    market_manager.reset_market_index()



RaceNew = on_command("赛马创建",aliases = {"创建赛马"}, permission=GROUP, priority=5, block=True)
RaceJoin = on_command("赛马加入",aliases = {"加入赛马"}, permission=GROUP, priority=5, block=True)
RaceStart = on_command("赛马开始",aliases = {"开始赛马"}, permission=GROUP, priority=5, block=True)
RaceReStart = on_command("赛马重置",aliases = {"重置赛马"}, permission=GROUP, priority=5, block=True)
RaceStop = on_command("赛马暂停",aliases = {"暂停赛马"}, permission=SUPERUSER, priority=5, block=True)
RaceClear = on_command("赛马清空",aliases = {"清空赛马"}, permission=SUPERUSER, priority=5, block=True)
RaceReload = on_command("赛马事件重载", permission=SUPERUSER, priority=5, block=True)

race = {}

@RaceNew.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    global race
    group = event.group_id
    try:
        if race[group].start == 0 and time.time() - race[group].time < 300:
            out_msg = (
                f'> 创建赛马比赛失败!\n'
                f'> 原因:{bot_name}正在打扫赛马场...\n'
                f'> 解决方案:等{bot_name}打扫完...\n'
                f'> 可以在{str(round(setting_over_time - time.time() + race[group].time),2)}秒后输入 赛马重置'
                )
            await RaceNew.finish(out_msg)
        elif race[group].start == 1:
            await RaceNew.finish(f"一场赛马正在进行中")
            await RaceNew.finish()
    except KeyError:
        pass

    race[group] = race_group()
    await RaceNew.finish(f'> 创建赛马比赛成功！\n> 输入 [赛马加入 + 名字] 即可加入赛马。')

@RaceJoin.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    global race, max_player
    msg = arg.extract_plain_text().strip()

    group = event.group_id
    uid = event.user_id

    gold = russian_manager.get_user_data(event)["gold"]

    player_name = event.sender.card if event.sender.card else event.sender.nickname

    if gold < race_bet_gold:
        await RaceJoin.finish(f'报名赛马需要{race_bet_gold}金币，你的金币：{gold}。', at_sender=True)
    else:
        pass

    try:
        race[group]
    except KeyError:
        await RaceJoin.finish( f"赛马活动未开始，请输入 [赛马创建] 开场")
    try:
        if race[group].start == 1 or race[group].start == 2:
            await RaceJoin.finish()
    except KeyError:
        await RaceJoin.finish()
    if race[group].query_of_player() >= max_player:
        await RaceJoin.finish( f"> 加入失败\n> 原因:赛马场就那么大，满了满了！" )
    if race[group].is_player_in(uid) == True:
        await RaceJoin.finish( f"> 加入失败\n> 原因:您已经加入了赛马场!")
    if msg:
        if len(msg) > 5:
            horse_name = msg[:2]+"酱"
        else:
            horse_name = msg

        race[group].add_player(horse_name, uid, player_name)
        
        russian_manager._player_data[str(group)][str(uid)]["gold"] -= race_bet_gold
        russian_manager.save()

        out_msg = (
            '\n> 加入赛马成功\n'
            '> 赌上马儿性命的一战即将开始!\n'
            f'> 赛马场位置:{str(race[group].query_of_player())}/{str(max_player)}'
            )
        await RaceJoin.finish(out_msg, at_sender=True)
    else:
        await RaceJoin.finish(f"请输入你的马儿名字", at_sender=True)

@RaceStart.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    global race
    global events_list
    group = event.group_id
    try:
        if race[group].query_of_player() == 0:
            await RaceStart.finish()
    except KeyError:
        await RaceStart.finish()
    try:
        if race[group].start == 0 or race[group].start == 2:
            if len(race[group].player) >= min_player:
                race[group].start_change(1)
            else:
                await RaceStart.finish(
                    f'> 开始失败\n'
                    f'> 原因:赛马开局需要最少{str(min_player)}人参与',
                    at_sender=True
                    )
        elif race[group].start == 1:
            await RaceStart.finish()
    except KeyError:
        await RaceStart.finish()
    race[group].time = time.time()

    await RaceStart.send(
        f'> 比赛开始\n'
        f'> 当前奖金：{len(race[group].player) * race_bet_gold}金币'
        )
    await asyncio.sleep(0.5)

    while race[group].start == 1:
        # 回合数+1
        race[group].round_add()
        #移除超时buff
        race[group].del_buff_overtime()
        #马儿全名计算
        race[group].fullname()
        #回合事件计算
        text = race[group].event_start(events_list)
        #马儿移动
        race[group].move()
        #场地显示
        display = race[group].display()

        logger.info(f'事件输出:{text}\n{display}')
        
        output = text_to_png(display)

        try:
            await RaceStart.send(Message(text) + MessageSegment.image(output))
        except:
            text = ""
            await RaceStart.send(MessageSegment.image(output))

        if text:
            await asyncio.sleep(0.5 + int(0.06 * len(text)))
        else:
            await asyncio.sleep(0.5)
            
        #全员失败计算
        if race[group].is_die_all():
            for x in race[group].player:
                uid = x.playeruid
                if uid > 10:
                    russian_manager._player_data[str(group)][str(uid)]["gold"] += race_bet_gold
            else:
                russian_manager.save()
                del race[group]

            await RaceStart.finish("比赛已结束，鉴定为无马生还")
        #全员胜利计算
        winer = race[group].is_win_all()
        winer_list="\n"
        if winer != []:
            await RaceStart.send(
                f'> 比赛结束\n'
                f'> {bot_name}正在为您生成战报...'
                ) 
            await asyncio.sleep(1)
            gold = int(race_bet_gold * len(race[group].player) / len(winer))
            for x in winer:
                uid = x[1]
                winer_list += "> "+ x[0] + "\n"
                if uid > 10:
                    russian_manager._player_data[str(group)][str(uid)]["gold"] += gold
            else:
                russian_manager.save()
                del race[group]

            msg = f"> 比赛已结束，胜者为：{winer_list}> 本次奖金：{gold} 金币"
            await RaceStart.finish(msg)

        await asyncio.sleep(1)

@RaceReStart.handle()
async def _(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    global race
    group = event.group_id
    time_key = math.ceil(time.time() - race[group].time)
    if time_key >= setting_over_time:
        for x in race[group].player:
            uid = x.playeruid
            if uid > 10:
                russian_manager._player_data[str(group)][str(uid)]["gold"] += race_bet_gold
        else:
            russian_manager.save()
            del race[group]

        await RaceReStart.finish(f'超时{str(setting_over_time)}秒，已重置赛马场')
    await RaceReStart.finish(f'未超时{str(setting_over_time)}秒，目前为{str(time_key)}秒，未重置')

@RaceStop.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    global race
    group = event.group_id
    race[group].start_change(2)

@RaceClear.handle()
async def _(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    global race
    group = event.group_id
    for x in race[group].player:
        uid = x.playeruid
        if uid > 10:
            russian_manager._player_data[str(group)][str(uid)]["gold"] += race_bet_gold
    else:
        russian_manager.save()
        del race[group]

@RaceReload.handle()
async def _(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    global events_list
    logs = f""
    files = os.listdir(os.path.dirname(__file__) + '/events/horserace')
    for file in files:
        try:
            with open(f'{os.path.dirname(__file__)}/events/horserace/{file}', "r", encoding="utf-8") as f:
                logger.info(f'加载事件文件：{file}')
                events = deal_events(json.load(f))
                events_list.extend(events)
            logger.info(f"加载 {file} 成功")
            logs += f'加载 {file} 成功\n'
        except:
            logger.info(f"加载 {file} 失败！失败！失败！")
            logs += f"加载 {file} 失败！失败！失败！\n"
    await RaceReload.finish(logs)



# 金币签到
sign = on_command("金币签到",aliases={"轮盘签到"}, permission=GROUP, priority=5, block=True)

@sign.handle()
async def _(event: GroupMessageEvent):
    msg, gold = russian_manager.sign(event)
    await sign.send(msg, at_sender=True)
    if gold != -1:
        logger.info(f"USER {event.user_id} | GROUP {event.group_id} 获取 {gold} 金币")

# 发动革命
revolt = on_command("发起重置", aliases={"发起revolt","发动revolt", "revolution", "Revolution"},permission=GROUP, priority=5, block=True)

@revolt.handle()
async def _(event: GroupMessageEvent):
    msg=russian_manager.revlot(event.group_id)
    if msg:
        await revolt.finish(msg)
    else:
        await revolt.finish()
# 重置签到
revolt_sign = on_command("重置签到",aliases={"revolt签到"},permission=GROUP, priority=5, block=True)

@revolt_sign.handle()
async def _(event: GroupMessageEvent):
    msg, gold = russian_manager.revolt_sign(event)
    await sign.send(msg, at_sender=True)
    if gold != -1:
        logger.info(f"USER {event.user_id} | GROUP {event.group_id} 获取 {gold} 金币")

# 发红包
give_gold = on_command("打钱", aliases={"发红包", "赠送金币"},permission=GROUP, priority=5, block=True)

@give_gold.handle()
async def _(bot: Bot,event: GroupMessageEvent,arg: Message = CommandArg(),):
    msg = arg.extract_plain_text().strip()
    if msg:
        msg = msg.split()
        if len(msg) == 1:
            msg = msg[0]
            if is_number(msg):
                unsettled = abs(int(msg))
                player_id = event.user_id
                at_player_id = get_message_at(event.json())
                if at_player_id:
                    at_player_id = at_player_id[0]
                    if unsettled > russian_manager.get_user_data(event)["gold"]:
                        await give_gold.finish("您的账户没有足够的金币", at_sender=True)
                    else:
                        await russian_manager._init_at_player_data(bot,event,at_player_id)
                        msg = russian_manager.transfer_accounts(event, at_player_id, unsettled)
                        await give_gold.finish(msg)

# 送道具
give_props = on_command("送道具", aliases={"赠送道具"},permission=GROUP, priority=5, block=True)

@give_props.handle()
async def _(bot: Bot,event: GroupMessageEvent,arg: Message = CommandArg(),):
    msg = arg.extract_plain_text().strip()
    if msg:
        msg = msg.split()
        at_player_id = get_message_at(event.json())
        if at_player_id:
            at_player_id = at_player_id[0]
            if len(msg) == 1:
                props = msg[0]
                count = 1
            else:
                props = msg[0]
                if is_number(msg[1]):
                    count = abs(int(msg[1])) or 1
                else:
                    count = 1
            russian_manager._init_player_data(event)
            await russian_manager._init_at_player_data(bot,event,at_player_id)
            msg = russian_manager.give_props(event, at_player_id, props, count)
            await give_props.finish(msg, at_sender=True)

# 状态处理
accept = on_command("接受挑战", aliases={"接受决斗", "接受对决"}, permission=GROUP, priority=5, block=True)

@accept.handle()
async def _(event: GroupMessageEvent):
    msg = russian_manager.accept(event) 
    if msg:
        await accept.send(msg)       
    else:
        await accept.finish()

refuse = on_command("拒绝挑战", aliases={"拒绝决斗", "拒绝对决"}, permission=GROUP, priority=5, block=True)

@refuse.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    msg = await russian_manager.refuse(bot, event)
    if msg:
        await refuse.send(msg, at_sender=True)        
    else:
        await refuse.finish()

settlement = on_command("结算", permission=GROUP, priority=5, block=True)

@settlement.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    msg = russian_manager.settlement(event)
    if msg:
        await settlement.send(msg, at_sender=True)
        await russian_manager.end_game(bot, event)
    else:
        await settlement.finish()

fold = on_command("结束", permission=GROUP, priority=5, block=True)

@fold.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await russian_manager.fold(bot, event)

# 俄罗斯轮盘

russian = on_command("俄罗斯轮盘", aliases={"装弹", "俄罗斯转盘"}, permission=GROUP, priority=5, block=True)

@russian.handle()
async def _(bot: Bot,event: GroupMessageEvent, arg: Message = CommandArg()):
    try:
        _msg = await russian_manager.check_current_game(bot, event)
        if _msg:
            await russian.finish(_msg)
    except KeyError:
        pass
    msg = arg.extract_plain_text().strip()
    if msg:
        bullet_num = 1
        money = 200
        msg = msg.split()
        if len(msg) == 1:
            msg = msg[0]
            if is_number(msg) and 0 < int(msg):
                if int(msg) < 7:
                    bullet_num = int(msg)
                else:
                    money = int(msg)
        else:
            msg[0] = msg[0].strip()  
            msg[1] = msg[1].strip()         
            if is_number(msg[0]) and 0 < int(msg[0]) < 7:
                bullet_num = int(msg[0])
            if is_number(msg[1]) and 0 < int(msg[1]):
                money = int(msg[1])

        user_money = russian_manager.get_user_data(event)["gold"]

        if money > max_bet_gold:
            await russian.finish(f"单次金额不能超过{max_bet_gold}", at_sender=True)
        if money > user_money:
            await russian.finish("你没有足够的金币支撑这场挑战", at_sender=True)

        player1_name = event.sender.card or event.sender.nickname
        at_ = get_message_at(event.json())
        if at_:
            at_ = at_[0]
            at_player_name = await bot.get_group_member_info(group_id=event.group_id, user_id=int(at_))
            at_player_name = at_player_name["card"] or at_player_name["nickname"]
            msg = (
                f"{player1_name} 向 {MessageSegment.at(at_)} 发起挑战！\n"
                f"请 {at_player_name} 回复 接受挑战 or 拒绝挑战\n"
                "【30秒内有效】"
                )
        else:
            at_ = 0
            msg = (
                f"{player1_name} 发起挑战！\n"
                "回复 接受挑战 即可开始对局。\n"
                "【30秒内有效】"
                )

        info = {
            "game":"russian",
            "bullet_num":bullet_num
            }
        _msg = russian_manager.ready_game(event, msg, player1_name, at_, money, info)
        await russian.send(_msg)

shot = on_command("开枪", aliases={"咔", "嘭", "嘣"}, permission=GROUP, priority=5, block=True)

@shot.handle()  
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    count = arg.extract_plain_text().strip()
    if is_number(count):
        count = abs(int(count))
        if count == 0:
            count = 7 - russian_manager.get_current_bullet_index(event)
        if count > 7 - russian_manager.get_current_bullet_index(event):
            await shot.finish(
                f"你不能开{count}枪，大于剩余的子弹数量，"
                f"剩余子弹数量：{7 - russian_manager.get_current_bullet_index(event)}"
                )
    else:
        count = 1
    await russian_manager.shot(bot, event, count)

# 摇骰子
dice = on_command("摇骰子",aliases={"摇色子", "掷骰子", "掷色子"}, permission=GROUP, priority=5, block=True)

@dice.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg(),):
    try:
        _msg = await russian_manager.check_current_game(bot, event)
        if _msg:
            await dice.finish(_msg)
    except KeyError:
        pass
    msg = arg.extract_plain_text().strip()
    if msg:
        msg = msg.split()
        money = msg[0].strip()
        if is_number(money) and 0 < int(money):
            money = int(money)
            money = money if money else 200
            user_money = russian_manager.get_user_data(event)["gold"]
            if money > max_bet_gold * 5:
                await dice.finish(f"单次金额不能超过{max_bet_gold * 5}", at_sender=True)
            if money > user_money:
                await dice.finish("你没有足够的金币支撑这场挑战", at_sender=True)

            player1_name = event.sender.card or event.sender.nickname
            at_ = get_message_at(event.json())
            if at_:
                at_ = at_[0]
                at_player_name = await bot.get_group_member_info(group_id=event.group_id, user_id=int(at_))
                at_player_name = at_player_name["card"] or at_player_name["nickname"]
                msg = (
                    f"{player1_name} 向 {MessageSegment.at(at_)} 发起挑战！\n"
                    f"请 {at_player_name} 回复 接受挑战 or 拒绝挑战\n"
                    "【30秒内有效】"
                    )
            else:
                at_ = 0
                msg = (
                    f"{player1_name} 发起挑战！\n"
                    "回复 接受挑战 即可开始对局。\n"
                    "【30秒内有效】"
                    )
            info = {"game":"dice"}
            _msg = russian_manager.ready_game(event, msg, player1_name, at_, money, info)
            await dice.send(_msg)

dice_open = on_command("取出", aliases={"开数", "开点"},permission=GROUP, priority=5, block=True)

@dice_open.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await russian_manager.dice_open(bot, event)

# 扑克对战
poker = on_command("扑克对战",aliases={"扑克对决", "扑克决斗"}, permission=GROUP, priority=5, block=True)

@poker.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg(),):
    try:
        _msg = await russian_manager.check_current_game(bot, event)
        if _msg:
            await poker.finish(_msg)
    except KeyError:
        pass
    msg = arg.extract_plain_text().strip()
    if msg:
        msg = msg.split()
        money = msg[0].strip()
        if is_number(money) and 0 < int(money):
            money = int(money)
            money = money if money else 200
            user_money = russian_manager.get_user_data(event)["gold"]
            if money > max_bet_gold:
                await poker.finish(f"单次金额不能超过{max_bet_gold}", at_sender=True)
            if money > user_money:
                await poker.finish("你没有足够的金币支撑这场挑战", at_sender=True)

            player1_name = event.sender.card or event.sender.nickname
            at_ = get_message_at(event.json())
            if at_:
                at_ = at_[0]
                at_player_name = await bot.get_group_member_info(group_id=event.group_id, user_id=int(at_))
                at_player_name = at_player_name["card"] or at_player_name["nickname"]
                msg = (
                    f"{player1_name} 向 {MessageSegment.at(at_)} 发起挑战！\n"
                    f"请 {at_player_name} 回复 接受挑战 or 拒绝挑战\n"
                    "【30秒内有效】"
                    )
            else:
                at_ = 0
                msg = (
                    f"{player1_name} 发起挑战！\n"
                    "回复 接受挑战 即可开始对局。\n"
                    "【30秒内有效】"
                    )
            info = {"game":"poker"}
            _msg = russian_manager.ready_game(event, msg, player1_name, at_, money, info)
            await poker.send(_msg)

poker_play = on_command("出牌", permission=GROUP, priority=5, block=True)

@poker_play.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    card = arg.extract_plain_text().strip()
    await russian_manager.poker_play(bot, event, card)

# 幸运花色
slot = on_command("（已停用）幸运花色", aliases={"（已停用）抽花色"},permission=GROUP, priority=5, block=True)

@slot.handle()
async def _(bot: Bot, event: GroupMessageEvent,arg: Message = CommandArg()):
    gold = 50
    if arg:
        if is_number(str(arg)):
            tmp = abs(int(str(arg)))
            if 0 < tmp <= int(max_bet_gold/2):
                gold = abs(int(str(arg)))

    msg = russian_manager.slot(event,gold)
    await slot.finish(msg, at_sender=True)

# 十连抽卡
gacha = on_command("十连",aliases={"10连"},rule = to_me(),permission=GROUP, priority=5, block=True)

@gacha.handle()
async def _(bot: Bot, event: GroupMessageEvent,arg: Message = CommandArg()):
    msg = russian_manager.gacha(event)
    await gacha.finish(msg, at_sender=True)

# 我的
my_props = on_command("我的道具", aliases={"我的仓库"}, permission=GROUP, priority=5, block=True)

@my_props.handle()
async def _(event: GroupMessageEvent):
    user = russian_manager.get_user_data(event)
    props = user["props"]
    props_info = '\n'
    for x in props.keys():
        if props[x] != 0:
            if x in constant_props:
                props_info += f'『{x}』 {props[x]}个\n'
            else:
                props_info += f'『{x}』 {props[x]}天\n'

    props_info = props_info[:-1]
    if not props_info:
        props_info = "你的仓库空空如也..."
    await my_props.finish(props_info,at_sender=True)

my_gold = on_command("我的金币", permission=GROUP, priority=5, block=True)

@my_gold.handle()
async def _(event: GroupMessageEvent):
    gold = russian_manager.get_user_data(event)["gold"]
    await my_gold.finish(f"你还有 {gold} 枚金币", at_sender=True)

my_info = on_command("我的信息", aliases={"我的资料"}, permission=GROUP, priority=5, block=True)

@my_info.handle()
async def _(event: GroupMessageEvent):
    info = russian_manager.my_info(event)
    output = text_to_png(info[:-1], 12)
    await my_info.finish(MessageSegment.image(output))

# 查看排行榜
russian_rank = on_command(
    "金币排行",
    aliases = {"胜场排行", "胜利排行", "败场排行", "失败排行", "欧洲人排行", "慈善家排行"},
    permission=GROUP,
    priority=5,
    block=True,
    )

@russian_rank.handle()
async def _(event: GroupMessageEvent):
    msg = await russian_manager.rank(event.raw_message, event.group_id)
    if msg:
        output = text_to_png(msg)
        await russian_rank.finish(MessageSegment.image(output))
    else:
        await russian_rank.finish()

# 查看路灯挂件
name_list = on_command("查看路灯挂件",aliases={"查看路灯","查看挂件"},permission=GROUP, priority=5, block=True)

@name_list.handle()
async def _(event: GroupMessageEvent):
    group_id = str(event.group_id)
    player_data = russian_manager._player_data
    all_user = list(player_data[group_id].keys())
    all_user_data = [player_data[group_id][x]["Achieve_revolution"] for x in all_user]
    if all_user:
        rst = ""
        for _ in range(len(all_user)):
            _max = max(all_user_data)
            if _max == 0:
                break
            _max_id = all_user[all_user_data.index(_max)]
            player_data[group_id][_max_id]["Achieve_revolution"]
            name = player_data[group_id][_max_id]["nickname"]
            rst += f"{name}：达成{_max}次\n"
            all_user_data.remove(_max)
            all_user.remove(_max_id)
        if rst:
            await name_list.finish("☆ ☆ 路灯挂件榜 ☆ ☆\n" + rst[:-1])
        else:
            await name_list.finish("群内没有路灯挂件。")
    else:
        await name_list.finish()

# 公司上市
Market_public = on_command("市场注册",aliases={"公司注册","注册公司"},rule = to_me(),permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=5, block=True)

@Market_public.handle()
async def _(event: GroupMessageEvent,arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    if msg:
        msg = msg.split()
        if len(msg) == 1:
            msg = msg[0]
            msg = market_manager.public(event,msg)
            await Market_public.finish(msg)
        else:
            await Market_public.finish(f"错误：公司名称格式错误\n{str(msg)}")
    else:
        await Market_public.finish("错误：未设置公司名称")

# 发行购买
company_buy = on_command("发行购买",aliases={"发行买入"},permission=GROUP, priority=5, block=True)

@company_buy.handle()
async def _(event: GroupMessageEvent,arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    if msg:
        msg = msg.split()
        if len(msg) == 2:
            company_name = msg[0]
            stock = abs(int(msg[1])) if is_number(msg[1]) else 100
            msg = market_manager.company_buy(event,company_name,stock)
            try:
                await company_buy.send(msg)
            except:
                output = text_to_png(msg)
                await company_buy.send(MessageSegment.image(output))
            finally:
                await company_buy.finish()

# 债务清算
company_clear = on_command("官方结算",permission=GROUP, priority=5, block=True)

@company_clear.handle()
async def _(event: GroupMessageEvent,arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    if msg:
        msg = msg.split()
        if len(msg) == 2:
            company_name = msg[0]            
            stock = abs(int(msg[1])) if is_number(msg[1]) else 100
            msg = market_manager.company_clear(event,company_name,stock)
            try:
                await company_clear.send(msg)
            except:
                output = text_to_png(msg)
                await company_clear.send(MessageSegment.image(output))
            finally:
                await company_clear.finish()

# 市场买入
Market_buy = on_command("买入",aliases={"购买","购入"},permission=GROUP, priority=5, block=True)

@Market_buy.handle()
async def _(event: GroupMessageEvent,arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    if msg:
        msg = msg.split()
        if len(msg) == 2:
            company_name = msg[0]            
            stock = abs(int(msg[1])) if is_number(msg[1]) else 100
            msg = market_manager.Market_buy(event,company_name,stock)
            try:
                await Market_buy.send(msg)
            except:
                output = text_to_png(msg)
                await Market_buy.send(MessageSegment.image(output))
            finally:
                await Market_buy.finish()

# 市场卖出
Market_sell = on_command("卖出",aliases={"出售","上架"},permission=GROUP, priority=5, block=True)

@Market_sell.handle()
async def _(event: GroupMessageEvent,arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    if msg:
        msg = msg.split()
        if len(msg) == 3:
            company_name = msg[0]
            if is_number(msg[1]):
                quote = abs(float(msg[1]))
                stock = abs(int(msg[2])) if is_number(msg[2]) else 100
                msg = market_manager.Market_sell(event,company_name,quote,stock)
                try:
                    await Market_sell.send(msg)
                except:
                    output = text_to_png(msg)
                    await Market_sell.send(MessageSegment.image(output))
                finally:
                    await Market_sell.finish()

# 市场信息
Market_info = on_command("市场信息",aliases={"查看市场"}, priority=5, block=True)

@Market_info.handle()
async def _(bot:Bot, event: MessageEvent,arg: Message = CommandArg()):
    company_name = arg.extract_plain_text().strip()
    if company_name:
        company_name = company_name.split()
        if len(company_name) == 1:
            company_name = company_name[0]
        else:
            company_name == ""
    else:
        company_name == ""
    msg = market_manager.Market_info(event,company_name)
    if type(msg) == list:
        await bot.send_group_forward_msg(group_id=event.group_id, messages = msg)
        await Market_info.finish()
    else:
        await Market_info.finish(msg)

# 市场走势
Market_info_pro = on_command("市场行情",aliases={"市场走势","市场详细信息"}, priority=5, block=True)

@Market_info_pro.handle()
async def _(bot:Bot, event: MessageEvent):
    if market_manager.info_temp[1] <= 6:
        msg = market_manager.info_temp[0]
    else:
        await Market_info_pro.send("正在生成走势图...")
        msg = await market_manager.Market_info_pro(event)

    if type(msg) == list:
        if isinstance(event, GroupMessageEvent):
            await bot.send_group_forward_msg(group_id = event.group_id, messages = msg)
        else:
            await bot.send_private_forward_msg(user_id = event.user_id, messages = msg)
        await Market_info_pro.finish()
    else:
        await Market_info_pro.finish(msg)

# 公司信息
company_info = on_command("公司信息",aliases={"公司资料"}, priority=5, block=True)

@company_info.handle()
async def _(event: MessageEvent,arg: Message = CommandArg()):
    company_name = arg.extract_plain_text().strip()
    if company_name:
        company_name = company_name.split()
        company_name = company_name[0]
        msg = market_manager.company_info(company_name)
        if msg:
            if os.path.exists(cache / "ohlc.json"):
                with open(cache / "ohlc.json", "r", encoding="utf8") as f:
                    ohlc = json.load(f)
                output = company_info_Splicing(msg ,ohlc[company_name])
            else:
                output = text_to_png(msg)
            await company_info.finish(MessageSegment.image(output))
        else:
            await company_info.finish(f"【{company_name}】未注册")
# 更新公司简介
update_intro = on_command("更新公司简介",aliases={"添加公司简介"},permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=5, block=True)

@update_intro.handle()
async def _(event: GroupMessageEvent,arg: Message = CommandArg()):
    intro = arg.extract_plain_text().strip()
    group_id = str(event.group_id)
    if intro:
        if group_id in market_manager._market_data.keys():
            company_name = market_manager._market_data[group_id]["company_name"]
            market_manager.update_intro(company_name,intro)
            await update_intro.finish("简介更新完成...")
        else:
            await update_intro.finish(f"群号：{group_id}未注册")
    else:
        await update_intro.finish()

# 管理员更新简介
update_intro_superuser = on_command("管理员更新公司简介",aliases={"管理员更新公司简介"},permission=SUPERUSER, priority=5, block=True)

@update_intro_superuser.handle()
async def _(event: GroupMessageEvent,arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    if msg:
        msg = msg.split(" ",1)
        market_manager.update_intro(msg[0],msg[1])
        await update_intro_superuser.finish("简介更新完成...")

# 跨群转移金币到自己的账户
intergroup_transfer = on_command("金币转移", permission=GROUP, priority=5, block=True)

@intergroup_transfer.handle()
async def _(event: GroupMessageEvent,arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    if len(msg) == 2 and is_number(msg[1]):
        company_name = msg[0]
        gold = msg[1]
        msg = market_manager.intergroup_transfer(event,company_name,gold)
        await intergroup_transfer.finish(msg, at_sender=True)

# 股票回收
repurchase = on_command("股票回收",aliases={"回收股票"} ,rule = to_me() , permission = SUPERUSER, priority=5, block = True)

@repurchase.handle()
async def _(bot:Bot):
    await repurchase.send("正在启动回收程序。")
    msg = await market_manager.repurchase(bot)
    await repurchase.finish(msg)

# 公司退市
delist = on_command("公司退市",aliases={"清理市场", "市场清理"} ,rule = to_me() , permission = SUPERUSER, priority=5, block = True)

@delist.handle()
async def _(bot:Bot):
    await delist.send("正在启动退市程序。")
    msg = await market_manager.delist(bot)
    await delist.finish(msg)

# 刷新每日签到和每日补贴
reset_sign = on_command("reset_sign", permission=SUPERUSER, priority=5, block=True) # 重置每日签到和每日补贴

@reset_sign.handle()
@scheduler.scheduled_job("cron", hour = 0)
async def _():
    russian_manager.reset_sign()
    logger.info("今日签到重置成功...")
    russian_manager.reset_security()
    logger.info("今日补贴重置成功...")
     
# 刷新道具时间
@scheduler.scheduled_job("cron", hour = 4)
async def _():
    for group_id in russian_manager._player_data.keys():
        for user_id in russian_manager._player_data[group_id].keys():
            for props in russian_manager._player_data[group_id][user_id]["props"].keys():
                if russian_manager._player_data[group_id][user_id]["props"][props] > 0 and props not in constant_props:
                    russian_manager._player_data[group_id][user_id]["props"][props] -= 1
    else:
        logger.info("道具时间已刷新...")
        russian_manager.save()

# 市场指数更新
@scheduler.scheduled_job("cron", hour = "0,3,6,9,12,15,18,21")
async def _():
    market_manager.reset_market_index()

# 股市更新
@scheduler.scheduled_job("cron", minute = "0,5,10,15,20,25,30,35,40,45,50,55")
async def _():
    for group_id in russian_manager._player_data.keys():
        for user_id in russian_manager._player_data[group_id].keys():
            russian_manager._player_data[group_id][user_id]["stock"]["value"] = market_manager.value_update(group_id,user_id)

        if group_id in market_manager._market_data.keys():
            market_manager.company_update(group_id)
            logger.info(f'【{market_manager._market_data[group_id]["company_name"]}】更新成功...')
    else:
        market_manager.info_temp[1] += 1
        russian_manager.save()
        market_manager.market_data_save()
        market_manager.market_history_save()

# 数据备份

@scheduler.scheduled_job("cron", hour = "4,10,16,22")
async def _():
    now = time.strftime('%Y-%m-%d-%H', time.localtime(time.time()))
    path =f"{russian_path}/data/russian"
    if not os.path.exists(f"{path}/backup"):
        os.makedirs(f"{path}/backup")
    if os.path.isfile(f"{path}/market_data.json"):
        shutil.copy(f"{path}/market_data.json",f"{path}/backup/market_data {now}.json")
        logger.info(f'market_data.json备份成功！')
    if os.path.isfile(f"{path}/russian_data.json"):
        shutil.copy(f"{path}/russian_data.json",f"{path}/backup/russian_data {now}.json")
        logger.info(f'russian_data.json备份成功！')
    if os.path.isfile(f"{path}/Stock_Exchange.json"):
        shutil.copy(f"{path}/Stock_Exchange.json",f"{path}/backup/Stock_Exchange {now}.json")
        logger.info(f'Stock_Exchange.json备份成功！')