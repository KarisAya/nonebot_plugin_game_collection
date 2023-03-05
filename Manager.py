from typing import Tuple,Dict
from pathlib import Path
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
    )

from .utils.utils import image_url
from .utils.chart import text_to_png, gini_coef, default_BG
from .utils.avatar import download_url
from .data.data import DataBase, UserDict, GroupAccount, GroupDict
from .data.data import props_library
from .config import revolt_gold, max_bet_gold, lucky_clover, path, BG_image

# 加载数据

datafile = path / "russian_data.json"

if datafile.exists():
    with open(datafile, "r") as f:
        data = DataBase.loads(f.read())
else:
    data = DataBase(file = datafile)

user_data = data.user
group_data = data.group

"""+++++++++++++++++
|     ／l、        |
|   （ﾟ､ 。７      |
|　   l、 ~ヽ      |
|　   じしf_, )ノ  |
+++++++++++++++++"""

def locate_user(event:MessageEvent) ->Tuple[UserDict,GroupAccount]:
    """
    定位个人账户
    """
    user_id = event.user_id
    user = user_data.setdefault(user_id,UserDict())
    user.init(event)
    if isinstance(event,GroupMessageEvent):
        group_id = event.group_id
        group = group_data.setdefault(group_id,GroupDict())
        group.init(event.group_id)
        namelist = group.namelist
        if user_id in namelist:
            group_account = user.group_accounts[group_id]
            group_account.init(event)
        else:
            namelist.add(user_id)
            user.group_accounts[group_id] = GroupAccount()
            group_account = user.group_accounts[group_id]
            group_account.init(event)
            data.save()
    else:
        group_id = user.connect
        if group_id:
            group_account = user.group_accounts[group_id]
        else:
            group_account = None

    return user,group_account

async def locate_user_at(bot:Bot, event:GroupMessageEvent, user_id:int) ->Tuple[UserDict,GroupAccount]:
    """
    定位at账户
    """
    if user_id not in user_data:
        info = await bot.get_group_member_info(group_id = event.group_id, user_id = user_id)
        user_data[user_id] = UserDict(user_id = user_id, nickname = info["nickname"])

    user = user_data[user_id]
    group_id = event.group_id
    group = group_data.setdefault(group_id,GroupDict())
    group.init(event.group_id)
    namelist = group.namelist

    if user_id not in namelist:
        namelist.add(user_id)
        user.group_accounts[group_id] = GroupAccount(group_id = group_id, nickname = user.nickname)
        data.save()

    group_account = user.group_accounts[group_id]

    return user,group_account

def update_company_index(company_index):
    """
    从群数据生成公司名查找群号的字典
    """
    for group_id in group_data:
        if company_name := group_data[group_id].company.company_name:
            company_index[company_name] = group_id
            company_index[str(group_id)] = group_id

company_index:Dict[str,int] = {}
update_company_index(company_index)

def BG_path(event:MessageEvent):
    my_BG = BG_image / f"{str(event.user_id)}.png"
    if my_BG.exists():
        return my_BG
    else:
        return default_BG

async def add_BG_image(event:MessageEvent):
    user = locate_user(event)[0]
    if user.props.get("33001",0) < 1:
        return f"你的【{props_library['33001']['name']}】已失效"
    if url := image_url(event):
        if not (bytes_image := await download_url(url[0])):
            return "图片下载失败"
        else:
            with open(BG_image / f"{str(event.user_id)}.png", 'wb') as f:
                f.write(bytes_image)
            return "图片下载成功"

async def del_BG_image(event:MessageEvent):
    Path.unlink(BG_image / str(event.user_id),True)
    return "背景图片删除成功！"

def Achieve_list(locate:Tuple[UserDict,GroupAccount]):
    """
    成就列表
    """
    user,group_account = locate
    rank = []
    count = group_account.props.get("02101",0)
    if count > 0:
        if count <= 4:
            rank.append(f"{count*'☆'}  路灯挂件  {count*'☆'}")
        else:
            rank.append(f"☆☆☆☆☆路灯挂件☆☆☆☆☆")

    count = group_account.props.get("32001",0)   # 四叶草标记
    if count > 0:
        rank.append(lucky_clover)

    count = group_account.gold
    if count > max_bet_gold:
        count = int(count/max_bet_gold)
        count = str(count) if count < 1000 else "MAX"
        level =f"Lv.{count}"
        rank.append(f"◆◇ 金库 {level}")

    count = user.Achieve_win
    if count >1:
        count = str(count) if count < 1000 else "MAX"
        level =f"Lv.{count}"
        rank.append(f"◆◇ 连胜 {level}")

    count = user.Achieve_lose
    if count >1:
        count = str(count) if count < 1000 else "MAX"
        level =f"Lv.{count}"
        rank.append(f"◆◇ 连败 {level}")

    return rank

