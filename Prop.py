from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    GroupMessageEvent,
    MessageSegment
    )
import random

from .utils.utils import get_message_at
from .utils.chart import bbcode_to_png
from .data.data import props_library, props_index, element_library
from .config import sign_gold, revolt_gold,max_bet_gold, gacha_gold

from .Manager import data
from . import Manager

user_data = data.user
group_data = data.group



def random_props() -> str:
    """
    随机获取道具。
        rare:稀有度
        return:道具代码
        道具代码规则：
        第1位：稀有度
        第2位：道具性质：
            1：空气
            2：群内道具
            3：全局道具
        第3位：道具时效：
            0：时效道具
            1：永久道具
        4,5位：本稀有度下的道具编号
    """
    code = random.randint(1,100)
    if code > 51:
        props = "11001"
    elif 0 < code <= 30:
        props = random.choice(["31001","32001","32002","33001","33101"])
    elif 30 < code <= 40:
        props = random.choice(["41001","42001","42101"])
    elif 40 < code <= 50:
        props = random.choice(["51001","51002","52001","52002","52101","52102"])
    elif code == 51:
        props = random.choice(["61001","62101"])
    else:
        props = "11001"
    return props

def gacha(event:MessageEvent, N:int):
    """
    抽卡
    """
    user,group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"

    if (gold := group_account.gold) < (cost := N * gacha_gold):
        return f'{N}连抽卡需要{cost}金币，你的金币：{gold}。'
    user.gold -= cost
    group_account.gold -= cost
    res = {}
    for i in range(N):
        prop_code = random_props()
        res.setdefault(prop_code,0)
        res[prop_code] += 1
    else:
        data = sorted(res.items(),key = lambda x:int(x[0]),reverse=True)

    msg = (f"{group_account.nickname}\n"
           f"{N} 连抽卡结果：\n"
           "[color=gray]——————————————[/color]\n")
    for prop_code, n in data:
        if prop_code[1] == "2":
            props = group_account.props
            props.setdefault(prop_code,0)
            props[prop_code] += n
            quant =  "天" if prop_code[2] == "0" else "个"
        elif prop_code[1] == "3":
            props = user.props
            props.setdefault(prop_code,0)
            props[prop_code] += n
            quant =  "天" if prop_code[2] == "0" else "个"
        else:
            quant =  "次"
        prop_info = props_library.get(prop_code,{"name":prop_code, "color":"black","rare":1,"intro":"未知","des":"未知"})
        color = prop_info['color']
        name = prop_info['name']
        rare = prop_info['rare']
        msg += (f"[align=left][color={color}]【{name}】{rare*'☆'}[/align]\n"
                f"[align=right]{n}{quant}[/color][/align][/size]\n"
                f"[align=left][color=gray]——————————————[/color][/align]\n")
        group_account.props = {k:v if v < 10 else 10 for k,v in group_account.props.items()}
    return MessageSegment.image(bbcode_to_png(msg[:-1]))

