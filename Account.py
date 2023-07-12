from typing import Tuple
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    Message,
    MessageSegment
    )

import random
import time
import datetime

from .utils.chart import (
    bar_chart,
    my_info_head,
    my_info_account,
    linecard,
    info_splicing
    )
from .data import Company, UserDict, GroupAccount
from .data import props_library, props_index
from .config import bot_name,sign_gold, revolt_gold, revolt_cd, revolt_gini, max_bet_gold

from . import Manager

data = Manager.data
user_data = data.user
group_data = data.group

company_index = Manager.company_index

def gold_create(event:MessageEvent,gold:int) -> str:
    """
    获取金币
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"

    user.gold += gold
    group_account.gold += gold
    return f"你获得了 {gold} 金币"

def props_create(event:MessageEvent, prop_name:str, count:int) -> str:
    """
    获取道具
    """
    prop_code = props_index.get(prop_name)
    if not prop_code:
        return f"没有【{prop_name}】这种道具。"

    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"

    if prop_code[1] == "3":
        account = user
    else:
        account = group_account

    account.props.setdefault(prop_code,0)
    account.props[prop_code] += count
    return f"你获得了{count}个【{prop_name}】！"

def sign(event:MessageEvent) -> str:
    """
    签到
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"

    if group_account.is_sign:
        return "你已经签过到了哦"
    else:
        gold = random.randint(sign_gold[0], sign_gold[1])
        user.gold += gold
        group_account.gold += gold
        group_account.is_sign = True
    return random.choice(["祝你好运~", "可别花光了哦~"]) + f"\n你获得了 {gold} 金币"

