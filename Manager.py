from typing import Tuple,Dict
from pathlib import Path
from collections import Counter
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
    )
from nonebot import get_driver
from nonebot.log import logger

from .utils.utils import image_url
from .utils.chart import gini_coef, default_BG
from .utils.avatar import download_url
from .data import DataBase, UserDict, GroupAccount, GroupDict, Company, props_library
from .config import max_bet_gold, lucky_clover, path, BG_image,bet_gold

driver = get_driver()

# 加载数据

datafile = path / "russian_data.json"

if datafile.exists():
    with open(datafile, "r") as f:
        data = DataBase.loads(f.read())
else:
    data = DataBase(file = datafile)

log = data.verification()
logger.info(f"\n{log}")

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
    user = user_data.setdefault(user_id,UserDict(event))
    if isinstance(event,GroupMessageEvent):
        group_id = event.group_id
        group = group_data.setdefault(group_id,GroupDict(group_id = group_id,company = Company(company_id = group_id)))
        namelist = group.namelist
        if user_id in namelist:
            group_account = user.group_accounts[group_id]
            group_account.nickname = event.sender.card or event.sender.nickname
        else:
            namelist.add(user_id)
            user.group_accounts[group_id] = GroupAccount(event)
            group_account = user.group_accounts[group_id]
            data.save()
    else:
        group_id = user.connect
        if group_id:
            group_account = user.group_accounts.get(group_id)
        else:
            group_account = None

    return user,group_account

def locate_user_at(event:GroupMessageEvent, user_id:int) ->Tuple[UserDict,GroupAccount]:
    """
    定位at账户
    """
    if user_id not in user_data:
        user_data[user_id] = UserDict(user_id = user_id, nickname = str(user_id))
    user = user_data[user_id]
    group_id = event.group_id
    group = group_data.setdefault(group_id,GroupDict(group_id = group_id))
    namelist = group.namelist

    if user_id not in namelist:
        namelist.add(user_id)
        user.group_accounts[group_id] = GroupAccount(group_id = group_id,nickname = user.nickname)
        data.save()
    group_account = user.group_accounts[group_id]
    return user,group_account

company_index:Dict[str,int] = {}

def update_company_index():
    """
    从群数据生成公司名查找群号的字典
    """
    company_index.clear()
    for group_id in group_data:
        if company_name := group_data[group_id].company.company_name:
            company_index[company_name] = group_id
            company_index[str(group_id)] = group_id

update_company_index()

def BG_path(user_id:int) -> Path:
    my_BG = BG_image / f"{str(user_id)}.png"
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
    Path.unlink(BG_image / f"{str(event.user_id)}.png", True)
    return "背景图片删除成功！"

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

def group_wealths(group_id:int, level:int = 1) -> float:
    """
    群内总资产
    """
    if group_id in group_data:
        namelist = group_data[group_id].namelist
    else:
        return 0
    total = 0.0
    for user_id in namelist:
        group_account = user_data[user_id].group_accounts[group_id]
        total += group_account.gold + group_account.value
    return total * level 

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
    elif title == "路灯挂件":
        rank = group_data[group_id].Achieve_revolution.items()
    else:
        return None
    rank = [x for x in rank if x[1]]
    rank.sort(key=lambda x:x[1],reverse=True)
    return rank

#def group_rank(group_id:int, title:str = "金币", top:int = 20) -> str:
#    if not (ranklist := group_ranklist(group_id, title)):
#        return "无数据。"
#    rank = ""
#    i = 1
#    for x in ranklist[:top]:
#        user = user_data[x[0]]
#        group_account = user.group_accounts[group_id]
#        nicname = group_account.nickname
#        rank += f"{i}.{nicname}：{x[1]}\n"
#        i += 1
#    return MessageSegment.image(text_to_png(rank[:-1]))

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
            gold = user.gold
            value = sum(group_account.value for group_account in user.group_accounts.values())
            rank.append([user_id, gold + value])
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

def company_level(group_id:int) -> int:
    """
    获取公司等级
    """
    return group_data[group_id].company.level

def Gini(group_id:int, limit:int = bet_gold) -> float:
    """
    本群基尼系数
    """
    if group_id in group_data:
        level = company_level(group_id)
        namelist = group_data[group_id].namelist
    else:
        return None
    rank = []
    for user_id in namelist:
        group_account = user_data[user_id].group_accounts[group_id]
        rank.append(group_account.gold*level + group_account.value)

    rank = [x for x in rank if x > limit]
    rank.sort()
    return gini_coef(rank)

async def try_send_private_msg(user_id:int, message: Message) -> bool:
    """
    发送私聊消息
    """
    bot_list = driver.bots.values()
    for bot in bot_list:
        friend_list = await bot.get_friend_list()
        friend_list = [friend["user_id"] for friend in friend_list]
        if user_id in friend_list:
            await bot.send_private_msg(user_id = user_id, message = message)
            return True
    return False