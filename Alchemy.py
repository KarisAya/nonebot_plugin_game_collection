from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    Message,
    MessageSegment
    )
from collections import Counter

import random

from .utils.chart import info_splicing, alchemy_info
from . import Manager

data = Manager.data
user_data = data.user
group_data = data.group

class Alchemy:
    elements  = ["1","2","3","4"]
    ProductsLibrary = {
        "1":"1",
        "2":"2",
        "3":"3",
        "4":"4",
        "12":"5",
        "21":"5",
        "13":"6",
        "31":"6",
        "14":"7",
        "41":"7",
        "23":"8",
        "32":"8",
        "24":"9",
        "42":"9",
        "34":"0",
        "43":"0",
        }
    ProductsName = {
        "":"以太",
        "1":"水",
        "2":"火",
        "3":"土",
        "4":"风",
        "5":"蒸汽",
        "6":"沼泽",
        "7":"寒冰",
        "8":"岩浆",
        "9":"雷电",
        "0":"尘埃"
        }
    @classmethod
    def do(cls,N:int):
        """
        炼金
        """
        result = Counter()
        for _ in range(N):
            product = cls.ProductsLibrary.get("".join(list(set(random.choices(cls.elements,k = 3)))),"")
            result[product] += 1
        return result

    @classmethod
    def status(cls,status:dict):
        """
        元素状态
        """
        result = Counter()
        for product,N in status.items():
            result += {k:v*N for k,v in cls.ProductsProperties[product].items()}
        return result

async def my_info(event:MessageEvent) -> Message:
    """
    炼金资料卡
    """
    user,group_account = Manager.locate_user(event)
    return MessageSegment.image(info_splicing(await alchemy_info(user,group_account.nickname if group_account else user.nickname),Manager.BG_path(user.user_id),5))
