from typing import Dict
from pydantic import BaseModel
from pathlib import Path

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from nonebot.adapters.onebot.v11 import MessageEvent,GroupMessageEvent

class GroupAccount(BaseModel):
    """
    用户群账户
    """
    group_id:int = None
    nickname:str = None
    is_sign:bool = False
    revolution:bool = False
    security:int = 0
    gold:int = 0
    value:float = 0.0
    stocks:Dict[int,int] = {}
    props:Dict[str,int] = {}

    def init(self,event:GroupMessageEvent):
        """
        初始化群账户
        """
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

    def init(self,event:MessageEvent):
        """
        初始化用户字典
        """
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

class GroupDict(BaseModel):
    """
    群字典
    """
    group_id:int = None
    namelist:set = set()
    revolution_time:float = 0.0
    Achieve_revolution:Dict[int,int] = {}
    company:Company = Company()

    def init(self,group_id:int):
        """
        初始化群字典
        """
        self.group_id = group_id
        self.company.company_id = group_id

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

# 加载元素库
with open(resourcefile / "element_library.json", "r", encoding="utf8") as f:
    element_library = json.load(f)

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
