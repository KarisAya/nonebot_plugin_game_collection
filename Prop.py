from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    GroupMessageEvent,
    MessageSegment
    )
import random

from .utils.utils import get_message_at
from .utils.chart import linecard_to_png
from .data import props_library, props_index, element_library
from .config import bot_name, sign_gold, revolt_gold, max_bet_gold, gacha_gold

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
    if 0 < code <= 30:
        props = random.choice(["31001","32001","32002","33001","33101"])
    elif 30 < code <= 40:
        props = random.choice(["41001","42001","42101"])
    elif 40 < code <= 50:
        props = random.choice(["51001","51002","52001","52002","52101","52102"])
    elif code == 51:
        props = random.choice(["61001","62101"])
    elif code == 52:
        props = random.choice(["63101","63102"])
    else:
        props = "11001"
    return props

def random_airs() -> str:
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
    if 0 < code <= 30:
        props = "31001"
    elif 30 < code <= 40:
        props = "41001"
    elif 40 < code <= 50:
        props = random.choice(["51001","51002"])
    elif code == 51:
        props = "61001"
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
    star = 0
    airstar = 0
    air = 0
    for i in range(N):
        prop_code = random_props()
        res.setdefault(prop_code,0)
        res[prop_code] += 1
        rare = int(prop_code[0])
        star += rare
        if prop_code[1] == '1':
            airstar += rare
            air += 1
    else:
        data = sorted(res.items(),key = lambda x:int(x[0]),reverse=True)

    msg = ""
    airdata = []
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
            airdata.append((prop_code, n))
            continue
        prop_info = props_library.get(prop_code,{"name":prop_code, "color":"black","rare":1,"intro":"未知","des":"未知"})
        color = prop_info['color']
        name = prop_info['name']
        rare = prop_info['rare']
        msg += (
            f"[color][{color}]{name}[nowrap][passport]\n"
            f"[pixel][450]{rare*'☆'}[nowrap][passport]\n"
            f"[right]{n}{quant}\n"
            )

    user.props = {k: v if k == "33101" else min(v, 30) for k, v in user.props.items()}
    group_account.props = {k:min(30,v) for k,v in group_account.props.items()}
    for prop_code, n in airdata:
        prop_info = props_library.get(prop_code,{"name":prop_code, "color":"black","rare":1,"intro":"未知","des":"未知"})
        color = prop_info['color']
        name = prop_info['name']
        rare = prop_info['rare']
        msg += (
            f"[color][{color}]{name}[nowrap][passport]\n"
            f"[pixel][450]{rare*'☆'}[nowrap][passport]\n"
            f"[right]{n}个\n"
            )

    if N >= 10:
        pt = star/N
        if pt < 1.6 or (air/N) > 0.8:
            if air == N:
                level = "[center][color][#003300]只 有 空 气"
                user.gold += cost
                group_account.gold += cost
                msg = f"本次抽卡已免费（{cost}金币）\n" + msg
            else:
                level = "[center][color][#003300]理 想 气 体"
            n = N//10
            user.props.setdefault("03103",0)
            user.props["03103"] += n
            prop_info = props_library.get("03103",{"name":"03103", "color":"black","rare":1,"intro":"未知","des":"未知"})
            color = prop_info['color']
            name = prop_info['name']
            msg += (
                f"[color][{color}]{name}[nowrap][passport]\n"
                f"[right]{n}个\n"
                )
        elif pt < 1.88:
            level = "[left][color][#003333]☆[nowrap][passport]\n[center]数据异常[nowrap][passport]\n[right]☆"
        elif pt < 2.16:
            level = "[left][color][#003366]☆ ☆[nowrap][passport]\n[center]一枚硬币[nowrap][passport]\n[right]☆ ☆"
        elif pt < 2.44:
            level = "[left][color][#003399]☆ ☆ ☆[nowrap][passport]\n[center]高斯分布[nowrap][passport]\n[right]☆ ☆ ☆"
        elif pt < 2.72:
            level = "[left][color][#0033CC]☆ ☆ ☆ ☆[nowrap][passport]\n[center]对称破缺[nowrap][passport]\n[right]☆ ☆ ☆ ☆"
        elif pt < 3:
            level = "[left][color][#0033FF]☆ ☆ ☆ ☆ ☆[nowrap][passport]\n[center]概率之子[nowrap][passport]\n[right]☆ ☆ ☆ ☆ ☆"
        else:
            level = "[center][color][#FF0000]☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆"
        msg = (
            f"{level}\n"
            "----\n"
            f"抽卡次数：{N}[nowrap]\n"f"[pixel][450]空气占比：{round(air*100/N,2)}%\n"
            f"获得☆：{star}[nowrap]\n"f"[pixel][450]获得☆：{airstar}\n"
            f"平均每抽☆数：{round(pt,3)}[nowrap]\n"f"[pixel][450]空气质量：{round(airstar/air,3)}\n"
            f"数据来源：{group_account.nickname}\n"
            "----\n"
            ) + msg
    else:
        msg = (
            f"{group_account.nickname}\n"
            "----\n"
            f"抽卡次数：{N}\n"
            "----\n"
            ) + msg
        
    return MessageSegment.image(linecard_to_png(msg,font_size = 40 , width = 880, endline = "抽卡结果"))

