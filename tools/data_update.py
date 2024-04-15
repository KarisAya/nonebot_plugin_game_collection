import os
import json
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Union
from collections import Counter

resource_file = Path(os.path.dirname(__file__))


with open(resource_file / "props_library.json", "r", encoding="utf8") as f:
    props_library: dict = json.load(f)

Bank = dict[str, int]


class Stock(BaseModel):
    id: str = None
    name: str = None
    time: float = 0.0
    """注册时间"""
    issuance: int = 0
    """股票发行量"""


class Account(BaseModel):
    """
    用户群账户
    """

    user_id: str = None
    group_id: str = None
    gold: int
    name: str = None
    nickname: str = None
    revolution: bool = False
    props: Bank = Bank()
    """更名为bank"""
    bank: Bank = Bank()
    invest: Bank = Bank()
    extra: dict = {}


class User(BaseModel):
    """
    用户数据
    """

    id: str = None
    user_id: str = None
    nickname: str = None
    """更名为name"""
    name: str = None
    avatar_url: str = None
    win: int = 0
    lose: int = 0
    Achieve_win: int = 0
    Achieve_lose: int = 0

    gold: int = 0
    """存入bank"""
    group_accounts: dict[str, Account] = {}
    accounts: dict[str, Account] = {}
    connect: str | None | int = None
    props: Bank = Bank()
    """更名为bank"""
    bank: Bank = Bank()
    invest: Bank = Bank()
    extra: dict = {}
    accounts_map: dict = {}


class Company(BaseModel):
    """
    公司账户
    """

    company_id: str = None
    """群号"""
    company_name: str | None = None
    """公司名称"""
    level: int = 1
    """公司等级"""
    time: float = 0.0
    """注册时间"""
    stock: Union[int, Stock] = Stock()
    """正在发行的股票数"""
    issuance: int = 0
    """股票发行量"""
    gold: float = 0.0
    """固定资产"""
    float_gold: float = 0.0
    """浮动资产"""
    group_gold: float = 0.0
    """全群资产"""
    bank: int = 0
    """群金币，存入group bank字段"""
    invest: dict[str, int] = {}
    """群投资"""
    transfer_limit: float = 0.0
    """每日转账限制"""
    transfer: int = 0
    """今日转账额"""
    intro: str | None = None
    """群介绍"""
    orders: dict = {}
    """当前订单"""


class Group(BaseModel):
    """
    群字典
    """

    id: str = None
    group_id: str = None
    namelist: set = set()
    name: str = None
    revolution_time: float = 0.0
    """存入extra"""
    Achieve_revolution: dict[str, int] = {}
    """存入extra"""
    company: Company = Company()
    """已取消"""
    stock: Stock = None
    level: int = 1
    bank: Bank = Bank()
    invest: Bank = Bank()
    intro: Union[str, None] = None
    """群介绍"""
    extra: dict = {}
    accounts_map: dict = {}


class DataBase(BaseModel):
    user: dict[str, User] = {}
    group: dict[str, Group] = {}

    user_dict: dict[str, User] = {}
    group_dict: dict[str, Group] = {}
    account_dict: dict[str, Account] = {}
    extra: dict = {}

    def save(self, file):
        """
        保存数据
        """
        with open(file, "w", encoding="utf8") as f:
            f.write(self.model_dump_json(indent=4))

    @classmethod
    def loads(cls, data: str):
        """
        从json字符串中加载数据
        """

        return cls.model_validate_json(data)


data_file = resource_file / "russian_data.json"
with open(data_file, "r") as f:
    data = DataBase.loads(f.read())


def recode(code: str):
    rare = int(code[0])
    domain = int(code[1])
    flow = int(code[2])
    number = code[3:]
    if number[0] == "0":
        domain -= 1

    number = int(number)
    return f"{rare}{domain}{flow}{number}"


for user_id, user in data.user.items():
    user.id = user_id
    invest = Counter()
    for group_id, group_account in user.group_accounts.items():
        group_account.name = group_account.nickname
        group_account.props = {recode(k): v for k, v in group_account.props.items()}
        group_account.bank = group_account.props
        group_account.bank["1111"] = group_account.gold
        invest += group_account.invest
        user.accounts[group_id] = group_account
        ranklist: dict[str, Counter] = data.extra.setdefault("ranklist", {})
        ranklist.setdefault("win", Counter())[user_id] = user.win
        ranklist.setdefault("win_achieve", Counter())[user_id] = user.Achieve_win
        ranklist.setdefault("lose", Counter())[user_id] = user.lose
        ranklist.setdefault("lose_achieve", Counter())[user_id] = user.Achieve_lose
        group_account.group_id = group_id
        group_account.user_id = user_id
        account_id = f"{user_id}-{group_id}"
        user.accounts_map[group_id] = account_id
        data.group[group_id].accounts_map[user_id] = account_id
        data.account_dict[account_id] = group_account
    user.name = user.nickname
    user.bank = {recode(k): v for k, v in user.props.items()}
    user.invest = Bank(invest)
for group_id, group in data.group.items():
    group.id = group_id
    company = group.company
    group.bank["1111"] = company.bank
    group.extra["revolution_achieve"] = group.Achieve_revolution
    group.extra["revolution_time"] = group.revolution_time
    group.level = company.level or 1
    group.invest = company.invest
    group.intro = company.intro
    if company.company_name:
        group.stock = Stock()
        group.stock.id = group.group_id
        group.stock.name = company.company_name
        group.stock.time = company.time
        group.stock.issuance = company.issuance

data.group_dict = data.group
data.user_dict = data.user

data.save(data_file)
