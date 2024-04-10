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


@reg_command("alchemy_order", {"查看元素订单"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    orders = Manager.locate_group(group_account.group_id).company.orders
    if not orders:
        return "今日本群元素订单已完成。"

    def result(order: dict) -> str:
        lst = [(min(user.alchemy.get(code, 0), 999), order.get(code, 0)) for code in ["5", "6", "7", "8", "9", "0"]]
        return (
            f"[color][{'red' if lst[0][0] < lst[0][1] else 'green'}][pixel][20]{Alchemy.ProductsName['5']} {lst[0][1]}/{lst[0][0]}[nowrap]\n"
            f"[color][{'red' if lst[1][0] < lst[1][1] else 'green'}][pixel][300]{Alchemy.ProductsName['6']} {lst[1][1]}/{lst[1][0]}[nowrap]\n"
            f"[color][{'red' if lst[2][0] < lst[2][1] else 'green'}][pixel][600]{Alchemy.ProductsName['7']} {lst[2][1]}/{lst[2][0]}\n"
            f"[color][{'red' if lst[3][0] < lst[3][1] else 'green'}][pixel][20]{Alchemy.ProductsName['8']} {lst[3][1]}/{lst[3][0]}[nowrap]\n"
            f"[color][{'red' if lst[4][0] < lst[4][1] else 'green'}][pixel][300]{Alchemy.ProductsName['9']} {lst[4][1]}/{lst[4][0]}[nowrap]\n"
            f"[color][{'red' if lst[5][0] < lst[5][1] else 'green'}][pixel][600]{Alchemy.ProductsName['0']} {lst[5][1]}/{lst[5][0]}\n"
        )

    info = [linecard(result(order), width=880, endline=f"编号{i}") for i, order in orders.items()]
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