class Prop(str):
    def use(self, event:MessageEvent, count:int):
        """
        使用道具
        """
        if self == "03101":
            return self.use_03101(event,count)
        elif self == "03100":
            return self.use_03100(event)
        elif self == "03103":
            return self.use_03103(event,count)
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
        elif self == "63101":
            return self.use_63101(event)
        elif self == "63102":
            return self.use_63102(event)
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
    def use_03103(cls, event:MessageEvent, count:int) -> str:
        """
        使用道具：空气礼包
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = user.props
        if props.get("03103",0) < count:
            return "数量不足"

        props["03103"] -= count
        if props["03103"] < 1:
            del props["03103"]

        N = count*10

        res = {}
        star = 0
        airstar = 0
        air = 0
        for i in range(N):
            prop_code = random_airs()
            res.setdefault(prop_code,0)
            res[prop_code] += 1
            rare = int(prop_code[0])
            star += rare
            airstar += rare
            air += 1
        else:
            data = sorted(res.items(),key = lambda x:int(x[0]),reverse=True)

        msg = ""
        props = group_account.props
        for prop_code, n in data:
            props.setdefault(prop_code,0)
            props[prop_code] += n
            prop_info = props_library.get(prop_code,{"name":prop_code, "color":"black","rare":1,"intro":"未知","des":"未知"})
            color = prop_info['color']
            name = prop_info['name']
            rare = prop_info['rare']
            msg += (
                f"[color][{color}]{name}[nowrap][passport]\n"
                f"[pixel][450]{rare*'☆'}[nowrap][passport]\n"
                f"[right]{n}个\n"
                )


        pt = star/N
        if pt < 1.6:
            level = "[center][color][#003300]杂质级"
        elif pt < 1.88:
            level = "[left][color][#003333]☆[nowrap][passport]\n[center]工业级[nowrap][passport]\n[right]☆"
        elif pt < 2.16:
            level = "[left][color][#003366]☆ ☆[nowrap][passport]\n[center]试剂级[nowrap][passport]\n[right]☆ ☆"
        elif pt < 2.44:
            level = "[left][color][#003399]☆ ☆ ☆[nowrap][passport]\n[center]实验级[nowrap][passport]\n[right]☆ ☆ ☆"
        elif pt < 2.72:
            level = "[left][color][#0033CC]☆ ☆ ☆ ☆[nowrap][passport]\n[center]分析级[nowrap][passport]\n[right]☆ ☆ ☆ ☆"
        elif pt < 3:
            level = "[left][color][#0033FF]☆ ☆ ☆ ☆ ☆[nowrap][passport]\n[center]超纯级[nowrap][passport]\n[right]☆ ☆ ☆ ☆ ☆"
        else:
            level = "[center][color][#FF0000]☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆"

        msg = (
            f"{level}\n"
            "----\n"
            f"抽卡次数：{N}[nowrap]\n"f"[pixel][450]空气占比：{round(air*100/N,2)}%\n"
            f"获得☆：{star}[nowrap]\n"f"[pixel][450]获得☆：{airstar}\n"
            f"平均每抽☆数：{round(pt,3)}[nowrap]\n"f"[pixel][450]空气质量：{round(airstar/air,3)}\n"
            f"数据来源：{group_account.nickname}\n"
            "----\n"
            ) + msg

        return MessageSegment.image(linecard_to_png(msg,font_size = 40, width = 880,endline = "抽卡结果"))

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
            gold = 0 if gold < 0 else gold
            user.gold -= gold
            group_account.gold -= gold
            target_user.gold += gold
            target_group_account.gold += gold
            info = f"调查没有发现问题。你赔偿了对方{gold}枚金币"
        else:
            gold = int(target_group_account.gold * N / 1000)
            gold = min(group_account.gold, gold)
            gold = 0 if gold < 0 else gold
            user.gold += gold
            group_account.gold += gold
            target_user.gold -= gold
            target_group_account.gold -= gold
            info = f"你获得了{gold}枚金币"
            #stocks = group_account.stocks
            #target_stocks = target_group_account.stocks
            #for company_id, count in target_stocks.items():
            #    if stock := int(count * N / 100):
            #        stocks.setdefault(company_id,0)
            #        stocks[company_id] += stock
            #        target_stocks[company_id] -= stock
            #        if at in (company := group_data[company_id].company):
            #            del company.exchange[at]
            #        info += f"{company.company_name}：{stock}\n"
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
        target_id = random.choice([x[0] for x in ranklist if x[1] > revolt_gold[0]])
        if target_id == event.user_id:
            return f"道具使用失败，你损失了一个『{props_library['52101']['name']}』"
        target_user = user_data[target_id]
        target_group_account = target_user.group_accounts[group_id]

        change = int((group_account.gold - target_group_account.gold) / 2)
        limit = min((group_account.gold, target_group_account.gold))
        limit = 0 if limit < 0 else limit
        if change > limit:
            change = limit
        if change < -limit:
            change = -limit

        abschange = abs(change)
        fee = int(abschange / 20)

        flag = group_account.props.get("42001",0)
        tag = "失去" if change > 0 else "获得"
        if flag > 0:
            user.gold -= change
            group_account.gold -= change
            msg1 = f"\n你{tag}了{abschange}金币『{props_library['42001']['name']}』。"
        else:
            user.gold -= change
            user.gold -= fee
            group_account.gold -= change
            group_account.gold -= fee
            msg1 = f"\n你{tag}了{abs(change + fee)}金币(扣除5%手续费：{fee})。"

        flag = target_group_account.props.get("42001",0)
        tag = "失去" if change < 0 else "获得"

        if flag > 0:
            target_user.gold += change
            target_group_account.gold += change
            msg2 = f"\n对方{tag}了{abschange}金币『{props_library['42001']['name']}』。"
        else:
            target_user.gold += change
            target_user.gold -= fee
            target_group_account.gold += change
            target_group_account.gold -= fee
            msg2 = f"\n对方{tag}了{abs(change - fee)}金币(扣除5%手续费：{fee})。"

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

        if count == 1:
            gold = int(group_account.gold/2)
            X = 1
        else:
            if props.get("62101",0) > 0:
                props["62101"] -= 1
                if props["62101"] < 1:
                    del props["62101"]
            else:
                return "钻石数量不足"
            if count == 2:
                gold = int(group_account.gold/2)
                X = 2
            else:
                gold = group_account.gold
                X = 1

        gold = gold if gold < (limit := 50 * max_bet_gold) else limit

        props["52102"] -= 1
        if props["52102"] < 1:
            del props["52102"]

        if random.randint(0,X) > 0:
            user.gold += gold
            group_account.gold += gold
            return f"你获得了{gold}金币"
        else:
            gold = int(group_account.gold/2)
            user.gold -= gold
            group_account.gold -= gold
            user.props.setdefault("53101",0)
            user.props["53101"] += 1
            return f"你失去了{gold}金币。\n{bot_name}送你1个『{props_library['53101']['name']}』，祝你好运~"

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

        gold = random.randint(sign_gold[0] * count, revolt_gold[1] * count)

        user.gold += gold
        group_account.gold += gold
        return f"你获得了{gold}金币。祝你好运~"

    @classmethod
    def use_63101(cls, event:MessageEvent) -> str:
        """
        使用道具：超级幸运硬币
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = user.props
        if props.get("63101",0) < 1:
            return "数量不足"

        props["63101"] -= 1
        if props["63101"] < 1:
            del props["63101"]

        gold = group_account.gold

        if random.randint(0,1) == 0:
            user.gold += gold
            group_account.gold += gold
            return f"你获得了{gold}金币"
        else:
            user.gold -= gold
            group_account.gold -= gold
            user.props.setdefault("53101",0)
            user.props["53101"] += 1
            return f"你失去了{gold}金币。\n{bot_name}送你1个『{props_library['53101']['name']}』，祝你好运~"

    @classmethod
    def use_63102(cls, event:MessageEvent) -> str:
        """
        使用道具：重开券
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = user.props
        if props.get("63102",0) < 1:
            return "数量不足"

        props["63102"] -= 1
        if props["63102"] < 1:
            del props["63102"]

        group_id = group_account.group_id
        user_id = user.user_id
        for company_id in group_account.stocks:
            company = group_data[company_id].company
            company.stock += group_account.stocks[company_id]
            exchange = company.exchange
            if user_id in exchange:
                del exchange[user_id]
        user.gold -= group_account.gold
        group_data[group_id].namelist.remove(user_id)
        del group_account
        return "你在本群的账户已重置，祝你好运~"

def use_prop(event:MessageEvent, prop_name:str, count:int):
    if prop_code := props_index.get(prop_name):
        return Prop(prop_code).use(event,count)
    else:
        return f"没有【{prop_name}】这种道具。"
