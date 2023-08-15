from re import M
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
import math
import datetime
import asyncio

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from .utils.chart import linecard,linecard_to_png, group_info_head, info_splicing
from .data import GroupAccount, Company, ExchangeInfo
from .data import OHLC, props_library
from .config import bot_name, gacha_gold, max_bet_gold, bet_gold, path

from .Alchemy import Alchemy
from . import Manager

data = Manager.data
user_data = data.user
group_data = data.group

company_index = Manager.company_index
company_level = Manager.company_level

def check_company_name(company_name:str):
    """
    检查公司名是否合法
    """
    if not company_name:
        return f"公司名称不能为空"
    Manager.update_company_index()
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
    gold = Manager.group_wealths(group_id) + company.bank
    if gold < (limit := 15 * max_bet_gold):
        return f"本群金币（{round(gold,2)}）小于{limit}，注册失败。"
    if (gini := Manager.Gini(group_id)) > 0.56:
        return f"本群基尼系数（{round(gini,3)}）过高，注册失败。"
    company = group_data[group_id].company
    company.company_id = group_id
    company.company_name = company_name
    company.time = time.time()
    company.level = min(10,sum(group_data[group_id].Achieve_revolution.values()) + 1)
    company.issuance = 20000*company.level
    company.stock = company.issuance
    gold = gold * company.level
    company.gold = gold * 0.8
    company.float_gold = company.gold
    company.group_gold = gold
    company.intro = f"发行初始信息\n金币 {round(gold,2)}\n基尼系数{round(gini,3)}\n{company_name} 名称检查通过\n发行成功！"
    Manager.update_company_index()
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
    Manager.update_company_index()
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
    group_account.value = value/company_level(group_id)
    return value

def bank(event:GroupMessageEvent,sign:int, gold:int):
    """
    群金库存取
    """
    user,group_account = Manager.locate_user(event)
    company = group_data[group_account.group_id].company
    if sign == 1:
        if company.bank < gold:
            return f"金币不足。本群金库还有{company.bank}枚金币。"
        tip = "取出"
    else:
        if group_account.gold < gold:
            return f"金币不足。你还有{group_account.gold}枚金币。"
        tip = "存入"
    user.gold += sign*gold
    group_account.gold += sign*gold
    company.bank -= sign*gold
    return f"你{tip}了{gold}金币。"

def buy(event:MessageEvent, buy:int, company_name:str ,limit:float):
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

    group_gold = Manager.group_wealths(company_id,company.level) + company.bank*company.level
    if group_gold < 10 * company.level * max_bet_gold:
        return f"【{company_name}】金币过少({round(group_gold,2)})，无法交易。"
    float_gold = company.float_gold
    SI = company.issuance
    my_gold_level = company_level(group_account.group_id)
    my_gold = my_gold_level * group_account.gold
    value = 0.0
    inner_buy = 0
    limit = limit if limit else float('inf')
    for _ in range(buy):
        unit = max(group_gold, float_gold)/SI
        if unit > limit:
            tip = f"你的金币不足（{group_account.gold}）。"
            break
        value += unit
        if value > my_gold:
            tip = f"价格超过限制（{limit}）。"
            break
        float_gold += unit
        inner_buy += 1
    else:
        tip = ""
    if inner_buy < 1:
        return f"购买失败，{tip}"
    # 结算股票
    company.stock -= inner_buy
    group_account.stocks[company_id] = group_account.stocks.get(company_id,0) + inner_buy
    # 结算金币
    gold = math.ceil(value/my_gold_level)
    user.gold -= gold
    group_account.gold -= gold
    company.gold += value
    company.float_gold = float_gold
    company.group_gold = group_gold
    # 更新群账户信息
    value_update(group_account)
    return (
        f"{company_name}\n"
        "——————————\n"
        f"数量：{inner_buy}\n"
        f"单价：{round(value/inner_buy,2)}\n"
        f"总计：{math.ceil(value)}（{gold}）\n"
        "——————————\n"
        "交易成功！"
        )