def revolt_sign(event:MessageEvent) -> str:
    """
    重置签到
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"

    if group_account.revolution:
        return "你没有待领取的金币"
    else:
        gold = random.randint(revolt_gold[0], revolt_gold[1])
        user.gold += gold
        group_account.gold += gold
        group_account.revolution = True
    return f"这是你重置后获得的金币，你获得了 {gold} 金币"

def revolution(group_id:int) -> str:
    """
    发动革命
        group_id:群号
    """

    if group_id not in group_data:
        return None

    group = group_data[group_id]

    if time.time() - group.revolution_time < revolt_cd:
        return f"重置正在冷却中，结束时间：{datetime.datetime.fromtimestamp(group.revolution_time + revolt_cd).strftime('%H:%M:%S')}"

    if (gold := (Manager.group_wealths(group_id) or 0)) < (limit := 15 * max_bet_gold):
        return f"本群金币（{round(gold,2)}）小于{limit}，未满足重置条件。"

    if (gini := Manager.Gini(group_id)) < revolt_gini:
        return f"当前基尼系数为{round(gini,3)}，未满足重置条件。"

    rank = Manager.group_ranklist(group_id,"资产")
    user_id = rank[0][0]
    group_account = user_data[user_id].group_accounts[group_id]
    group_account.props.setdefault("02101",0)
    group_account.props["02101"] += 1

    group.revolution_time = time.time()
    group.Achieve_revolution.setdefault(user_id,0)
    group.Achieve_revolution[user_id] += 1

    first_name = group_account.nickname

    i = 0.0
    j = i**2
    for x in rank[:10]:
        user = user_data[x[0]]
        group_account = user.group_accounts[group_id]
        gold = int(group_account.value*j - group_account.gold*(1-j))
        user.gold += gold
        group_account.gold += gold
        company_ids = [company_id for company_id in group_account.stocks]
        for company_id in company_ids:
            company = group_data[company_id].company
            if user_id in company.exchange:
                del company.exchange[user_id]
            company.stock += group_account.stocks[company_id]
            del group_account.stocks[company_id]
        i += 0.1
        j = i**2
    for user_id in group.namelist:
        user_data[user_id].group_accounts[group_id].revolution = False
    data.save()
    return f"重置成功！恭喜{first_name}进入挂件榜☆！\n当前系数为：{round(gini,3)}，重置签到已刷新。"

def transfer_gold(event:GroupMessageEvent, target:Tuple[UserDict,GroupAccount], gold:int) -> str:
    """
    转账处理
        param:
        event: GroupMessageEvent
        target:目标账户
        gold:  转账金币
    """
    self_user,self_group_account = Manager.locate_user(event)
    target_user,target_group_account = target

    if self_group_account.gold < gold:
        return f"你没有足够的金币，无法完成结算。\n——你还有{self_group_account.gold}枚金币。"

    if target_group_account.props.get("42001",0):
        fee = 0
        tips = f"『{props_library['42001']['name']}』免手续费"
    else:
        fee = int(gold * 0.02)
        tips = f"扣除2%手续费：{fee}，实际到账金额{gold - fee}"

    self_user.gold -= gold
    self_group_account.gold -= gold
    target_user.gold += gold - fee
    target_group_account.gold += gold - fee

    return f"向 {target_group_account.nickname} 赠送{gold}金币\n" + tips

def transfer_props(event:GroupMessageEvent, target:Tuple[UserDict,GroupAccount], prop_name:str, count:int) -> str:
    """
    赠送道具
        param:
        event: GroupMessageEvent
        target:目标账户
        props: 道具名
        count: 数量
    """
    prop_code = props_index.get(prop_name)
    if not prop_code:
        return f"没有【{prop_name}】这种道具。"

    self_user,self_group_account = Manager.locate_user(event)
    target_user,target_group_account = target

    if prop_code[1] == "3":
        self_account = self_user
        target_account = target_user
    else:
        self_account = self_group_account
        target_account = target_group_account

    n = self_account.props.get(prop_code,0)
    if n < count:
        return f"你没有足够的道具，无法完成结算。\n——你有{n}个【{prop_name}】。"

    self_account.props[prop_code] -= count
    target_account.props.setdefault(prop_code,0)
    target_account.props[prop_code] += count
    return f"向 {target_group_account.nickname} 送出{count}个【{prop_name}】！"

def connect(event:MessageEvent, group_id:str = None) -> str:
    """
    关联账户
        param:
        event: GroupMessageEvent
        group_id:关联群号
    """
    user = Manager.locate_user(event)[0]
    if group_id:
        try:
            group_id = int(group_id)
        except:
            return f"无效输入：{group_id}"
        if group_id in user.group_accounts:
            user.connect = group_id
        else:
            return f"你在 {group_id} 无账户，关联失败。"
    else:
        user.connect = event.group_id
    return f"私聊账户已关联到{group_id}"

def my_gold(event:MessageEvent) -> str:
    """
    我的金币
    """
    user,group_account = Manager.locate_user(event)
    if group_account:
        return f"你还有 {group_account.gold} 枚金币"
    else:
        group_accounts = user.group_accounts
        msg = "你的账户\n"
        for group_id in group_accounts:
            msg += f'{group_id} 金币：{group_accounts[group_id].gold}枚\n'
        return msg

async def my_info(event:MessageEvent) -> Message:
    """
    我的资料卡
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"

    info = []
    # 加载全局信息
    nickname = group_account.nickname
    info.append(await my_info_head(user,nickname))
    # 加载卡片
    PropsCard = Manager.PropsCard_list((user,group_account))
    msg = ""
    for x in PropsCard:
        msg += f"----\n[center]{x}\n"
    if msg:
        info.append(linecard(msg+"----", width = 880,padding = (0,-28),spacing = 1, font_size = 60))

    # 加载成就卡片
    Achieve = Manager.Achieve_list((user,group_account))[:2]
    # 加载本群账户
    gold = group_account.gold
    value = group_account.value
    is_sign = group_account.is_sign
    if is_sign:
        is_sign = ["已签到","green"]
    else:
        is_sign = ["未签到","red"]
    security = 3 - group_account.security
    if security:
        security = [security,"green"]
    else:
        security = [security,"red"]
    msg = ""
    for x in Achieve:
        msg += f"{x}\n"
    msg += (2-len(Achieve))*"\n"
    msg += (
        f"金币 {'{:,}'.format(gold)}\n"
        f"股票 {'{:,}'.format(round(value,2))}\n"
        "签到 [nowrap]\n"
        f"[color][{is_sign[1]}]{is_sign[0]}\n"
        "补贴 还剩 [nowrap]\n"
        f"[color][{security[1]}]{security[0]}[nowrap]\n 次"
        )
    # 加载资产分析
    dist = []
    for x in user.group_accounts:
        account = user.group_accounts[x]
        if not (group_name := group_data[x].company.company_name):
            group_name = f"（{str(x)[-4:]}）"
        dist.append([account.gold + account.value, group_name])
    dist = [x for x in dist if x[0] > 0]

    info.append(my_info_account(msg,dist))

    # 加载股票信息
    msg = ""
    for stock in group_account.stocks:
        company_name = group_data[stock].company.company_name
        if i := group_account.stocks[stock]:
            msg += f"{company_name}[nowrap]\n[right][color][green]{i}\n"
    if msg:
        info.append(linecard(msg, width = 880,endline = "股票信息"))

    return MessageSegment.image(info_splicing(info,Manager.BG_path(event.user_id)))

