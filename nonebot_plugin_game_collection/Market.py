from collections import Counter
import random
import time
import math
import datetime

from .data import Company, ExchangeInfo
from .Processor import Event, Result, reg_command
from .Alchemy import Alchemy
from . import Prop
from . import Manager

from .utils.chart import (
    linecard,
    linecard_to_png,
    group_info_head,
    group_info_account,
    info_splicing,
)
from .utils.utils import format_number
from .config import gacha_gold, max_bet_gold


def check_company_name(company_name: str):
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


@reg_command(
    "company_public", {"市场注册", "公司注册", "注册公司"}, need_extra_args={"to_me", "permission"}
)
async def _(event: Event) -> Result:
    if event.is_private() or not (event.permission() and event.to_me()):
        return
    company_name = event.single_arg()
    group_id = event.group_id
    group = Manager.locate_group(group_id)
    company = group.company
    if company.company_name:
        return f"本群已在市场注册，注册名：{company.company_name}"
    if check := check_company_name(company_name):
        return check
    gold = Manager.group_wealths(group_id)
    if gold < (limit := 15 * max_bet_gold):
        return f"本群金币（{round(gold,2)}）小于{limit}，注册失败。"
    gini = Manager.gini_coef(group_id)
    if gini > 0.56:
        return f"本群基尼系数（{round(gini,3)}）过高，注册失败。"
    company.company_id = group_id
    company.company_name = company_name
    company.time = time.time()
    company.level = min(20, sum(group.Achieve_revolution.values()) + 1)
    company.stock = company.issuance = 20000 * company.level
    company.group_gold = gold * company.level
    company.float_gold = company.gold = company.group_gold * 0.8
    company.intro = (
        f"发行初始信息\n金币 {round(gold,2)}\n基尼系数{round(gini,3)}\n{company_name} 名称检查通过\n发行成功！"
    )
    update_company_index()
    return f"{company_name}发行成功，发行价格为每股{round((gold/ 20000),2)}金币"


@reg_command("company_rename", {"公司重命名"}, need_extra_args={"to_me", "permission"})
async def _(event: Event) -> Result:
    if event.is_private() or not (event.permission() and event.to_me()):
        return
    company_name = event.single_arg()
    group_id = event.group_id
    company = Manager.locate_group(group_id).company
    if not company.company_name:
        return "本群未在市场注册，不可重命名。"
    user = Manager.locate_user(event)[0]
    if user.props.get("33001", 0) < 1:
        return f"你的【{Prop.get_prop_name('33001')}】已失效"
    if check := check_company_name(company_name):
        return check
    old_company_name = company.company_name
    company.company_name = company_name
    update_company_index()
    return f"【{old_company_name}】已重命名为【{company_name}】"


@reg_command(
    "bank_gold", {"存金币", "取金币", "查看群金库", "群金库查看"}, need_extra_args={"permission"}
)
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    company = Manager.locate_group(group_account.group_id).company
    if event.raw_command == "取金币":
        if not event.permission():
            return
        gold = event.args_to_int()
        if company.bank < gold:
            return f"金币不足。本群金库还有{company.bank}枚金币。"
        tip = "取出"
        sign = 1
    elif event.raw_command == "存金币":
        gold = event.args_to_int()
        if group_account.gold < gold:
            return f"金币不足。你还有{group_account.gold}枚金币。"
        tip = "存入"
        sign = -1
    else:
        invest_info = []
        for inner_company_id, stock in company.invest.items():
            inner_company = Manager.locate_group(inner_company_id).company
            inner_company_name = inner_company.company_name
            inner_company_gold = "{:,}".format(
                round(inner_company.float_gold / inner_company.issuance, 2)
            )
            invest_info.append(
                f"[pixel][20]公司 {inner_company_name}\n[pixel][20]结算 [nowrap]\n[color][green]{inner_company_gold}[nowrap]\n[pixel][400]数量 [nowrap]\n[color][green]{stock}"
            )
        if not invest_info:
            return f"本群金库还有{company.bank}枚金币。"
        else:
            info = []
            info.append(
                linecard(
                    f"[pixel][20]金币 {'{:,}'.format(company.bank)}\n",
                    width=880,
                    endline=f"金库等级：Lv{company.level}",
                )
            )
            info.append(
                linecard("\n----\n".join(invest_info) + "\n", width=880, endline="投资信息")
            )
            return info_splicing(info, Manager.BG_path(event.user_id))
    gold = sign * gold
    user.gold += gold
    group_account.gold += gold
    company.bank -= gold
    return f"你{tip}了{abs(gold)}金币。"