def settle(event:MessageEvent, settle:int, company_name:str, limit:float):
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
    settle = min(settle,my_stock)
    if settle < 1:
        return f"您未持有 {company_name}"
    company = group_data[company_id].company
    company_name = company.company_name
    group_gold = Manager.group_wealths(company_id,company.level) + company.bank*company.level
    if group_gold < 10 * company.level * max_bet_gold:
        return f"【{company_name}】金币过少({group_gold})，无法交易。"
    float_gold = company.float_gold
    SI = company.issuance
    if float_gold < SI:
        return f"【{company_name}】单价过低({round(float_gold/SI,2)})，无法交易。"
    my_gold_level = company_level(group_account.group_id)
    value = 0.0
    inner_settle = 0
    limit = limit if limit else 1
    for _ in range(settle):
        unit = float_gold/SI
        if unit < limit:
            break
        value += unit
        float_gold -= unit
        inner_settle += 1
    gold = value/my_gold_level
    if group_account.props.get("42001",0):
        fee = 0
        tips = f"『{props_library['42001']['name']}』免手续费"
    else:
        fee = int(gold * 0.02)
        company.bank += int(value * 0.02 / company.level)
        tips = f"扣除2%手续费：{fee}"
    # 结算股票
    company.stock += inner_settle
    if group_account.stocks[company_id] == inner_settle:
        del group_account.stocks[company_id]
        stock = 0
    else:
        stock = group_account.stocks[company_id] = group_account.stocks.get(company_id) - inner_settle
    # 结算金币
    gold = int(gold) - fee
    user.gold += gold
    group_account.gold += gold
    company.gold -= value
    company.group_gold = group_gold
    company.float_gold = float_gold
    # 更新交易市场
    user_id = user.user_id
    if user_id in company.exchange:
        exchange = company.exchange[user_id]
        if exchange.group_id == group_account.group_id:
            if stock < exchange.n:
                exchange.n = stock
    # 更新群账户信息
    value_update(group_account)
    return (
        f"{company_name}\n"
        "——————————\n"
        f"数量：{inner_settle}\n"
        f"单价：{round(value/inner_settle,2)}\n"
        f"总计：{int(value)}（{gold+fee}）\n"
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

    rank = [(user_id,exchange) for user_id,exchange in company.exchange.items() if user_id != user.user_id and exchange.n > 0]
    if not rank:
        return f"没有正在出售的 {company_name}"
    rank.sort(key = lambda x:x[1].quote)

    value = 0.0
    Exlist = []
    level = company_level(group_account.group_id)
    my_gold = group_account.gold * level
    for user_id,exchange in rank:
        n = exchange.n
        Exlist.append([user_id,n])
        if buy < n:
            Exlist[-1][1] = buy
            break
        buy -= n
        unsettled = exchange.quote * n
        value += unsettled
        if value > my_gold:
            return f"你的金币不足（{group_account.gold}）"
    value = 0.0
    count = 0
    group_account.stocks.setdefault(company_id,0)
    for user_id,n in Exlist:
        exchange = company.exchange[user_id]
        # 定位卖家
        seller_user = user_data[user_id]
        seller_group_account = seller_user.group_accounts[exchange.group_id]
        seller_level = company_level(exchange.group_id)
        # 记录信息
        unsettled = exchange.quote * n
        value += unsettled
        count += n
        # 卖家金币结算
        unsettled = math.ceil(unsettled/seller_level)
        seller_user.gold += unsettled
        seller_group_account.gold += unsettled
        # 股票结算
        seller_group_account.stocks[company_id] -= n
        group_account.stocks[company_id] += n
        # 更新卖家群账户信息
        value_update(seller_group_account)
        exchange.n -= n
    # 买家金币结算
    gold = math.ceil(value/level)
    user.gold -= gold
    group_account.gold -= gold
    # 更新买家群账户信息
    value_update(group_account)
    company.exchange = {k:v for k,v in company.exchange.items() if v.n > 0}

    return (
        f"{company_name}\n"
        "——————————\n"
        f"数量：{count}\n"
        f"单价：{round(value/count,2)}\n"
        f"总计：{math.ceil(value)}（{gold}）\n"
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
        group_gold = Manager.group_wealths(company_id,company.level) + company.bank*company.level
        float_gold = company.float_gold
        SI = company.issuance
        if quote < 1 or quote > max(bet_gold, (min(group_gold,float_gold)*10) / SI):
            return "报价异常，发布失败。"
        else:
            if user_id in exchange:
                tips = "交易信息已修改。"
            else:
                tips = "交易信息发布成功！"
            exchange[user_id] = exchange_info

        # 自动结算交易市场上的股票
        value = 0.0
        inner_settle = 0
        for _ in range(n):
            unit = float_gold/SI
            if unit < quote:
                break
            value += quote
            float_gold -= quote
            inner_settle += 1

        if inner_settle > 0:
            # 结算股票
            company.Buyback(group_account,inner_settle)
            # 结算金币
            my_gold_level = company_level(group_account.group_id)
            gold = int(value/my_gold_level)
            user.gold += gold
            group_account.gold += gold
            company.gold -= value
            company.float_gold = float_gold
        company.group_gold = group_gold

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
    try:
        group_info = await bot.get_group_info(group_id = group_id)
    except:
        group_info = {"group_name":"群聊已注销","member_count":3000}
    group_name = group_info["group_name"]
    member_count = group_info["member_count"]
    member_count = member_count if member_count else 3000

    info.append(await group_info_head(group_name, company_name, group_id, (len(group.namelist),member_count)))

    ranklist = list(group.Achieve_revolution.items())
    if ranklist:
        ranklist.sort(key=lambda x:x[1],reverse=True)
        msg = "".join(f"{user_data.get_nickname(user_id,group_id)}[nowrap]\n[right]{n}次\n" for user_id,n in ranklist[:10])
        info.append(linecard(msg, width = 880, endline = "路灯挂件"))

    # 加载公司信息
    if company_name:
        msg = (
            f"公司等级 {company.level}\n"
            f"成立时间 {datetime.datetime.fromtimestamp(company.time).strftime('%Y 年 %m 月 %d 日')}\n"
            f"账户金额 {'{:,}'.format(company.bank)}\n"
            )
        info.append(linecard(msg + stock_profile(company), width = 880, endline = "注册信息"))

        p = OHLC(path, group_id)

        overtime = time.time() + 30
        while (returncode := p.poll()) == None:
            if time.time() > overtime:
                returncode = 1
                break
            await asyncio.sleep(0.5)

        if returncode == 0:
            info.append(Image.open(path / "candlestick" / f"{group_id}.png"))
        ranklist = [(user_id,exchange) for user_id,exchange in company.exchange.items() if exchange.n > 0]
        if ranklist:
            ranklist.sort(key=lambda x:x[1].quote)
            msg = "".join(f"{user_data[user_id].nickname}\n[pixel][20]单价 {exchange.quote}[nowrap]\n[pixel][400]数量 {exchange.n}\n" for user_id,exchange in ranklist[:10])
            info.append(linecard(msg, width = 880, font_size = 40,endline = "市场详情"))

        msg = company.intro
        if msg:
            info.append(linecard(msg + '\n', width = 880, font_size = 40,endline = "公司介绍"))

    return MessageSegment.image(info_splicing(info, Manager.BG_path(event.user_id)))

def stock_profile(company:Company) -> str:
    """
    产业信息
    """
    group_gold = company.group_gold
    float_gold = company.float_gold
    SI = company.issuance
    msg = (
        f"固定资产 {'{:,}'.format(round(company.gold,2))}\n"
        f"市场流动 {'{:,}'.format(round(group_gold))}\n"
        f"发行价格 {'{:,}'.format(round(max(group_gold,float_gold)/SI,2))}\n"
        f"结算价格 {'{:,}'.format(round(float_gold/SI,2))}\n"
        f"股票数量 {company.stock}\n"
        )
    return msg

def Market_info_All(event:MessageEvent):
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
    return MessageSegment.image(linecard_to_png("----\n".join(f"{company.company_name}\n----\n{stock_profile(company)}" for company in companys)[:-1]))

def pricelist(user_id:int):
    """
    市场价格表
    """
    global company_index
    company_ids = set([company_index[company_id] for company_id in company_index])
    companys = []
    for company_id in company_ids:
        company = group_data[company_id].company
        companys.append(company)
    if not companys:
        return "市场为空"

    companys.sort(key = lambda x:x.group_gold, reverse = True)

    def result(company:Company) -> str:
        group_gold = company.group_gold
        float_gold = company.float_gold
        SI = company.issuance
        gold = max(group_gold,float_gold)
        stock = company.stock
        return (
            "----\n"
            f"[pixel][20]{company.company_name}\n"
            f"[pixel][20]发行 [nowrap]\n[color][{'green' if gold == float_gold else 'red'}]{'{:,}'.format(round(gold/SI,2))}[nowrap]\n"
            f"[pixel][300]结算 [nowrap]\n[color][green]{'{:,}'.format(round(float_gold/SI,2))}[nowrap]\n"
            f"[pixel][600]数量 [nowrap]\n[color][{'green' if stock else 'red'}]{stock}\n"
            )

    return MessageSegment.image(
        info_splicing([linecard(
            "".join(result(company) for company in companys),
            width = 880,
            endline = "市场价格表")], Manager.BG_path(user_id)))

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
    group_gold = company.group_gold = Manager.group_wealths(company_id,company.level) + company.bank * company.level
    # 固定资产回归值 = 全群金币数 + 股票融资
    SI = company.issuance
    line = group_gold * (2  - company.stock / SI)
    # 公司金币数回归到固定资产回归值
    gold = company.gold
    gold += (line - gold)/96
    company.gold = gold
    if gold > 0.0:
        # 股票价格变化 = 趋势性影响（正态分布） + 随机性影响（平均分布）
        float_gold = company.float_gold
        float_gold += float_gold * random.gauss(0,0.03) + gold * random.uniform(-0.1, 0.1)
        # 股票价格向债务价值回归
        deviation = gold - float_gold
        float_gold +=  0.1 * deviation * abs(deviation / gold)
        # Nan检查
        float_gold = group_gold if math.isnan(float_gold) else float_gold
        # 自动结算交易市场上的股票
        Exlist = []
        for user_id,exchange in company.exchange.items():
            if not (user := user_data.get(user_id)):
                exchange.n = 0
                continue
            if not (group_account := user.group_accounts.get(exchange.group_id)):
                exchange.n = 0
                continue

            quote = exchange.quote
            value = 0.0
            inner_settle = 0
            for _ in range(exchange.n):
                unit = float_gold/SI
                if unit < quote:
                    break
                value += quote
                float_gold -= quote
                inner_settle += 1

            if not inner_settle:
                continue
            # 结算股票
            company.Buyback(group_account,inner_settle)
            # 结算金币
            gold = int(value / company_level(exchange.group_id))
            user.gold += gold
            group_account.gold += gold
            company.gold -= value
        # 清理无效交易信息
        company.exchange = {user_id:exchange for user_id,exchange in company.exchange.items() if exchange.n > 0}
    else:
        float_gold = 0.0
    # 更新浮动价格
    company.float_gold = float_gold
    # 记录价格历史
    global market_history
    market_history.setdefault(company_id,[]).append((time.time(), group_gold / SI, float_gold / SI))
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

def new_order():
    """
    发布订单
    """
    company_ids = set([company_index[company_id] for company_id in company_index])
    for company_id in company_ids:
        company = group_data[company_id].company
        orders = company.orders
        for i in range(company.level):
            i = str(i+1)
            if i in orders:
                continue
            else:
                orders[i] = Alchemy.random_products(10)

def alchemy_order(event:MessageEvent):
    """
    查看元素订单
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    orders = group_data[group_account.group_id].company.orders
    if not orders:
        return "今日本群元素订单已完成。"
    def result(order:dict) -> str:
        lst = [(min(user.alchemy.get(code,0),999), order.get(code,0)) for code in ['5','6','7','8','9','0']]
        return(
            f"[color][{'red' if lst[0][0] < lst[0][1] else 'green'}][pixel][20]{Alchemy.ProductsName['5']} {lst[0][1]}/{lst[0][0]}[nowrap]\n"
            f"[color][{'red' if lst[1][0] < lst[1][1] else 'green'}][pixel][300]{Alchemy.ProductsName['6']} {lst[1][1]}/{lst[1][0]}[nowrap]\n"
            f"[color][{'red' if lst[2][0] < lst[2][1] else 'green'}][pixel][600]{Alchemy.ProductsName['7']} {lst[2][1]}/{lst[2][0]}\n"
            f"[color][{'red' if lst[3][0] < lst[3][1] else 'green'}][pixel][20]{Alchemy.ProductsName['8']} {lst[3][1]}/{lst[3][0]}[nowrap]\n"
            f"[color][{'red' if lst[4][0] < lst[4][1] else 'green'}][pixel][300]{Alchemy.ProductsName['9']} {lst[4][1]}/{lst[4][0]}[nowrap]\n"
            f"[color][{'red' if lst[5][0] < lst[5][1] else 'green'}][pixel][600]{Alchemy.ProductsName['0']} {lst[5][1]}/{lst[5][0]}\n"
            )
    info = [linecard(result(order),width = 880,endline = f"编号{i}") for i,order in orders.items()]
    return MessageSegment.image(info_splicing(info, Manager.BG_path(group_account.user_id),5))

def complete_order(event:MessageEvent,key:str):
    """
    完成元素订单
    """
    if not key:
        return "未指定订单编号"
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    company = group_data[group_account.group_id].company
    orders = company.orders
    if not orders:
        return "今日本群元素订单已完成。"
    order = orders.get(key) 
    if not order:
        return f"不存在元素订单编号【{key}】"
    tip = ""
    for k,v in order.items():
        n = user.alchemy.get(k,0)
        if n < v:
            tip += f"\n{Alchemy.ProductsName[k]} {v - n}个"
    if tip:
        return f"你的元素不足,你还需要：{tip}"
    for k,v in order.items():
        user.alchemy[k] -= v
    gold = random.randint(10,30) * gacha_gold
    user.gold += gold
    group_account.gold += gold
    company.bank += gacha_gold * 2
    del orders[key]
    return f"恭喜您完成了订单{key}，您获得了{gold}金币。"

def reset():
    """
    市场重置
    """
    company_ids = set([company_index[company_id] for company_id in company_index])
    for company_id in company_ids:
        company = group_data[company_id].company
        group_gold = company.group_gold = Manager.group_wealths(company_id,company.level) + company.bank*company.level
        company.gold = company.float_gold = group_gold * (2  - company.stock / company.issuance)