class Prop(str):
    def use(self, event:MessageEvent, count:int):
        """
        使用道具
        """
        if self == "03101":
            return self.use_03101(event,count)
        elif self == "03100":
            return self.use_03100(event)
        elif self == "33101":
            return self.use_33101(event,count)
        elif self == "42101":
            return self.use_42101(event)
        elif self == "52101":
            return self.use_52101(event)
        elif self == "52102":
            return self.use_52102(event,count)
        elif self == "53101":
            return self.use_53101(event,count)
        else:
            return f"【{props_library[self]['name']}】不是可用道具。"

    @classmethod
    def use_03100(cls, event:MessageEvent) -> str:
        """
        使用道具：测试金库
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = user.props
        if props.get("03100",0) < 1:
            return "数量不足"

        props["03100"] -= 1
        if props["03100"] < 1:
            del props["03100"]

        return "你获得了10亿金币，100万钻石。祝你好运！"

    @classmethod
    def use_03101(cls, event:MessageEvent, count:int) -> str:
        """
        使用道具：被冻结的资产
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = user.props
        if props.get("03101",0) < count:
            return "数量不足"

        props["03101"] -= count
        if props["03101"] < 1:
            del props["03101"]

        gold = count * max_bet_gold
        user.gold += gold
        group_account.gold += gold
        return f"你获得了{gold}金币。"

    @classmethod
    def use_33101(cls, event:MessageEvent, count:int) -> str:
        """
        使用道具：初级元素
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = user.props
        if props.get("33101",0) < count:
            return "数量不足"

        props["33101"] -= count
        if props["33101"] < 1:
            del props["33101"]

        res = {}
        for i in range(count*4):
            element_code = f"0{random.randint(1,4)}01"
            res.setdefault(element_code,0)
            res[element_code] += 1
        msg = "你获得了\n"
        for element_code in res:
            n = res[element_code]
            user.alchemy.setdefault(element_code,0)
            user.alchemy[element_code] += n
            msg += f'{element_library[element_code]["name"]}：{n}个\n' 
        return msg + "祝你好运~"

    @classmethod
    def use_42101(cls, event:MessageEvent) -> str:
        """
        使用道具：调查凭证
        """
        if isinstance(event, GroupMessageEvent):
            group_id = event.group_id
        else:
            return f"此道具只能在群内使用"

        if not (at := get_message_at(event.message)):
            return "没有指定用户。"
        else:
            at = int(at[0])

        if at not in group_data[group_id].namelist:
            return "对方没有账户。"

        user,group_account = Manager.locate_user(event)
        props = group_account.props
        if props.get("42101",0) < 1:
            return "数量不足"

        props["42101"] -= 1
        if props["42101"] < 1:
            del props["42101"]

        target_user = user_data[at]
        target_group_account = target_user.group_accounts[group_id]
        N = random.randint(0,50)
        if N < 30:
            gold = int(group_account.gold * N / 1000)
            user.gold -= gold
            group_account.gold -= gold
            target_user.gold += gold
            target_group_account.gold += gold
            info = f"调查没有发现问题。你赔偿了对方{gold}枚金币"
        else:
            gold = int(target_group_account.gold * N / 1000)
            user.gold += gold
            group_account.gold += gold
            target_user.gold -= gold
            target_group_account.gold -= gold
            info = f"你获得了{gold}枚金币\n"
            stocks = group_account.stocks
            target_stocks = target_group_account.stocks
            for company_id, count in target_stocks.items():
                if stock := int(count * N / 100):
                    stocks.setdefault(company_id,0)
                    stocks[company_id] += stock
                    target_stocks[company_id] -= stock
                    if at in (company := group_data[company_id].company):
                        del company.exchange[at]
                    info += f"{company.company_name}：{stock}\n"
            info += f"（{N/10}%）" 
        return info

    @classmethod
    def use_52101(cls, event:MessageEvent,) -> str:
        """
        使用道具：神秘天平
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = group_account.props
        if props.get("52101",0) < 1:
            return "数量不足"

        props["52101"] -= 1
        if props["52101"] < 1:
            del props["52101"]

        group_id = group_account.group_id
        ranklist = Manager.group_ranklist(group_id,"金币")
        target_id = random.choice(ranklist[:20])[0]
        if target_id == event.user_id:
            return f"道具使用失败，你损失了一个『{props_library['52101']['name']}』"
        target_user = user_data[target_id]
        target_group_account = target_user.group_accounts[group_id]

        gold = int((group_account.gold + target_group_account.gold) / 2)
        fee = int(gold / 20)

        flag = group_account.props.get("42001",0)
        if flag > 0:
            change = gold - group_account.gold
            user.gold += change
            group_account.gold += change
            msg1 = f"\n你获得了{gold}金币『{props_library['42001']['name']}』。"
        else:
            change = gold - group_account.gold - fee
            user.gold += change
            group_account.gold += change
            msg1 = f"\n你获得了{gold - fee}金币(扣除5%手续费：{fee})。"

        flag = target_group_account.props.get("42001",0)
        if flag > 0:
            change = gold - target_group_account.gold
            target_user.gold += change
            target_group_account.gold += change
            msg2 = f"\n对方获得了{gold}金币『{props_library['42001']['name']}』。"
        else:
            change = gold - target_group_account.gold - fee
            target_user.gold += change
            target_group_account.gold += change
            msg2 = f"\n对方获得了{gold - fee}金币(扣除5%手续费：{fee})。"

        return f"你与{target_group_account.nickname}平分了金币。" + msg1 + msg2

    @classmethod
    def use_52102(cls, event:MessageEvent, count:int,) -> str:
        """
        使用道具：幸运硬币
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = group_account.props
        if props.get("52102",0) < 1:
            return "数量不足"

        gold = group_account.gold

        if count == 2:
            if props.get("62101",0) > 1:
                props["62101"] -= 1
                if props["62101"] < 1:
                    del props["62101"]
                flag = 0
            else:
                return "钻石数量不足"
        else:
            flag = 50 * max_bet_gold

        props["52102"] -= 1
        if props["52102"] < 1:
            del props["52102"]

        if random.randint(0,1) == 1:
            bet = gold
            x = "获得"
        else:
            bet = int(-gold/2)
            x = "失去"

        if flag:
            if bet > flag:
                bet = flag
            elif bet < -flag:
                bet = -flag
        else:
            pass

        user.gold += bet
        group_account.gold += bet
        return f"你{x}了{bet}金币"

    @classmethod
    def use_53101(cls, event:MessageEvent, count:int) -> str:
        """
        使用道具：随机红包
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = user.props
        if props.get("53101",0) < count:
            return "数量不足"

        props["53101"] -= count
        if props["53101"] < 1:
            del props["53101"]

        gold = 0
        for i in range(count):
            gold += random.randint(sign_gold[0], revolt_gold[1])

        user.gold += gold
        group_account.gold += gold
        return f"你获得了{gold}金币。祝你好运~"

def use_prop(event:MessageEvent, prop_name:str, count:int):
    if prop_code := props_index.get(prop_name):
        return Prop(prop_code).use(event,count)
    else:
        return f"没有【{prop_name}】这种道具。"
