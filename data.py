from typing import Dict
from pydantic import BaseModel
from pathlib import Path
import random
import math
try:
    import ujson as json
except ModuleNotFoundError:
    import json

from nonebot.adapters.onebot.v11 import MessageEvent,GroupMessageEvent

class GroupAccount(BaseModel):
    """
    用户群账户
    """
    user_id:int = None
    group_id:int = None
    nickname:str = None
    is_sign:bool = False
    revolution:bool = False
    security:int = 0
    gold:int = 0
    value:float = 0.0
    stocks:Dict[int,int] = {}
    props:Dict[str,int] = {}

    def __init__(self, event:GroupMessageEvent = None, **obj):
        """
        初始化群账户
        """
        super().__init__(**obj)
        if event:
            self.user_id = event.user_id
            self.group_id = event.group_id
            self.nickname = event.sender.card or event.sender.nickname

class UserDict(BaseModel):
    """
    用户字典
    """
    user_id:int = None
    nickname:str = None
    gold:int = 0
    win:int = 0
    lose:int = 0
    Achieve_win:int = 0
    Achieve_lose:int = 0
    group_accounts:Dict[int,GroupAccount] = {}
    connect:int = 0
    transfer_limit:int = 0
    props:Dict[str,int] = {}
    alchemy:Dict[str,int] = {}

    def __init__(self, event:MessageEvent = None, **obj):
        """
        初始化用户字典
        """
        super().__init__(**obj)
        if event:
            self.user_id = event.user_id
            self.nickname = event.sender.nickname

class UserData(Dict[int, UserDict]):
    """
    用户数据
    """

class ExchangeInfo(BaseModel):
    """
    交易信息
    """
    group_id:int = None
    quote:float = 0.0
    n:int = 0

class Company(BaseModel):
    """
    公司账户
    """
    company_id:int = None
    company_name:str = None
    level:int = 0
    time:float = 0.0
    stock:int = 0
    issuance:int = 0
    gold:float = 0.0
    float_gold:float = 0.0
    group_gold:float = 0.0
    intro:str = None
    exchange:Dict[int,ExchangeInfo] = {}

    def Buyback(self, group_account:GroupAccount):
        """
        让公司回收本账户的股票
        """
        stocks = group_account.stocks
        if count := stocks.get(self.company_id):
            self.stock += count
            stocks = 0
            user_id = group_account.user_id
            if user_id in self.exchange:
                del self.exchange[user_id]


class GroupDict(BaseModel):
    """
    群字典
    """
    group_id:int = None
    namelist:set = set()
    revolution_time:float = 0.0
    Achieve_revolution:Dict[int,int] = {}
    company:Company = Company()


class GroupData(Dict[int, GroupDict]):
    """
    群数据
    """
    pass