def my_props(event:MessageEvent) -> Message:
    """
    我的道具
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"

    props = {}
    props.update(user.props)
    props.update(group_account.props)
    props = sorted(props.items(), key = lambda x:int(x[0]), reverse = True)
    info = []
    for seg in props:
        if (n := seg[1]) < 1:
            continue
        prop_code = seg[0]
        quant = "天" if prop_code[2] == "0" else "个"
        prop = props_library.get(prop_code,{"name": prop_code, "color": "black","rare": 1,"intro": "未知","des": "未知"})

        color = prop['color']
        name = prop['name']
        rare = prop['rare']
        msg = (
            f"[font_big][color][{color}]【{name}】[nowrap][passport]\n[right]{n}{quant}\n"
            "----\n"
            + prop['intro'] + f"\n[right]{prop['des']}\n"
            )

        info.append(
            linecard(msg,
                     width = 880,
                     padding=(0,20),
                     endline = "特殊道具" if rare == 0 else rare*'☆',
                     bg_color = (255,255,255,153),
                     autowrap = True
                     ))
    if info:
        return MessageSegment.image(info_splicing(info,Manager.BG_path(event.user_id),spacing = 5))
    else:
        return "您的仓库空空如也。"

async def info_profile(user_id:int) -> list:
    """
    总览资料卡
    """
    user = user_data[user_id]
    info = []
    # 加载全局信息
    nickname = user.nickname
    info.append(await my_info_head(user,nickname))
    msg = ""
    # 加载资产分析
    dist = []
    for x in user.group_accounts:
        account = user.group_accounts[x]
        if not (group_name := group_data[x].company.company_name):
            group_name = f"（{str(x)[-4:]}）"
        dist.append([account.gold + account.value, group_name])
    dist = [x for x in dist if x[0] > 0]
    if dist:
        info.append(my_info_account(msg,dist))
    return info

def format_ranktitle(x,title:str = "金币"):
    """
    根据排行榜将数据格式化
    """
    if title == "金币" or title == "总金币":
        return '{:,}'.format(x)
    elif title == "总资产" or title == "资产" or title == "财富":
        return '{:,}'.format(round(x,2))
    elif title == "胜率":
        return f"{round(x*100,2)}%"
    else:
        return x

async def draw_rank(ranklist:list, title:str = "金币", top:int = 20, group_id = None) -> list:
    """
    排名信息
    """
    info = []
    i = 1
    first = ranklist[0][1]
    if group_id:
        nicname = lambda user:user.group_accounts[group_id].nickname
    else:
        nicname = lambda user:user.nickname
    for x in ranklist[:top]:
        user_id = x[0]
        info.append(await bar_chart(user_id,f"{i}.{nicname(user_data[user_id])}：{format_ranktitle(x[1],title)}\n", x[1]/first))
        i += 1
    return info

async def group_rank(event:MessageEvent, title:str = "金币") -> str:
    """
    生成群内排行榜
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    user_id = user.user_id
    group_id = group_account.group_id
    if not (ranklist := Manager.group_ranklist(group_id, title)):
        return "无数据。"
    info = await draw_rank(ranklist, title, 20, group_id = group_id)
    return MessageSegment.image(info_splicing(info,Manager.BG_path(user_id), spacing = 5))

async def All_rank(event:MessageEvent, title:str = "金币", top:int = 10) -> list:
    """
    生成总排行榜
    """
    if not (ranklist := Manager.All_ranklist(title)):
        return None
    info = await draw_rank(ranklist, title, 20)
    return MessageSegment.image(info_splicing(info,Manager.BG_path(event.user_id), spacing = 5))