@reg_command("bank_invest", {"存股票", "取股票"}, need_extra_args={"permission"})
async def _(event: Event) -> Result:
    group_account = Manager.locate_user(event)[1]
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    company_name, count, _ = event.args_parse()
    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"
    company = Manager.locate_group(group_account.group_id).company
    if event.raw_command == "取股票":
        if not event.permission():
            return
        invest = company.invest
        tip = "取出"
        sign = 1
    else:
        invest = group_account.invest
        tip = "存入"
        sign = -1
    count = min(invest.get(company_id, 0), count)
    if count < 1:
        return f"数量不足，无法{tip}：{company_name}"
    group_account.invest[company_id] = (
        group_account.invest.get(company_id, 0) + sign * count
    )
    company = Manager.locate_group(group_account.group_id).company
    company.invest[company_id] = company.invest.get(company_id, 0) - sign * count
    return f"你{tip}了{count}个{company_name}"


@reg_command("Market_buy", {"购买", "发行购买"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    company_name, buy, limit = event.args_parse()
    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"
    company = Manager.locate_group(company_id).company
    company_name = company.company_name
    buy = min(company.stock, buy)
    if buy < 1:
        return "已售空，请等待结算或在交易市场购买。"

    group_gold = Manager.group_wealths(company_id, company.level)
    if group_gold < 10 * company.level * max_bet_gold:
        return f"【{company_name}】金币过少({round(group_gold,2)})，无法交易。"
    float_gold = company.float_gold
    SI = company.issuance
    my_gold_level = Manager.locate_group(group_account.group_id).company.level
    my_gold = my_gold_level * group_account.gold
    value = 0.0
    inner_buy = 0
    limit = limit if limit else float("inf")
    for _ in range(buy):
        unit = max(group_gold, float_gold) / SI
        if unit > limit:
            tip = f"价格超过限制（{limit}）。"
            break
        value += unit
        if value > my_gold:
            tip = f"你的金币不足（{group_account.gold}）。"
            break
        float_gold += unit
        inner_buy += 1
    else:
        tip = ""
    if inner_buy < 1:
        return f"购买失败，{tip}"
    # 结算股票
    company.stock -= inner_buy
    group_account.invest[company_id] = (
        group_account.invest.get(company_id, 0) + inner_buy
    )
    # 结算金币
    gold = math.ceil(value / my_gold_level)
    user.gold -= gold
    group_account.gold -= gold
    company.gold += value
    company.float_gold = float_gold
    company.group_gold = group_gold
    return (
        f"{company_name}\n"
        "——————————\n"
        f"数量：{inner_buy}\n"
        f"单价：{round(value/inner_buy,2)}\n"
        f"总计：{math.ceil(value)}（{gold}）\n"
        "——————————\n"
        "交易成功！"
    )


@reg_command("Market_settle", {"结算", "官方结算"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    company_name, settle, limit = event.args_parse()
    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"
    my_stock = group_account.invest.get(company_id, 0)
    settle = min(settle, my_stock)
    if settle < 1:
        return f"您未持有 {company_name}"
    company = Manager.locate_group(company_id).company
    company_name = company.company_name
    group_gold = Manager.group_wealths(company_id, company.level)
    if group_gold < 10 * company.level * max_bet_gold:
        return f"【{company_name}】金币过少({group_gold})，无法交易。"
    float_gold = company.float_gold
    SI = company.issuance
    if float_gold < SI:
        return f"【{company_name}】单价过低({round(float_gold/SI,2)})，无法交易。"
    my_gold_level = Manager.locate_group(group_account.group_id).company.level
    value = 0.0
    inner_settle = 0
    limit = limit if limit else 1
    for _ in range(settle):
        unit = float_gold / SI
        if unit < limit:
            break
        value += unit
        float_gold -= unit
        inner_settle += 1
    gold = value / my_gold_level
    if group_account.props.get("42001", 0):
        fee = 0
        tips = f"『{Prop.get_prop_name('42001')}』免手续费"
    else:
        fee = int(gold * 0.02)
        company.bank += int(value * 0.02 / company.level)
        tips = f"扣除2%手续费：{fee}"
    # 结算股票
    company.stock += inner_settle
    if group_account.invest[company_id] == inner_settle:
        del group_account.invest[company_id]
        stock = 0
    else:
        stock = group_account.invest[company_id] = (
            group_account.invest.get(company_id) - inner_settle
        )
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
    return (
        f"{company_name}\n"
        "——————————\n"
        f"数量：{inner_settle}\n"
        f"单价：{round(value/inner_settle,2)}\n"
        f"总计：{int(value)}（{gold+fee}）\n"
        "——————————\n"
        "交易成功！\n" + tips
    )


@reg_command("Exchange_buy", {"市场购买"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    company_name, buy, _ = event.args_parse()
    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"

    company = Manager.locate_group(company_id).company
    company_name = company.company_name

    rank = [
        (user_id, exchange)
        for user_id, exchange in company.exchange.items()
        if user_id != user.user_id and exchange.n > 0
    ]
    if not rank:
        return f"没有正在出售的 {company_name}"
    rank.sort(key=lambda x: x[1].quote)

    value = 0.0
    Exlist = []
    level = Manager.locate_group(group_account.group_id).company.level
    my_gold = group_account.gold * level
    for user_id, exchange in rank:
        n = exchange.n
        Exlist.append([user_id, n])
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
    group_account.invest.setdefault(company_id, 0)
    for user_id, n in Exlist:
        exchange = company.exchange[user_id]
        # 定位卖家
        seller_user, seller_group_account = Manager.locate_user_at(
            user_id, exchange.group_id
        )
        seller_level = Manager.locate_group(exchange.group_id).company.level
        # 记录信息
        unsettled = exchange.quote * n
        value += unsettled
        count += n
        # 卖家金币结算
        unsettled = math.ceil(unsettled / seller_level)
        seller_user.gold += unsettled
        seller_group_account.gold += unsettled
        # 股票结算
        seller_group_account.invest[company_id] -= n
        group_account.invest[company_id] += n
        exchange.n -= n
    # 买家金币结算
    gold = math.ceil(value / level)
    user.gold -= gold
    group_account.gold -= gold
    company.exchange = {k: v for k, v in company.exchange.items() if v.n > 0}

    return (
        f"{company_name}\n"
        "——————————\n"
        f"数量：{count}\n"
        f"单价：{round(value/count,2)}\n"
        f"总计：{math.ceil(value)}（{gold}）\n"
        "——————————\n"
        "交易成功！"
    )


@reg_command("Exchange_sell", {"出售", "市场出售", "卖出", "上架", "发布交易信息"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    company_name, n, quote = event.args_parse()
    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"
    my_stock = group_account.invest.get(company_id, 0)
    if my_stock < n:
        return f"你的账户中没有足够的股票（{my_stock}）。"
    user_id = user.user_id
    company = Manager.locate_group(company_id).company
    exchange = company.exchange
    if n < 1:
        quote = 0
        n = 0
        if exchange.get(user_id):
            del exchange[user_id]
            tips = "交易信息已注销。"
        else:
            tips = "交易信息无效。"
    else:
        if not quote:
            return
        group_gold = Manager.group_wealths(company_id, company.level)
        float_gold = company.float_gold
        SI = company.issuance
        if user_id in exchange:
            tips = "交易信息已修改。"
        else:
            tips = "交易信息发布成功！"
        exchange[user_id] = ExchangeInfo(
            group_id=group_account.group_id, quote=quote, n=n
        )
        # 自动结算交易市场上的股票
        value = 0.0
        inner_settle = 0
        for _ in range(n):
            unit = float_gold / SI
            if unit < quote:
                break
            value += quote
            float_gold -= quote
            inner_settle += 1

        if inner_settle > 0:
            # 结算股票
            company.Buyback(group_account, inner_settle)
            # 结算金币
            my_gold_level = Manager.locate_group(group_account.group_id).company
            gold = int(value / my_gold_level)
            user.gold += gold
            group_account.gold += gold
            company.gold -= value
            company.float_gold = float_gold
        company.group_gold = group_gold

    return (
        f"{company.company_name}\n"
        "——————————\n"
        f"报价：{quote}\n"
        f"数量：{n}\n"
        "——————————\n" + tips
    )


async def group_info(group_id, bg_id: str = None) -> Result:
    """
    群资料卡
    """
    info = []
    # 加载群信息
    group = Manager.locate_group(group_id)
    company = group.company
    company_name = group.company.company_name
    info.append(group_info_head(company_name or "未注册", group_id, len(group.namelist)))
    # 加载公司信息
    if company_name:
        # 注册信息
        msg = (
            f"公司等级 {company.level}\n"
            f"成立时间 {datetime.datetime.fromtimestamp(company.time).strftime('%Y 年 %m 月 %d 日')}\n"
        )
        info.append(linecard(msg + stock_profile(company), width=880, endline="注册信息"))
        # 蜡烛图
        ohlc = await Manager.candlestick(group_id)
        if ohlc:
            info.append(ohlc)
        # 资产分布
        invist = Counter(company.invest)
        for inner_user_id in group.namelist:
            invist += Counter(Manager.locate_user_at(inner_user_id, group_id)[1].invest)
        dist = []
        for inner_company_id, n in invist.items():
            inner_company = Manager.locate_group(inner_company_id).company
            inner_company_name = (
                inner_company.company_name or f"（{str(inner_company_id)[-4:]}）"
            )
            unit = max(inner_company.float_gold / inner_company.issuance, 0)
            dist.append([unit * n, inner_company_name])

        if dist:
            info.append(group_info_account(company, dist))

        ranklist = [
            (inner_user_id, exchange)
            for inner_user_id, exchange in company.exchange.items()
            if exchange.n > 0
        ]
        if ranklist:
            ranklist.sort(key=lambda x: x[1].quote)

            def result(inner_user_id, exchange):
                nickname = Manager.get_user(inner_user_id).nickname
                nickname = nickname if len(nickname) < 7 else nickname[:6] + ".."
                return f"[pixel][20]{nickname}[nowrap]\n[pixel][300]单价 {exchange.quote}[nowrap]\n[pixel][600]数量 {exchange.n}\n"

            msg = "".join(
                result(inner_user_id, exchange)
                for inner_user_id, exchange in ranklist[:10]
            )
            info.append(linecard(msg, width=880, font_size=40, endline="市场详情"))

        msg = company.intro
        if msg:
            info.append(linecard(msg + "\n", width=880, font_size=40, endline="公司介绍"))

    # 路灯挂件
    ranklist = list(group.Achieve_revolution.items())
    if ranklist:
        ranklist.sort(key=lambda x: x[1], reverse=True)

        def result(inner_user_id, n):
            user, group_account = Manager.locate_user_at(inner_user_id, group_id)
            return f"{group_account.nickname or user.nickname}[nowrap]\n[right]{n}次\n"

        msg = "".join(result(inner_user_id, n) for inner_user_id, n in ranklist[:10])
        info.insert(min(len(info), 2), linecard(msg, width=880, endline="路灯挂件"))

    return info_splicing(info, Manager.BG_path(bg_id), 10)


def stock_profile(company: Company) -> str:
    """
    产业信息
    """
    group_gold = company.group_gold
    float_gold = company.float_gold
    SI = company.issuance
    rate = company.group_gold * (2 - company.stock / SI) / company.float_gold
    rate = rate - 1
    rate = f'{round(rate*100,2)}% {"↑[color][green]" if rate > 0 else "↓[color][red]"}'
    msg = (
        f"账户金额 {format_number(company.bank)}[nowrap]\n"
        f"[pixel][450]资产总量 {format_number(round(group_gold))}\n"
        f"发行价格 {'{:,}'.format(round(max(group_gold,float_gold)/SI,2))}[nowrap]\n"
        f"[pixel][450]结算价格 {'{:,}'.format(round(float_gold/SI,2))}\n"
        f"股票数量 {company.stock}[nowrap]\n"
        f"[pixel][450]回归趋势 [nowrap]\n{rate}\n"
    )
    return msg


def Market_info_All() -> Result:
    """
    市场信息总览
    """
    global company_index
    company_ids = set([company_index[company_id] for company_id in company_index])
    companys = [Manager.locate_group(company_id).company for company_id in company_ids]
    companys.sort(key=lambda x: x.group_gold, reverse=True)
    return linecard_to_png(
        "----\n".join(
            f"{company.company_name}\n----\n{stock_profile(company)}"
            for company in companys
        )[:-1],
        font_size=40,
        width=880,
    )


@reg_command("group_info", {"群资料卡"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    return await group_info(group_account.group_id, event.user_id)


@reg_command("Market_info", {"市场信息", "查看市场"})
async def _(event: Event) -> Result:
    company_name = event.single_arg(" ")
    if company_name == " ":
        return Market_info_All() if company_index else "市场不存在"
    if company_name in company_index:
        company_id = company_index[company_name]
    else:
        return f"没有 {company_name} 的注册信息"
    return await group_info(company_id, event.user_id)


def pricelist(user_id: int) -> Result:
    """
    市场价格表
    """
    global company_index
    company_ids = set(company_index[company_id] for company_id in company_index)
    companys = []
    for company_id in company_ids:
        company = Manager.locate_group(company_id).company
        companys.append(company)
    if not companys:
        return "市场为空"

    companys.sort(key=lambda x: x.group_gold, reverse=True)

    def result(company: Company) -> str:
        group_gold = company.group_gold
        float_gold = company.float_gold
        SI = company.issuance
        gold = max(group_gold, float_gold)
        stock = company.stock
        return (
            "----\n"
            f"[pixel][20]{company.company_name}\n"
            f"[pixel][20]发行 [nowrap]\n[color][{'green' if gold == float_gold else 'red'}]{'{:,}'.format(round(gold/SI,2))}[nowrap]\n"
            f"[pixel][300]结算 [nowrap]\n[color][green]{'{:,}'.format(round(float_gold/SI,2))}[nowrap]\n"
            f"[pixel][600]数量 [nowrap]\n[color][{'green' if stock else 'red'}]{stock}\n"
        )

    return info_splicing(
        [
            linecard(
                "".join(result(company) for company in companys),
                width=880,
                endline="市场价格表",
            )
        ],
        Manager.BG_path(user_id),
    )


@reg_command("Market_pricelist", {"市场价格表", "股票价格表"})
async def _(event: Event) -> Result:
    return pricelist(event.user_id)


@reg_command(
    "company_intro", {"更新公司简介", "添加公司简介", "修改公司简介"}, need_extra_args={"permission"}
)
async def _(event: Event) -> Result:
    if event.is_private() or not (event.permission() and event.to_me()):
        return
    group = Manager.locate_group(event.group_id)
    if not group:
        return "本群未注册"
    group.company.intro = " ".join(event.args)
    return "简介更新完成!"


@reg_command("alchemy_order", {"查看元素订单"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    orders = Manager.locate_group(group_account.group_id).company.orders
    if not orders:
        return "今日本群元素订单已完成。"

    def result(order: dict) -> str:
        lst = [
            (min(user.alchemy.get(code, 0), 999), order.get(code, 0))
            for code in ["5", "6", "7", "8", "9", "0"]
        ]
        return (
            f"[color][{'red' if lst[0][0] < lst[0][1] else 'green'}][pixel][20]{Alchemy.ProductsName['5']} {lst[0][1]}/{lst[0][0]}[nowrap]\n"
            f"[color][{'red' if lst[1][0] < lst[1][1] else 'green'}][pixel][300]{Alchemy.ProductsName['6']} {lst[1][1]}/{lst[1][0]}[nowrap]\n"
            f"[color][{'red' if lst[2][0] < lst[2][1] else 'green'}][pixel][600]{Alchemy.ProductsName['7']} {lst[2][1]}/{lst[2][0]}\n"
            f"[color][{'red' if lst[3][0] < lst[3][1] else 'green'}][pixel][20]{Alchemy.ProductsName['8']} {lst[3][1]}/{lst[3][0]}[nowrap]\n"
            f"[color][{'red' if lst[4][0] < lst[4][1] else 'green'}][pixel][300]{Alchemy.ProductsName['9']} {lst[4][1]}/{lst[4][0]}[nowrap]\n"
            f"[color][{'red' if lst[5][0] < lst[5][1] else 'green'}][pixel][600]{Alchemy.ProductsName['0']} {lst[5][1]}/{lst[5][0]}\n"
        )

    info = [
        linecard(result(order), width=880, endline=f"编号{i}")
        for i, order in orders.items()
    ]
    return info_splicing(info, Manager.BG_path(group_account.user_id), 5)


@reg_command("complete_order", {"完成元素订单"})
async def _(event: Event) -> Result:
    key = event.single_arg()
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    company = Manager.locate_group(group_account.group_id).company
    orders = company.orders
    if not orders:
        return "今日本群元素订单已完成。"
    order = orders.get(key)
    if not order:
        return f"不存在元素订单编号【{key}】"
    tip = ""
    for k, v in order.items():
        n = user.alchemy.get(k, 0)
        if n < v:
            tip += f"\n{Alchemy.ProductsName[k]} {v - n}个"
    if tip:
        return f"你的元素不足,你还需要：{tip}"
    for k, v in order.items():
        user.alchemy[k] -= v
    gold = random.randint(10, 30) * gacha_gold
    user.gold += gold
    group_account.gold += gold
    company.bank += gacha_gold * 2
    del orders[key]
    return f"恭喜您完成了订单{key}，您获得了{gold}金币。"


@reg_command("inherit_group", {"继承公司账户", "继承群账户"}, need_extra_args={"permission"})
async def _(event: Event) -> Result:
    if event.permission() != 3:
        return
    if len(event.args) != 3:
        return
    arrow = event.args[1]
    if arrow == "->":
        Deceased = event.args[0]
        Heir = event.args[2]
    elif arrow == "<-":
        Deceased = event.args[2]
        Heir = event.args[0]
    else:
        return "请输入:Deceased -> Heir"
    Deceased = company_index.get(Deceased) or Deceased
    Deceased = Manager.locate_group(Deceased)
    if not Deceased:
        return "被继承群不存在"
    Heir = company_index.get(Heir) or Heir
    Heir = Manager.locate_group(Heir)
    if not Heir:
        return "继承群不存在"
    if Deceased is Heir:
        return "无法继承自身"
    ExRate = Deceased.company.level / Heir.company.level
    gold_group = 0
    invest_group = Counter()
    gold_private = 0
    invest_private = Counter()
    # 继承群金库
    gold = math.ceil(Deceased.company.bank * ExRate)
    Heir.company.bank += gold
    gold_group += gold
    invest = Counter(Deceased.company.invest)
    Heir.company.invest = dict(Counter(Heir.company.invest) + invest)
    invest_group += invest
    # 继承群员账户
    for user_id in Deceased.namelist:
        Deceased_account = Manager.locate_user_at(user_id, Deceased.group_id)[1]
        gold = math.ceil(Deceased_account.gold * ExRate)
        invest = Counter(Deceased_account.invest)
        if user_id in Heir.namelist:
            Heir_account = Manager.locate_user_at(user_id, Heir.group_id)[1]
            Heir_account.gold += gold
            Heir_account.invest = dict(Counter(Heir_account.invest) + invest)
            gold_private += gold
            invest_private += invest
        else:
            Heir.company.bank += gold
            Heir.company.invest = dict(Counter(Heir.company.invest) + invest)
            gold_group += gold
            invest_group += invest

        del Manager.user_data[user_id].group_accounts[Deceased.group_id]

    def company_name(k):
        group = Manager.locate_group(k)
        if group:
            return Manager.locate_group(k).company.company_name

    invest_group_info = "\n".join(
        f">{company_name(k) or '已注销'}:{v}" for k, v in invest_group.items()
    )
    invest_private_info = "\n".join(
        f">{company_name(k) or '已注销'}:{v}" for k, v in invest_private.items()
    )
    del Manager.group_data[Deceased.group_id]
    update_company_index()
    Manager.data.verification()
    return (
        "继承已完成\n"
        ">群金库入账\n"
        f">金币:{gold_group}\n"
        f">投资:\n{invest_group_info}\n"
        ">个人账户总入账\n"
        f">金币:{gold_private}\n"
        f">投资:\n{invest_private_info}"
    )


def company_update(company: Company):
    """
    刷新公司信息
        company:公司账户
    """
    company_id = company.company_id
    # 更新全群金币数
    group_gold = company.group_gold = Manager.group_wealths(company_id, company.level)
    # 固定资产回归值 = 全群金币数 + 股票融资
    SI = company.issuance
    line = group_gold * (2 - company.stock / SI)
    # 公司金币数回归到固定资产回归值
    gold = company.gold
    gold += (line - gold) / 96
    company.gold = gold
    if gold > 0.0:
        # 股票价格变化 = 趋势性影响（正态分布） + 随机性影响（平均分布）
        float_gold = company.float_gold
        float_gold += float_gold * random.gauss(0, 0.03) + gold * random.uniform(
            -0.1, 0.1
        )
        # 股票价格向债务价值回归
        deviation = gold - float_gold
        float_gold += 0.1 * deviation * abs(deviation / gold)
        # Nan检查
        float_gold = group_gold if math.isnan(float_gold) else float_gold
        # 自动结算交易市场上的股票
        for user_id, exchange in company.exchange.items():
            if not (user := Manager.get_user(user_id)):
                exchange.n = 0
                continue
            if not (group_account := user.group_accounts.get(exchange.group_id)):
                exchange.n = 0
                continue

            quote = exchange.quote
            value = 0.0
            inner_settle = 0
            for _ in range(exchange.n):
                unit = float_gold / SI
                if unit < quote:
                    break
                value += quote
                float_gold -= quote
                inner_settle += 1

            if not inner_settle:
                continue
            # 结算股票
            company.Buyback(group_account, inner_settle)
            # 结算金币
            gold = int(value / Manager.locate_group(exchange.group_id).company.level)
            user.gold += gold
            group_account.gold += gold
            company.gold -= value
        # 清理无效交易信息
        company.exchange = {
            user_id: exchange
            for user_id, exchange in company.exchange.items()
            if exchange.n > 0
        }
    else:
        float_gold = 0.0
    # 更新浮动价格
    company.float_gold = float_gold
    # 记录价格历史
    Manager.market_history.record(
        company_id, (time.time(), group_gold / SI, float_gold / SI)
    )


def update():
    """
    刷新市场
    """
    log = []
    company_ids = set([company_index[company_id] for company_id in company_index])
    for company_id in company_ids:
        company = Manager.locate_group(company_id).company
        company_update(company)
        log.append(f"{company.company_name} 更新成功！")

    return "\n".join(log)


def new_order():
    """
    发布订单
    """
    company_ids = set([company_index[company_id] for company_id in company_index])
    for company_id in company_ids:
        company = Manager.locate_group(company_id).company
        orders = company.orders
        for i in range(company.level):
            i = str(i + 1)
            if i in orders:
                continue
            else:
                orders[i] = Alchemy.random_products(10)


company_index = {}


def update_company_index():
    """
    从群数据生成公司名查找群号的字典
    """
    company_index.clear()
    for group_id in Manager.group_data:
        company_name = Manager.locate_group(group_id).company.company_name
        if company_name:
            company_index[company_name] = group_id
            company_index[group_id] = group_id


update_company_index()