class DataBase(BaseModel):
    user:UserData = UserData()
    group:GroupData = GroupData()
    file:Path

    def save(self):
        """
        保存数据
        """
        with open(self.file,"w") as f:
            f.write(self.json(indent = 4))
    
    @classmethod
    def loads(cls, data:str):
        """
        从json字符串中加载数据
        """
        data_dict = json.loads(data)
        Truedata = cls(file = Path(data_dict["file"]))
        for user_id, user in data_dict["user"].items():
            for group_id, group_account in user["group_accounts"].items():
                user["group_accounts"][group_id] = GroupAccount.parse_obj(group_account)
            Truedata.user[int(user_id)] = UserDict.parse_obj(user)

        for group_id, group in data_dict["group"].items():
            for user_id, exchange_info in group["company"]["exchange"].items():
                group["company"]["exchange"][user_id] = ExchangeInfo.parse_obj(exchange_info)
            group["company"] = Company.parse_obj(group["company"])
            Truedata.group[int(group_id)] = GroupDict.parse_obj(group)

        return Truedata

    def verification(self):
        """
        数据校验
        """
        log = ""
        user_data = self.user
        group_data = self.group
        namelist_check = {k:set() for k in group_data}
        stock_check = {company.company_id:0 for company in map(lambda group:group.company ,group_data.values()) if company.company_name}
        # 检查user_data
        for user_id,user in user_data.items():
            # 回归
            user.user_id = user_id
            # 清理未持有的道具
            user.props = {k:v for k,v in user.props.items() if v > 0}
            # 删除无效群账户
            group_accounts = user.group_accounts = {k:v for k,v in user.group_accounts.items() if k in namelist_check}
            gold = 0
            for group_id,group_account in group_accounts.items():
                gold += group_account.gold
                # 回归
                group_account.user_id = user_id
                group_account.group_id = group_id
                # 清理未持有的道具
                group_account.props = {k:v for k,v in group_account.props.items() if v > 0}
                # 删除无效及未持有的股票
                stocks = group_account.stocks = {k:v for k,v in group_account.stocks.items() if k in stock_check and v > 0}
                # 群名单检查
                namelist_check[group_id].add(user_id)
                # 股票数检查
                for company_id,count in stocks.items():
                    stock_check[company_id] += count
                # Nan检查
                group_account.value = 0.0 if math.isnan(group_account.value) else group_account.value
            # 金币总数
            log += f"{user.nickname} 金币总数异常。记录值：{user.gold} 实测值：{gold} 数据已修正。\n" if user.gold != gold else ""
            user.gold = gold
            # 修复炼金账户
            user.alchemy = {k:v for k,v in user.alchemy.items() if k in ["1","2","3","4","5","6","7","8","9","0"]}
        # 检查group_data
        for group_id,group in group_data.items():
            # 修正群名单记录
            log += (
                f"{group_id} 群名单异常。\n"
                f"记录多值：{group.namelist - namelist_check[group_id]}\n"
                f"记录少值：{namelist_check[group_id] - group.namelist}\n"
                "数据已修正。\n"
                ) if group.namelist != namelist_check[group_id] else ""
            group.namelist = namelist_check[group_id]
            if group_id in stock_check:
                company = group.company
                # 回归
                company.company_id = group_id
                # 修正公司等级
                level = sum(group.Achieve_revolution.values()) + 1
                log += (
                    f"{company.company_name} 公司等级异常。\n"
                    f"记录值：{company.level}\n"
                    f"实测值：{level}\n"
                    "数据已修正。\n"
                    ) if company.stock + stock_check[group_id] != company.issuance else ""
                company.level = level
                # 修正股票发行量
                company.issuance = 20000*level
                # 修正股票库存
                stock = company.issuance - stock_check[group_id]
                log += (
                    f"{company.company_name} 股票库存异常。\n"
                    f"记录值：{company.stock}\n"
                    f"实测值：{stock}\n"
                    "数据已修正。\n"
                    ) if company.stock + stock_check[group_id] != company.issuance else ""
                company.stock = stock
                # Nan检查
                company.gold = 0.0 if math.isnan(company.gold) else company.gold
                company.float_gold = 0.0 if math.isnan(company.float_gold) else company.float_gold
                company.group_gold = 0.0 if math.isnan(company.group_gold) else company.group_gold
        self.save()
        return log[:-1] if log else "数据一切正常！"

    def Newday(self):
        """
        刷新每日
        """
        revolution_today = random.randint(1,5) != 1
        for user in self.user.values():
            # 刷新转账限额
            user.transfer_limit = 0
            # 全局道具有效期 - 1天
            props = user.props
            props = {k:min(v-1,30) if k[2] == '0' else v for k,v in props.items()}
            for group_account in user.group_accounts.values():
                # 刷新今日签到
                group_account.is_sign = False
                # 概率刷新重置签到
                group_account.revolution = revolution_today
                # 群内道具有效期 - 1天
                props = group_account.props
                props = {k:min(v-1,30) if k[2] == '0' else v for k,v in props.items()}
        self.save()

"""+++++++++++++++++
——————————
    上面是定义~♡
——————————
   ᕱ⑅ᕱ。 ᴍᴏʀɴɪɴɢ
  (｡•ᴗ-)_
——————————
    下面是实例~♡
——————————
+++++++++++++++++"""

import os

resourcefile = Path(os.path.join(os.path.dirname(__file__),"./resource"))

# 加载道具库
with open(resourcefile / "props_library.json", "r", encoding="utf8") as f:
    props_library = json.load(f)

def update_props_index(props_index):
    """
    从道具库生成道具名查找道具代号字典
    """
    for prop_code in props_library:
        props_index[props_library[prop_code]["name"]] = prop_code
        props_index[prop_code] = prop_code

props_index:Dict[str,str] = {}
update_props_index(props_index)

def update_props_index(props_index):
    """
    从道具库生成道具名查找道具代号字典
    """
    for prop_code in props_library:
        props_index[props_library[prop_code]["name"]] = prop_code
        props_index[prop_code] = prop_code

props_index:Dict[str,str] = {}
update_props_index(props_index)

# 加载菜单
with open(resourcefile / "menu_data.json", "r", encoding="utf8") as f:
    menu_data = json.load(f)

# OHLC子程序
import subprocess
from sys import platform

python = "python" if platform == "win32" else "python3"

def OHLC(path, company_id):
    """
    OHLC子程序
    """
    return subprocess.Popen([python,f"{resourcefile}/subprocess/ohlc.py", path, str(company_id)], shell = True)

"""
from . import Data
from .Data import (
    DataBase,
    UserData,
    UserDict,
    GroupAccount,
    GroupData,
    GroupDict,
    Company,
    ExchangeInfo
    )
from .Data import (
    resourcefile,
    menu_data,
    props_library,
    props_index,
    update_props_index,
    element_library,
    OHLC,
    )
"""