def group_wealths(group_id:int) -> float:
    """
    群内总资产
    """
    if group_id in group_data:
        namelist = group_data[group_id].namelist
    else:
        return None
    total = 0
    for user_id in namelist:
        group_account = user_data[user_id].group_accounts[group_id]
        total += group_account.gold + group_account.value
    return total

def group_ranklist(group_id:int , title:str) -> list:
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
        namelist = group_data[group_id].namelist
    else:
        return None

    rank = []
    if title == "总金币":
        for user_id in namelist:
            user = user_data[user_id]
            rank.append([user_id,user.gold])
    elif title == "总资产":
        for user_id in namelist:
            user = user_data[user_id]
            value = 0
            for x in user.group_accounts:
                value += user.group_accounts[x].value
            rank.append([user_id, user.gold + value])
    elif title == "金币":
        for user_id in namelist:
            group_account = user_data[user_id].group_accounts[group_id]
            rank.append([user_id,group_account.gold])
    elif title == "资产" or title == "财富":
        for user_id in namelist:
            group_account = user_data[user_id].group_accounts[group_id]
            rank.append([user_id, group_account.gold + group_account.value])
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
    elif title == "路灯":
        rank = group_data[group_id].Achieve_revolution.items()
    else:
        return None
    rank = [x for x in rank if x[1]]
    rank.sort(key=lambda x:x[1],reverse=True)
    return rank

def group_rank(group_id:int, title:str = "金币", top:int = 20) -> str:
    if not (ranklist := group_ranklist(group_id, title)):
        return "无数据。"
    rank = ""
    i = 1
    for x in ranklist[:top]:
        user = user_data[x[0]]
        group_account = user.group_accounts[group_id]
        nicname = group_account.nickname
        rank += f"{i}.{nicname}：{x[1]}\n"
        i += 1
    return MessageSegment.image(text_to_png(rank[:-1]))

def Gini(group_id:int, limit:int = revolt_gold[0]) -> float:
    """
    本群基尼系数
    """
    if group_id in group_data:
        namelist = group_data[group_id].namelist
    else:
        return None
    rank = []
    for user_id in namelist:
        group_account = user_data[user_id].group_accounts[group_id]
        rank.append(group_account.gold + group_account.value)

    rank = [x for x in rank if x > limit]
    rank.sort()
    return gini_coef(rank)

def Newday():
    """
    刷新每日
    """
    log = ""
    group_check = {k:set() for k in group_data}
    global company_index
    update_company_index(company_index)
    company_ids = company_index.values()
    stock_check = {k:0 for k in company_ids}
    # 检查user_data
    for user_id in user_data:
        user = user_data[user_id]
        user.transfer_limit = 0
        props = user.props
        props = {k:v-1 if k[2] == '0' else v for k, v in props.items()}
        user.props = {k:v for k, v in props.items() if v > 0}
        group_accounts = user.group_accounts
        gold = 0
        for group_id in list(group_accounts.keys()):
            if group_id not in group_check:
                log += f"{user.nickname} 群账户{group_id}无效，已删除。\n"
                del group_accounts[group_id]
            else:
                group_check[group_id].add(user_id)
                group_account = group_accounts[group_id]
                group_account.is_sign = False
                gold += group_account.gold
                props = group_account.props
                props = {k:v-1 if k[2] == '0' else v for k, v in props.items()}
                group_account.props = {k:v for k, v in props.items() if v > 0}
                stocks = group_account.stocks
                for company_id in list(stocks.keys()):
                    if company_id in stock_check:
                        stock_check[company_id] += stocks[company_id]
                    else:
                        log += f"{user.nickname} 群账户{group_id}内股票{company_id}回收异常，数据已修正。\n"
                        del stocks[company_id]
        if user.gold != gold:
            log += f"{user.nickname} 金币总数异常。记录值：{user.gold} 实测值：{gold} 数据已修正。\n"
            user.gold = gold

    # 检查group_data
    for group_id in group_data:
        group = group_data[group_id]
        if group.namelist != group_check[group_id]:
            log += (
                f"{group_id} 群名单异常。\n"
                f"记录多值：{group.namelist - group_check[group_id]}\n"
                f"记录少值：{group_check[group_id] - group.namelist}\n"
                "数据已修正。\n"
                )
            group.namelist = group_check[group_id]

        if group_id in company_ids:
            company = group.company
            if company.stock + stock_check[group_id] != company.issuance:
                log += (
                    f"{company.company_name} 股票数量异常。\n"
                    f"记录值：{company.stock}\n"
                    f"实测值：{company.issuance - stock_check[group_id]}\n"
                    "数据已修正。\n"
                    )
                company.stock = company.issuance - stock_check[group_id]
    data.save()
    return log[:-1] if log else "数据一切正常！"