from typing import Tuple
from PIL import Image
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment
    )

import random
import time
import datetime
import asyncio

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from .utils.chart import bbcode_to_PIL, group_info_head, info_Splicing
from .data.data import GroupAccount, Company, ExchangeInfo
from .data.data import OHLC, props_library
from .config import bot_name, revolt_gini, max_bet_gold, path

from .Manager import data, company_index
from .Manager import BG_path, update_company_index

from . import Manager

user_data = data.user
group_data = data.group

def check_company_name(company_name:str):
    """
    检查公司名是否合法
    """
    if not company_name:
        return f"公司名称不能为空"
    update_company_index()
    if company_name in company_index:
        return f"{company_name} 已被注册"
    if " " in company_name or "\n" in company_name:
        return "公司名称不能含有空格或回车"
    count = 0
    for x in company_name:
        if ord(x) < 0x200:
            count += 1
        else:
            count += 2
    if count > 24:
        return f"公司名称不能超过24字符"
    try:
        int(company_name)
        return f"公司名称不能是数字"
    except:
        return None

def public(event:GroupMessageEvent,company_name:str):
    """
    公司上市
        company_name:公司名
    """
    group_id = event.group_id
    company = group_data[group_id].company
    if company.company_name:
        return f"本群已在市场注册，注册名：{company.company_name}"
    if check := check_company_name(company_name):
        return check
    if (gold := (Manager.group_wealths(group_id) or 0)) < (limit := 15 * max_bet_gold):
        return f"本群金币（{round(gold,2)}）小于{limit}，注册失败。"
    if (gini := Manager.Gini(group_id)) > 0.56:
        return f"本群基尼系数（{round(gini,3)}）过高，注册失败。"
    gold = Manager.group_wealths(group_id)
    company = group_data[group_id].company
    company.company_id = group_id
    company.company_name = company_name
    company.level = 1
    company.time = time.time()
    company.stock = 20000
    company.issuance = 20000
    company.gold = gold * 0.8
    company.float_gold = company.gold
    company.group_gold = gold
    company.intro = f"发行初始信息\n金币 {round(gold,2)}\n基尼系数{round(gini,3)}\n{company_name} 名称检查通过\n发行成功！"
    update_company_index()
    data.save()
    return f'{company_name}发行成功，发行价格为每股{round((gold/ 20000),2)}金币'

def rename(event:GroupMessageEvent,company_name:str):
    """
    公司重命名
        company_name:公司名
    """
    group_id = event.group_id
    company = group_data[group_id].company
    if not company.company_name:
        return "本群未在市场注册，不可重命名。"
    user = Manager.locate_user(event)[0]
    if user.props.get("33001",0) < 1:
        return f"你的【{props_library['33001']['name']}】已失效"
    if check := check_company_name(company_name):
        return check
    old_company_name = company.company_name
    company.company_name = company_name
    update_company_index()
    return f'【{old_company_name}】已重命名为【{company_name}】'

def value_update(group_account:GroupAccount):
    """
    刷新持股价值
    group_account:用户群账户
    """
    stocks = group_account.stocks
    group_id = group_account.group_id
    value = 0.0
    for company_id in stocks:
        if company_id != group_id:
            company = group_data[company_id].company
            unit = company.float_gold / company.issuance
            value += stocks[company_id] * unit
    group_account.value = value
    return value

def buy(event:MessageEvent, buy:int, company_name:str):
    """
    以发行价格购买股票
        buy:购买数量
        company_name:股票名
    """
    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"

    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"

    company = group_data[company_id].company
    company_name = company.company_name

    buy = company.stock if company.stock < buy else buy
    if buy < 1:
        return "已售空，请等待结算或在交易市场购买。"

    group_gold = Manager.group_wealths(company_id) or 0
    company.group_gold = group_gold
    if group_gold < 10 * max_bet_gold:
        return f"【{company_name}】金币过少({group_gold})，无法交易。"

    gold = max(group_gold, company.float_gold)
    SI = company.issuance
    gini = Manager.Gini(company_id)
    value = 0.0
    for _ in range(buy):
        unit = gold/SI
        gold += unit * gini
        value += unit
    else:
        value = int(value + 0.5)
    my_gold = group_account.gold
    if value > my_gold:
        return (
            f"{company_name}\n"
            "——————————\n"
            f"数量：{buy}\n"
            f"单价：{round(value/buy,2)}\n"
            f"总计：{value}\n"
            "——————————\n"
            f"金币不足（{my_gold}）"
            )        
    else:
        company.stock -= buy
        group_account.stocks.setdefault(company_id,0)
        group_account.stocks[company_id] += buy
        user.gold -= value
        group_account.gold -= value
        company.gold += value
        company.float_gold += value
        company.group_gold = group_gold
        value_update(group_account)
        return (
            f"{company_name}\n"
            "——————————\n"
            f"数量：{buy}\n"
            f"单价：{round(value/buy,2)}\n"
            f"总计：{value}\n"
            "——————————\n"
            "交易成功！"
            )

