from typing import Tuple,Dict,List
from pathlib import Path
from PIL import Image
from collections import Counter
import time
import asyncio
from .Processor import Event
from .utils.chart import gini_coef as gini,default_BG
from .data import DataBase, UserDict, GroupAccount, GroupDict, Company,MarketHistory,OHLC
from .config import path,backup,lucky_clover,bet_gold,max_bet_gold,BG_image

from nonebot.log import logger

# 加载数据

data_file = path / "russian_data.json"

if data_file.exists():
    with open(data_file, "r") as f:
        data = DataBase.loads(f.read())
else:
    data = DataBase(file = data_file)

log = data.verification()
logger.info(f"\n{log}")

user_data = data.user
group_data = data.group

data_file = path / "market_history.json"

if data_file.exists():
    with open(data_file, "r", encoding = "utf8") as f:
        market_history = MarketHistory.loads(f.read())
else:
    market_history = MarketHistory(file = data_file)

"""+++++++++++++++++
|     ／l、        |
|   （ﾟ､ 。７      |
|　   l、 ~ヽ      |
|　   じしf_, )ノ  |
+++++++++++++++++"""

def locate_user(event:Event) ->Tuple[UserDict,GroupAccount]:
    """
    定位个人账户
    """
    user_id = event.user_id
    group_id = event.group_id

    user = user_data.setdefault(user_id,UserDict(event))
    if event.is_private():
        group_id = user.connect
        if group_id:
            group_account = user.group_accounts.get(group_id)
        else:
            group_account = None
    else:
        group_id = event.group_id
        group = group_data.setdefault(group_id,GroupDict(group_id = group_id,company = Company(company_id = group_id)))
        namelist = group.namelist
        if user_id in namelist:
            group_account = user.group_accounts[group_id]
            group_account.nickname = event.nickname
        else:
            namelist.add(user_id)
            group_account = user.group_accounts[group_id] = GroupAccount(event)
            data.save()
    return user,group_account

def locate_group(group_id:str) -> GroupDict:
    """
    定位群账户
    """
    return group_data.get(group_id)

def locate_user_at(user_id:str,group_id:str) ->Tuple[UserDict,GroupAccount]:
    """
    定位at账户
    """
    user = user_data.setdefault(user_id,UserDict(user_id = user_id, nickname = ""))
    group = group_data.setdefault(group_id,GroupDict(group_id = group_id))
    namelist = group.namelist
    if user_id not in namelist:
        namelist.add(user_id)
        data.save()
    group_account = user.group_accounts.setdefault(group_id,GroupAccount(group_id = group_id,nickname = user.nickname))
    return user,group_account

def locate_user_all(group_id:str) ->List[Tuple[UserDict,GroupAccount]]:
    """
    定位本群全部账户
    """
    group = locate_group(group_id)
    if not group:
        return []
    users = []
    for user_id in group.namelist:
        user = user_data[user_id]
        users.append((user,user.group_accounts[group_id]))

def get_user(user_id:str) -> UserDict:
    return user_data.get(user_id)

def pay_tax(locate:Tuple[UserDict,GroupAccount], group:GroupDict, tax:int):
    """
    上税
    """
    locate[0].gold -= tax
    locate[1].gold -= tax
    group.company.bank += tax

def account_connect(event:Event, group_id:str = None):
    """
    关联账户
    """
    if not group_id:
        if event.is_private():
            return
        group_id = event.group_id
    user = get_user(event.user_id)
    if group_id in user.group_accounts:
        user.connect = group_id

def BG_path(user_id:str) -> Path:
    my_BG = BG_image / f"{user_id}.png"
    if my_BG.exists():
        return my_BG
    else:
        return default_BG

def PropsCard_list(locate:Tuple[UserDict,GroupAccount]):
    """
    道具列表
    """
    user,group_account = locate
    rank = []
    count = group_account.props.get("02101",0)
    if count > 0:
        if count <= 4:
            rank.append(f"{count*'☆'} 路灯挂件 {count*'☆'}")
        else:
            rank.append("☆☆☆☆☆路灯挂件☆☆☆☆☆")
    count = group_account.props.get("32001",0)   # 四叶草标记
    if count > 0:
        rank.append(lucky_clover)
    return rank

def Achieve_list(locate:Tuple[UserDict,GroupAccount]):
    """
    成就列表
    """
    user,group_account = locate
    rank = []
    count = group_account.gold
    if count > max_bet_gold:
        count = int(count/max_bet_gold)
        count = str(count) if count < 1000 else "MAX"
        level =f"Lv.{count}"
        rank.append(f"◆金库 {level}")

    count = user.Achieve_win
    if count >1:
        count = str(count) if count < 1000 else "MAX"
        level =f"Lv.{count}"
        rank.append(f"◆连胜 {level}")

    count = user.Achieve_lose
    if count >1:
        count = str(count) if count < 1000 else "MAX"
        level =f"Lv.{count}"
        rank.append(f"◇连败 {level}")

    return rank

def group_wealths(group_id:str, level:int = 1) -> float:
    """
    群内总资产
    """
    if group_id in group_data:
        group = group_data[group_id]
    else:
        return 0

    total = group.company.bank
    total += sum(user_data[user_id].group_accounts[group_id].gold for user_id in group.namelist)

    return total * level 

