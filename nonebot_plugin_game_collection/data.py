from typing import Dict, Tuple, List
from pydantic import BaseModel
from pathlib import Path
from collections import Counter
from sys import platform

import os
import math
import datetime
import subprocess

from .Processor import Event

try:
    import ujson as json
except ModuleNotFoundError:
    import json

python = "python" if platform == "win32" else "python3"


class GroupAccount(BaseModel):
    """
    用户群账户
    """

    user_id: str = None
    group_id: str = None
    nickname: str = None
    is_sign: bool = False
    revolution: bool = False
    security: int = 0
    gold: int = 0
    invest: Dict[str, int] = {}
    props: Dict[str, int] = {}

    def __init__(self, event: Event = None, **obj):
        """
        初始化群账户
        """
        if event:
            obj["user_id"] = event.user_id
            obj["group_id"] = event.group_id
            obj["nickname"] = event.nickname
        super().__init__(**obj)


class UserDict(BaseModel):
    """
    用户字典
    """

    user_id: str = None
    nickname: str = None
    avatar_url: str = "https://avatars.githubusercontent.com/u/51886078"
    gold: int = 0
    win: int = 0
    lose: int = 0
    Achieve_win: int = 0
    Achieve_lose: int = 0
    group_accounts: Dict[str, GroupAccount] = {}
    connect: str = 0
    props: Dict[str, int] = {}
    alchemy: Dict[str, int] = {}

    def __init__(self, event: Event = None, **obj):
        """
        初始化用户字典
        """
        if event:
            obj["user_id"] = event.user_id
            obj["nickname"] = event.nickname
        super().__init__(**obj)


class UserData(Dict[str, UserDict]):
    """
    用户数据
    """


class ExchangeInfo(BaseModel):
    """
    交易信息
    """

    group_id: str = None
    quote: float = 0.0
    n: int = 0


class Company(BaseModel):
    """
    公司账户
    """

    company_id: str = None
    """群号"""
    company_name: str = None
    """公司名称"""
    level: int = 1
    """公司等级"""
    time: float = 0.0
    """注册时间"""
    stock: int = 0
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
    """群金库"""
    invest: dict[str, int] = {}
    """群投资"""
    transfer_limit: float = 0.0
    """每日转账限制"""
    transfer: int = 0
    """今日转账额"""
    intro: str = None
    """群介绍"""
    exchange: Dict[str, ExchangeInfo] = {}
    """本群交易市场"""
    orders: dict = {}
    """当前订单"""

    def Buyback(self, group_account: GroupAccount, n: int = None):
        """
        让公司回收本账户的股票
        """
        stock = group_account.invest.get(self.company_id, 0)
        count = min(n, stock) if n else stock
        stock = stock - count
        if count:
            self.stock += count
            user_id = group_account.user_id
            group_account.invest[self.company_id] = (
                group_account.invest.get(self.company_id) - count
            )
            if (
                user_id in self.exchange
                and (exchange := self.exchange[user_id]).group_id
                == group_account.group_id
            ):
                exchange.n -= count


class GroupDict(BaseModel):
    """
    群字典
    """

    group_id: str = None
    namelist: set = set()
    revolution_time: float = 0.0
    Achieve_revolution: Dict[str, int] = {}
    company: Company = Company()


class GroupData(Dict[str, GroupDict]):
    """
    群数据
    """

    pass


