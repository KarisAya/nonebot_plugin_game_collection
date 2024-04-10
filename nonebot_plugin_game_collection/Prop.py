from typing import Tuple, Dict, Callable
import random

from .data import UserDict, GroupAccount, props_library
from .Processor import Event, Result
from .Alchemy import Alchemy
from . import Manager
from .utils.chart import linecard_to_png, line_splicing
from .config import bot_name, sign_gold, revolt_gold, max_bet_gold, gacha_gold


@add_prop("初级元素")
def _(user: UserDict, group_account: GroupAccount, event: Event, count: int) -> Result:
    res = {}
    info = []
    if count <= 20:
        msg = ""
        for _ in range(count):
            originproduct = random.choices(Alchemy.elements, k=3)
            product = Alchemy.ProductsLibrary.get("".join(list(set(originproduct))), "")
            msg += f'|{"|".join(Alchemy.ProductsName[x] for x in originproduct)}| >>>> {Alchemy.ProductsName[product]}\n'
            res[product] = res.get(product, 0) + 1
        info.append(f"合成结果：\n----\n{msg[:-1]}")
    else:
        res = Alchemy.do(count)
    msg = ""
    for product, N in res.items():
        if product:
            user.alchemy[product] = user.alchemy.get(product, 0) + N
        msg += f"{Alchemy.ProductsName[product]}：{N}个\n"
    info.append(f"你获得了：\n----\n{msg[:-1]}")
    if count < 3:
        return "\n".join(info) + "\n祝你好运"
    else:
        return line_splicing(info)