def settle(event:MessageEvent, settle:int, company_name:str):
    """
    以债务价值结算股票
        settle:结算数量
        company_name:股票名
    """ 
    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"

    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"

    my_stock = group_account.stocks.get(company_id,0)

    if my_stock < settle:
        return f"你没有足够的股份...你的 {company_name} 还有 {my_stock} 个"

    company = group_data[company_id].company
    company_name = company.company_name

    group_gold = Manager.group_wealths(company_id) or 0
    company.group_gold = group_gold
    if group_gold < 10 * max_bet_gold:
        return f"【{company_name}】金币过少({group_gold})，无法交易。"

    gold = company.float_gold
    SI = company.issuance
    gini = Manager.Gini(company_id)
    value = 0.0
    for _ in range(settle):
        unit = gold/SI
        gold -= unit * gini
        value += unit
    else:
        value = int(value + 0.5)

    if group_account.props.get("42001",0):
        fee = 0
        tips = f"『{props_library['42001']['name']}』免手续费"
    else:
        fee = int(value * 0.02)
        tips = f"扣除2%手续费：{fee}"

    company.stock += settle
    if group_account.stocks[company_id] == settle:
        del group_account.stocks[company_id]
    else:
        group_account.stocks[company_id] -= settle
    user.gold += value - fee
    group_account.gold += value - fee
    company.gold -= value
    company.float_gold -= value
    company.group_gold = group_gold
    if user.user_id in company.exchange:
        del company.exchange[user.user_id]
    value_update(group_account)

    return (
        f"{company_name}\n"
        "——————————\n"
        f"数量：{settle}\n"
        f"单价：{round(value/settle,2)}\n"
        f"总计：{value} - {fee}\n"
        "——————————\n"
        "交易成功！\n" + tips
        )

def Exchange_buy(event:MessageEvent, buy:int, company_name:str):
    """
    从交易市场买入股票
        buy:购买数量
        company_name:股票名
    """
    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"

    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"

    company = group_data[company_id].company
    company_name = company.company_name

    exchange = company.exchange
    user_id = user.user_id

    rank = [x for x in exchange.items() if x[0] != user_id]
    rank.sort(key = lambda x:x[1].quote)
    
    my_gold = group_account.gold

    gold = 0
    count = 0
    n = 0
    i = 0

    if (l := len(rank)) < 1:
        return f"没有正在出售的 {company_name}"

    lastinfo = None

    while count < buy and i < l:
        tmp = rank[i]
        n = tmp[1].n
        quote = tmp[1].quote
        count += n
        if count > buy:
            lastinfo = (tmp[0],ExchangeInfo(group_id = tmp[1].group_id, quote = quote,n = (count - buy)))
            n = n - (count - buy)
            count = buy
        unsettled = int((quote * n) + 0.5)
        gold += unsettled
        rank[i] = [tmp[0], tmp[1].group_id, n, unsettled]
        if gold > my_gold:
            return f"你的金币不足（{my_gold}）"
        i += 1

    group_account.stocks.setdefault(company_id,0)
    rank = rank[:i]
    for x in rank:
        seller_user = user_data[x[0]]
        seller_group_account = seller_user.group_accounts[x[1]]
        unsettled = x[3]
        user.gold -=  unsettled
        group_account.gold -= unsettled
        if seller_group_account.props.get("42001",0):
            fee = 0
        else:
            fee = int(unsettled * 0.02)
        seller_user.gold += unsettled - fee
        seller_group_account.gold += unsettled - fee
        n = x[2]
        group_account.stocks[company_id] += n
        seller_group_account.stocks[company_id] -= n
        value_update(seller_group_account)
        del exchange[x[0]]
    else:
        value_update(group_account)
    if lastinfo:
        exchange[lastinfo[0]] = lastinfo[1]

    return (
        f"{company_name}\n"
        "——————————\n"
        f"数量：{count}\n"
        f"单价：{round(gold/count,2)}\n"
        f"总计：{gold}\n"
        "——————————\n"
        "交易成功！"
        )