def transfer_fee(amount:int,limit:int) -> int:
    limit = limit if limit > 0 else 0
    if amount <= limit:
        fee = amount * 0.02
    else:
        fee = limit * 0.02 + (amount - limit) * 0.2
    return int(fee)

def intergroup_transfer_gold(event:MessageEvent, gold:int, company_name:str):
    """
    跨群转移金币到自己的账户
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    if gold > group_account.gold:
        return f"你没有足够的金币，无法完成结算。\n——你还有{group_account.gold}枚金币。"

    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"

    if company_id in user.group_accounts:
        target_group_account = user.group_accounts[company_id]
    else:
        return f"你在 {company_name} 没有创建账户"

    group_account.gold -= gold
    ExRate = min((group_data[group_account.group_id].company.level or 1)/group_data[company_id].company.level,1)
    tgold = int(ExRate * gold + 0.5)
    fee = transfer_fee(tgold, (10 * max_bet_gold) - user.transfer_limit)
    target_group_account.gold += tgold - fee
    user.transfer_limit += tgold
    user.gold -= fee

    return f"向 {company_name} 转移 {gold}金币。汇率：{round(ExRate,2)}、手续费：{fee}\n实际到账金额{tgold - fee}"

def freeze(target:UserDict):
    target_id = target.user_id
    gold = target.gold
    value = 0.0
    group_accounts = target.group_accounts
    for group_id,group_account in group_accounts.items():
        value += group_account.value
        group = group_data[group_id]
        for company_id in group_account.stocks:
            company = group_data[company_id].company
            company.Buyback(group_account)
        group.namelist.remove(target_id)

    target.gold = 0
    target.group_accounts = {}

    x = gold + value
    if x > 500 * max_bet_gold:
        count = 500
    elif x > 50 * max_bet_gold:
        count = int (x / max_bet_gold)
    else:
        count = int (x / max_bet_gold) + 1

    target.props.setdefault("03101",0)
    target.props["03101"] += count

    data.save()

    return f"【冻结】清算完成，总价值为 {round(x,2)}（金币 {gold} 股票 {round(value,2)}）"

async def delist():
        """
        清理无效账户
        """
        mapping = {}
        bot_list = Manager.driver.bots.values()
        for bot in bot_list:
            group_list = await bot.get_group_list(no_cache = True)
            for group in group_list:
                mapping[group["group_id"]] = bot
        if not mapping:
            return "群组获取失败"

        # 存在的群
        groups = set(mapping.keys())
        # 注册过的群
        login_groups= set(group_data.keys())
        # 已注册但不存在的群
        delist_group = login_groups - groups

        log = ""
        # 处理与不存在的群相关的群账户
        for user_id in user_data:
            user = user_data[user_id]
            group_accounts = user.group_accounts
            accountset = set(group_accounts.keys())
            delist_group_accounts = accountset & delist_group
            for group_id in accountset:
                group_account = group_accounts[group_id]
                if group_id in delist_group_accounts:
                    # 删除不存在的群账户
                    log += f'删除群账户：{user_id} - {group_id}\n'
                    del group_account
                else:
                    # 删除不存在的股票
                    group_account.stocks = {stock:count for stock, count in group_account.stocks.items() if stock not in delist_group_accounts}
        # 删除不存在的群
        for group_id in delist_group:
            log += f'删除群：{group_id}\n'
            del group_data[group_id]

        # 已注册且存在的群
        normal_groups = login_groups & groups
        for group_id in normal_groups:
            users = await mapping[group_id].get_group_member_list(group_id = group_id, no_cache = True)
            if users:
                users = set(x["user_id"] for x in users)
            else:
                continue
            # 删除已注册但不存在的用户
            namelist = group_data[group_id].namelist
            delist_users = namelist - users
            for user_id in delist_users:
                log += f'删除群账户：{user_id} - {group_id}\n'
                del user_data[user_id].group_accounts[group_id]
                namelist.discard(user_id)
        Manager.update_company_index()
        # 保存数据
        data.save()
        return log[:-1] if log else "没有要清理的数据！"