def group_wealths_detailed(group_id:str) -> Tuple[str,dict]:
    """
    详细的群内总资产
    """
    if group_id in group_data:
        group = group_data[group_id]
    else:
        return 0
    company = group.company
    gold = company.bank
    invist = Counter(company.invest)
    for user_id in group.namelist:
        group_account = user_data[user_id].group_accounts[group_id]
        gold += group_account.gold
        invist += Counter(group_account.invest)
    return gold,dict(invist)

def invest_value(invest:Dict[str,str]) -> float:
    """
    计算投资价值
    invest:投资信息（{company_id:n}）
    self_id:排除 company_id
    """
    value = 0.0
    for company_id,n in invest.items():
        company = group_data[company_id].company
        unit = company.float_gold / company.issuance
        value += n * unit
    return value

def group_ranklist(group_id:str , title:str) -> list:
    """
    群内排行榜
        param:
        group_id:群号
        title:排名内容
        return:List[data]
        data[0]:QQ号
        data[1]:title
    """
    if group_id in group_data:
        group = group_data[group_id]
    else:
        return None

    namelist = group.namelist
    rank = []
    if title == "总金币":
        for user_id in namelist:
            user = user_data[user_id]
            rank.append([user_id,user.gold])
    elif title == "总资产":
        for user_id in namelist:
            user = user_data[user_id]
            rank.append([user_id, sum(invest_value(group_account.invest) for group_account in user.group_accounts.values())])
    elif title == "金币":
        for user_id in namelist:
            group_account = user_data[user_id].group_accounts[group_id]
            rank.append([user_id,group_account.gold])
    elif title == "资产" or title == "财富":
        rank = [[user_id, invest_value(user_data[user_id].group_accounts[group_id].invest)] for user_id in namelist]
    elif title == "胜率":
        for user_id in namelist:
            user = user_data[user_id]
            if (count := user.win + user.lose) > 2:
                rank.append([user_id, user.win / count])
    elif title == "胜场":
        for user_id in namelist:
            user = user_data[user_id]
            rank.append([user_id, user.win])
    elif title == "败场":
        for user_id in namelist:
            user = user_data[user_id]
            rank.append([user_id, user.lose])
    elif title == "路灯挂件":
        rank = group_data[group_id].Achieve_revolution.items()
    else:
        return None
    rank = [x for x in rank if x[1]]
    rank.sort(key=lambda x:x[1],reverse=True)
    return rank

def All_ranklist(title:str) -> list:
    """
    总排行榜
        param:
        title:排名内容
        return:List[data]
        data[0]:QQ号
        data[1]:title
    """
    namelist = user_data.keys()
    rank = []
    if title == "金币":
        for user_id in namelist:
            gold = user_data[user_id].gold
            rank.append([user_id,gold])
    elif title == "资产" or title == "财富":
        for user_id in namelist:
            user = user_data[user_id]
            rank.append([user_id, sum(invest_value(group_account.invest) for group_account in user.group_accounts.values())])
    elif title == "胜率":
        for user_id in namelist:
            user = user_data[user_id]
            if (count := user.win + user.lose) > 2:
                rank.append([user_id, user.win / count])
    elif title == "胜场":
        for user_id in namelist:
            user = user_data[user_id]
            rank.append([user_id, user.win])
    elif title == "败场":
        for user_id in namelist:
            user = user_data[user_id]
            rank.append([user_id, user.lose])
    elif title == "路灯挂件":
        result = Counter()
        for group in group_data.values():
            result += Counter(group.Achieve_revolution)
        rank = result.items()
    else:
        return None

    rank = [x for x in rank if x[1]]
    rank.sort(key=lambda x:x[1],reverse=True)
    return rank

def gini_coef(group_id:str, limit:int = bet_gold) -> float:
    """
    本群基尼系数
    """
    if group_id in group_data:
        level = locate_group(group_id).company.level
        namelist = group_data[group_id].namelist
    else:
        return None
    rank = []
    for user_id in namelist:
        group_account = user_data[user_id].group_accounts[group_id]
        rank.append(group_account.gold * level + invest_value(group_account.invest))

    rank = [x for x in rank if x > limit]
    rank.sort()
    return gini(rank)

async def candlestick(group_id:str):
    p = OHLC(path, group_id)
    overtime = time.time() + 30
    while (p.poll()) == None:
        if time.time() > overtime:
            return
        await asyncio.sleep(0.5)
    return Image.open(path / "candlestick" / f"{group_id}.png")

async def cancellation():
    """
    清理市场账户
    """
    folders = [f for f in backup.iterdir() if f.is_dir()]
    if not folders:
        return
    oldest_folder = min(folders, key = lambda f:f.stat().st_ctime)
    files = [f for f in oldest_folder.iterdir() if f.is_file()]
    if not files:
        return
    oldest_file = min(files, key = lambda f:f.stat().st_ctime)
    print(oldest_file)
    with open(oldest_file, "r") as f:
        old_data = DataBase.loads(f.read())
    old_data.verification()
    company_ids = [group.group_id for group in old_data.group.values() if group.company.company_name]
    result = []
    for company_id in company_ids:
        old_namelist = old_data.group[company_id].namelist
        for user_id in old_namelist:
            old_group_account = old_data.user[user_id].group_accounts[company_id]
            user = data.user.get(user_id)
            if not user:
                continue
            group_account = user.group_accounts.get(company_id)
            if not group_account:
                continue
            if group_account != old_group_account:
                break
        else:
            group = locate_group(company_id)
            if not group:
                continue
            result.append(group.company.company_name)
            group.company.company_name = None         
    return result
                
        