def Exchange_sell(event:MessageEvent, info:Tuple[int,ExchangeInfo]):
    """
    从交易市场发布交易信息
        buy:购买数量
        company_name:股票名
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    else:
        company_id = info[0]
        exchange_info = info[1]
        exchange_info.group_id = group_account.group_id

    my_stock = group_account.stocks.get(company_id,0)

    if my_stock < exchange_info.n:
        return f"你的账户中没有足够的股票（{my_stock}）。"

    user_id = user.user_id
    company = group_data[company_id].company
    exchange = company.exchange
    n = exchange_info.n 
    if n < 1:
        quote = 0
        n = 0
        if exchange.get(user_id):
            del exchange[user_id]
            tips = "交易信息已注销。"
        else:
            tips = "交易信息无效。"
    else:
        quote = exchange_info.quote
        unit = company.group_gold if company.group_gold < company.float_gold else company.float_gold
        unit = unit / company.issuance
        if quote < (1  if (tmp := unit/4) < 1 else tmp) or quote > (max_bet_gold if (tmp := 10 * unit) < max_bet_gold else tmp):
            tips = "报价异常，发布失败。"
        else:
            if exchange.get(user_id):
                tips = "交易信息已修改。"
            else:
                tips = "交易信息发布成功！"
            exchange[user_id] = exchange_info

    return (
        f"{company.company_name}\n"
        "——————————\n"
        f'报价：{quote}\n'
        f'数量：{n}\n'
        "——————————\n"
        + tips
        )

async def group_info(bot:Bot, event:MessageEvent, group_id:int):
    """
    群资料卡
    """
    if group_id in group_data:
        group = group_data[group_id]
        company = group.company
    else:
        return f"没有 {group_id} 的注册信息"

    info = []
    # 加载群信息
    company_name = company.company_name
    group_info = await bot.get_group_info(group_id = group_id)
    group_name = group_info["group_name"]
    member_count = group_info["member_count"]
    if member_count == 0:
        member_count = 3000
    else:
        member_count = member_count - 1

    info.append(await group_info_head(group_name, company_name, group_id, (len(group.namelist),member_count)))

    linestr = "[color=gray][size=15][font=simsun.ttc]────────────────────────────────────────────────────────[/font][/size][/color]\n"

    msg = ""
    ranklist = list(group.Achieve_revolution.items())
    ranklist.sort(key=lambda x:x[1],reverse=True)
    for x in ranklist[:10]:
        msg += f"{user_data[x[0]].group_accounts[group_id].nickname}[align=right]{x[1]}次[/align]\n"
    if msg:
        info.append(bbcode_to_PIL("[align=center]路灯挂件[/align]" + linestr + msg[:-1], 60))

    # 加载公司信息
    if company_name:
        msg = (
            f"公司等级 {company.level}\n"
            f"成立时间 {datetime.datetime.fromtimestamp(company.time).strftime('%Y 年 %m 月 %d 日')}\n"
            )

        info.append(bbcode_to_PIL(msg + linestr + "[align=right][size=30][color=gray]注册信息[/color][/size][/align]", 60))

        info.append(bbcode_to_PIL(stock_profile(company) + linestr + "[align=right][size=30][color=gray]产业信息[/color][/size][/align]", 60))

        p = OHLC(path, group_id)

        overtime = time.time() + 30
        while (returncode := p.poll()) == None:
            if time.time() > overtime:
                returncode = 1
                break
            await asyncio.sleep(0.5)

        if returncode == 0:
            info.append(Image.open(path / "candlestick" / f"{group_id}.png"))

        ranklist = list(company.exchange.items())
        ranklist.sort(key=lambda x:x[1].quote)
        msg = ""
        for x in ranklist[:10]:
            msg += f"{user_data[x[0]].nickname}[align=right]单价 {x[1].quote} 数量 {x[1].n}[/align]\n"
        if msg:
            info.append(bbcode_to_PIL(msg + linestr + "[align=right][size=30][color=gray]市场详情[/color][/size][/align]", 40))

        msg = company.intro
        if msg:
            info.append(bbcode_to_PIL(msg + "\n" +linestr + "[align=right][size=30][color=gray]公司介绍[/color][/size][/align]", 40))

    return MessageSegment.image(info_Splicing(info, BG_path(event.user_id)))

def stock_profile(company:Company) -> str:
    """
    产业信息
    """
    group_gold = company.group_gold
    float_gold = company.float_gold
    issuance = company.issuance
    msg = (
        f"固定资产 {'{:,}'.format(round(company.gold,2))}\n"
        f"市场流动 {'{:,}'.format(round(company.group_gold))}\n"
        f"发行价格 {'{:,}'.format(round(max(group_gold,float_gold)/issuance,2))}\n"
        f"结算价格 {'{:,}'.format(round(float_gold/issuance,2))}\n"
        f"剩余数量 {company.stock}\n"
        )
    return msg

def Market_info_All(event:MessageEvent, ohlc:bool = False):
    """
    市场信息总览
    """
    global company_index
    company_ids = set([company_index[company_id] for company_id in company_index])
    companys = []
    for company_id in company_ids:
        company = group_data[company_id].company
        companys.append(company)
    companys.sort(key = lambda x:x.group_gold, reverse = True)

    lst = [companys[i:i+5] for i in range(0, len(companys), 5)]
    linestr = "[color=gray][size=15][font=simsun.ttc]────────────────────────────────────────────────────────[/font][/size][/color]\n"
    msg = []
    for seg in lst:
        info = []
        for company in seg:
            info.append(bbcode_to_PIL(company.company_name +"\n" + linestr + stock_profile(company), 60))
        msg.append({"type":"node",
                    "data":{
                        "name":f"{bot_name}",
                        "uin":str(event.self_id),
                        "content":MessageSegment.image(info_Splicing(info, BG_path(event.user_id)))}})
    return msg

def update_intro(company_name:str, intro:str):
    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"
    group_data[company_id].company.intro = intro
    return "简介更新完成!"

market_history_file = path / "market_history.json"

if market_history_file.exists():
    with open(market_history_file, "r", encoding = "utf8") as f:
        market_history = json.load(f)
    market_history = {int(k):v for k,v in market_history.items()}
else:
    market_history = {}

def company_update(company:Company):
    """
    刷新公司信息
        company:公司账户
    """
    company_id = company.company_id
    # 更新全群金币数
    group_gold = Manager.group_wealths(company_id)
    company.group_gold = group_gold
    # 固定资产回归值 = 80%全群金币数 + 40%股票融资 总计：80%~120%全群金币数
    line = group_gold * (1.2 - 0.4 * (company.stock / company.issuance))
    # 公司金币数回归到固定资产回归值
    company.gold += (line - company.gold)/96
    # 股票价格变化 = 趋势性影响（正态分布） + 随机性影响（平均分布）
    float_gold = company.float_gold
    float_gold += company.float_gold * random.gauss(0,0.03) + company.gold * random.uniform(-0.1, 0.1)
    # 股票价格向债务价值回归
    gold = company.gold
    deviation = gold - float_gold
    float_gold += deviation * 0.1 * abs(deviation)/gold
    # 更新浮动价格
    company.float_gold = float_gold
    # 记录价格历史
    global market_history
    market_history.setdefault(company_id,[]).append((time.time(), group_gold / company.issuance, float_gold / company.issuance))
    market_history[company_id] = market_history[company_id][-720:]

def update():
    """
    刷新市场
    """
    log = ""
    company_ids = set([company_index[company_id] for company_id in company_index])
    for company_id in company_ids:
        company = group_data[company_id].company
        company_update(company)
        log += f"{company.company_name} 更新成功！\n"

    for user_id in user_data:
        group_accounts = user_data[user_id].group_accounts
        for group_id in group_accounts:
            value_update(group_accounts[group_id])

    return log[:-1]