class DataBase(BaseModel):
    user: UserData = UserData()
    group: GroupData = GroupData()
    file: Path

    def save(self):
        """
        保存数据
        """
        with open(self.file, "w") as f:
            f.write(self.json(indent=4))

    @classmethod
    def loads(cls, data: str):
        """
        从json字符串中加载数据
        """
        data_dict = json.loads(data)
        Truedata = cls(file=Path(data_dict["file"]))
        for user_id, user in data_dict["user"].items():
            for group_id, group_account in user["group_accounts"].items():
                user["group_accounts"][group_id] = GroupAccount.parse_obj(group_account)
            Truedata.user[user_id] = UserDict.parse_obj(user)

        for group_id, group in data_dict["group"].items():
            for user_id, exchange_info in group["company"]["exchange"].items():
                group["company"]["exchange"][user_id] = ExchangeInfo.parse_obj(
                    exchange_info
                )
            group["company"] = Company.parse_obj(group["company"])
            Truedata.group[group_id] = GroupDict.parse_obj(group)
        return Truedata

    def verification(self):
        """
        数据校验
        """
        log = ""
        user_data = self.user
        group_data = self.group
        namelist_check = {k: set() for k in group_data}
        stock_check = Counter()
        # 检查user_data
        for user_id, user in user_data.items():
            # 回归
            user.user_id = user_id
            # 清理未持有的道具
            user.props = {
                k: v for k, v in user.props.items() if v > 0 and k in props_library
            }
            # 删除无效群账户
            group_accounts = user.group_accounts = {
                k: v for k, v in user.group_accounts.items() if k in namelist_check
            }
            gold = 0
            for group_id, group_account in group_accounts.items():
                gold += group_account.gold
                # 回归
                group_account.user_id = user_id
                group_account.group_id = group_id
                # 清理未持有的道具
                group_account.props = {
                    k: v
                    for k, v in group_account.props.items()
                    if v > 0 and k in props_library
                }
                # 删除无效及未持有的股票
                invest = group_account.invest = {
                    k: v
                    for k, v in group_account.invest.items()
                    if k in namelist_check and v > 0
                }
                # 群名单检查
                namelist_check[group_id].add(user_id)
                # 股票数检查
                stock_check += Counter(invest)
            # 金币总数
            log += (
                f"{user.nickname} 金币总数异常。记录值：{user.gold} 实测值：{gold} 数据已修正。\n"
                if user.gold != gold
                else ""
            )
            user.gold = gold
            # 修复炼金账户
            user.alchemy = {
                k: v
                for k, v in user.alchemy.items()
                if k in {"1", "2", "3", "4", "5", "6", "7", "8", "9", "0"}
            }
        # 检查group_data
        for group in group_data.values():
            group.company.invest = {
                k: v for k, v in group.company.invest.items() if k in namelist_check
            }
        stock_check = sum(
            (Counter(group.company.invest) for group in group_data.values()),
            stock_check,
        )
        for group_id, group in group_data.items():
            # 修正群名单记录
            log += (
                (
                    f"{group_id} 群名单异常。\n"
                    f"记录多值：{group.namelist - namelist_check[group_id]}\n"
                    f"记录少值：{namelist_check[group_id] - group.namelist}\n"
                    "数据已修正。\n"
                )
                if group.namelist != namelist_check[group_id]
                else ""
            )
            group.namelist = namelist_check[group_id]
            group.Achieve_revolution = {
                k: v for k, v in group.Achieve_revolution.items() if k in group.namelist
            }
            company = group.company
            # 修正公司等级
            level = min(20, sum(group.Achieve_revolution.values()) + 1)
            if company.level != level:
                log += (
                    f"{company.company_name} 公司等级异常。\n"
                    f"记录值：{company.level}\n"
                    f"实测值：{level}\n"
                    "数据已修正。\n"
                )
                company.level = level
            if group_id in stock_check:
                # 回归
                company.company_id = group_id
                # 修正股票发行量
                company.issuance = 20000 * level
                # 修正股票库存
                stock = company.issuance - stock_check[group_id]
                log += (
                    (
                        f"{company.company_name} 股票库存异常。\n"
                        f"记录值：{company.stock}\n"
                        f"实测值：{stock}\n"
                        "数据已修正。\n"
                    )
                    if company.stock + stock_check[group_id] != company.issuance
                    else ""
                )
                company.stock = stock
                # 修正交易市场
                company.exchange = {
                    user_id: exchange
                    for user_id, exchange in company.exchange.items()
                    if exchange.n > 0
                    and user_id in user_data
                    and (
                        group_account := user_data[user_id].group_accounts.get(
                            exchange.group_id
                        )
                    )
                    and group_account.invest.get(company.company_id, 0) > exchange.n
                }
                # Nan检查
                company.gold = 0.0 if math.isnan(company.gold) else company.gold
                company.float_gold = (
                    0.0 if math.isnan(company.float_gold) else company.float_gold
                )
                company.group_gold = (
                    0.0 if math.isnan(company.group_gold) else company.group_gold
                )
        self.save()
        return log[:-1] if log else "数据一切正常！"

    def Newday(self):
        """
        刷新每日
        """
        revolution_today = datetime.date.today().weekday() in {5, 6}
        for user in self.user.values():
            # 全局道具有效期 - 1天
            props = user.props
            props = {k: min(v - 1, 30) if k[2] == "0" else v for k, v in props.items()}
            for group_account in user.group_accounts.values():
                # 刷新今日签到
                group_account.is_sign = False
                # 刷新每日补贴
                group_account.security = 3
                # 周末刷新重置签到
                group_account.revolution = revolution_today
                # 群内道具有效期 - 1天
                props = group_account.props
                props = {
                    k: min(v - 1, 30) if k[2] == "0" else v for k, v in props.items()
                }
        for group in self.group.values():
            # 刷新今日转账限制
            group.company.transfer = 0
            group.company.transfer_limit = (
                int(group.company.group_gold / 10)
                if group.company.group_gold
                else float("inf")
            )
        self.save()


class MarketHistory(BaseModel):
    data: Dict[str, List[Tuple[float, float, float]]] = {}
    file: Path

    def record(self, company_id: str, data: Tuple[float, float, float]):
        self.data.setdefault(company_id, [(0, 0, 0) for x in range(720)]).append(data)
        self.data[company_id] = self.data[company_id][-720:]

    @classmethod
    def loads(cls, data: str):
        """
        从json字符串中加载数据
        """
        return cls.parse_obj(json.loads(data))

    def save(self):
        """
        保存数据
        """
        with open(self.file, "w") as f:
            f.write(self.json(indent=4))


"""+++++++++++++++++
——————————
   ᕱ⑅ᕱ。 ᴍᴏʀɴɪɴɢ
  (｡•ᴗ-)_
——————————
+++++++++++++++++"""

resourcefile = Path(os.path.join(os.path.dirname(__file__), "./resource"))

# 加载道具库
with open(resourcefile / "props_library.json", "r", encoding="utf8") as f:
    props_library = json.load(f)

# 加载菜单
with open(resourcefile / "menu_data.json", "r", encoding="utf8") as f:
    menu_data = json.load(f)

# OHLC子程序


def OHLC(path, company_id):
    """
    OHLC子程序
    """
    return subprocess.Popen(
        [python, f"{resourcefile}/subprocess/ohlc.py", path, str(company_id)],
        shell=True,
    )
