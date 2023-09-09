from webbrowser import get
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    GroupMessageEvent,
    MessageSegment
    )
import random
import math
from .utils.utils import get_message_at
from .utils.chart import linecard_to_png,line_splicing
from .data import props_library, props_index, update_props_index
from .config import path,bot_name, sign_gold, revolt_gold, max_bet_gold, gacha_gold

from .Alchemy import Alchemy
from . import Manager

try:
    import ujson as json
except ModuleNotFoundError:
    import json

data = Manager.data
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
            msg = self.use_42101(event,count)
            if count > 10:
                return MessageSegment.image(linecard_to_png(msg))
            else:
                return msg
        elif self == "52101":
            msg = self.use_52101(event,count)
            if count > 3:
                return MessageSegment.image(linecard_to_png(msg))
            else:
                return msg

        elif self == "52102":
            return self.use_52102(event,count)
        elif self == "53101":
            return self.use_53101(event,count)
        elif self == "62102":
            return self.use_62102(event,count)
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
        level = Manager.company_level(group_account.group_id)
        gold = math.ceil(count * max_bet_gold / level)
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
        info = []
        if count <= 20:
            msg = ""
            for _ in range(count):
                originproduct = random.choices(Alchemy.elements,k = 3)
                product = Alchemy.ProductsLibrary.get("".join(list(set(originproduct))),"")
                msg += f'|{"|".join(Alchemy.ProductsName[x] for x in originproduct)}| >>>> {Alchemy.ProductsName[product]}\n'
                res[product] = res.get(product, 0) + 1
            info.append(f"合成结果：\n----\n{msg[:-1]}")
        else:
            res = Alchemy.do(count)
        msg = ""
        for product,N in res.items():
            if product:
                user.alchemy[product] = user.alchemy.get(product, 0) + N
            msg += f'{Alchemy.ProductsName[product]}：{N}个\n'
        info.append(f"你获得了：\n----\n{msg[:-1]}")
        if count < 3:
            return "\n".join(info) + "\n祝你好运"
        else:
            return MessageSegment.image(line_splicing(info))

    @classmethod
    def use_42101(cls, event:MessageEvent, count:int) -> str:
        """
        使用道具：调查凭证
        """
        if isinstance(event, GroupMessageEvent):
            group_id = event.group_id
        else:
            return f"此道具只能在群内使用"

        if not (at := get_message_at(event.message)):
            at = event.message.extract_plain_text().strip().split()[-1]
            try:
                at = int(at)
            except:
                return "没有指定用户。"
            group = group_data.get(group_id)
            if not group or at not in group.namelist:
                return "没有指定用户。"
            if at == count:
                count = 1
        else:
            at = int(at[0])

        user,group_account = Manager.locate_user(event)
        target_user,target_group_account = Manager.locate_user_at(event,at)

        props = group_account.props
        if props.get("42101",0) < count:
            return "数量不足"

        props["42101"] -= count
        if props["42101"] < 1:
            del props["42101"]

        info = []
        for _ in range(count):
            N = random.randint(0,50)
            if N < 30:
                gold = int(group_account.gold * N / 1000)
                gold = 0 if gold < 0 else gold
                user.gold -= gold
                group_account.gold -= gold
                target_user.gold += gold
                target_group_account.gold += gold
                info.append(f"调查没有发现问题。你赔偿了对方{gold}枚金币（{N/10}%）")
            else:
                gold = int(target_group_account.gold * N / 1000)
                gold = min(group_account.gold, gold)
                gold = 0 if gold < 0 else gold
                user.gold += gold
                group_account.gold += gold
                target_user.gold -= gold
                target_group_account.gold -= gold
                info.append(f"你获得了对方{gold}枚金币（{N/10}%）")
        return "\n".join(info)

    @classmethod
    def use_52101(cls, event:MessageEvent, count:int) -> str:
        """
        使用道具：神秘天平
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = group_account.props
        if props.get("52101",0) < count:
            return "数量不足"

        props["52101"] -= count
        if props["52101"] < 1:
            del props["52101"]

        group_id = group_account.group_id
        ranklist = Manager.group_ranklist(group_id,"金币")
        info = []
        for _ in range(count):
            target_id = random.choice([x[0] for x in ranklist if x[1] > revolt_gold[0]])
            if target_id == event.user_id:
                info.append(f"道具使用失败，你损失了一个『{props_library['52101']['name']}』")
            target_user,target_group_account = Manager.locate_user_at(event, target_id)
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
                group_data[group_id].company.bank += fee
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
                group_data[group_id].company.bank += fee
                msg2 = f"\n对方{tag}了{abs(change - fee)}金币(扣除5%手续费：{fee})。"

            info.append(f"你与{target_group_account.nickname}平分了金币。" + msg1 + msg2)

        return "\n".join(info)

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

        gold = random.randint(sign_gold[0], revolt_gold[1]) * count
        user.gold += gold
        group_account.gold += gold
        return f"你获得了{gold}金币。祝你好运~"

    @classmethod
    def use_62102(cls, event:MessageEvent, count:int) -> str:
        """
        使用道具：道具兑换券
        """
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = group_account.props
        prop_name = event.message.extract_plain_text().rstrip()[4:].split()[-1]
        if prop_name == str(count):
            prop_code = "62102"
            prop_name = props_library['62102']['name']
        else:
            prop_code = props_index.get(prop_name)
            if not prop_code:
                return f"没有【{prop_name}】这种道具。"
            if prop_code[0] == "0":
                return "不能兑换特殊道具。"

        # 购买道具兑换券，价格 50抽
        props.setdefault("62102",0)
        buy = max(count - props["62102"],0)
        gold = buy * gacha_gold * 50
        if group_account.gold < gold:
            return f"金币不足。你还有{group_account.gold}枚金币。（需要：{gold}）"
        # 购买结算
        group_account.gold -= buy * gacha_gold * 50
        props["62102"] += buy
        # 道具结算
        if prop_code[1] == "3":
            account = user
        else:
            account = group_account
        account.props[prop_code] = account.props.get(prop_code,0) + count
        props["62102"] -= count
        if props["62102"] < 1:
            del props["62102"]
        return f"你获得了{count}个【{prop_name}】！（使用金币：{gold}）" 

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
        for company_id in group_account.stocks:
            company = group_data[company_id].company
            company.Buyback(group_account)
        user.gold -= group_account.gold
        group_account.__init__(
            user_id = group_account.user_id,
            group_id = group_account.group_id,
            nickname = group_account.nickname,
            gold = 0 if group_account.gold > 0 else group_account.gold 
            )
        return "你在本群的账户已重置，祝你好运~"

    @staticmethod
    def refine(event:MessageEvent, prop_code:str, count:int) -> str:
        """
        道具精炼
        """
        rare = {"3":1,"4":3,"5":5,"6":10}.get(prop_code[0])
        if not rare:
            return "此道具不可精炼"
        user,group_account = Manager.locate_user(event)
        if not group_account:
            return "私聊未关联账户，请发送【关联账户】关联群内账户。"
        props = user.props if prop_code[1] == "3" else group_account.props
        count = min(count,props.get(prop_code,0))
        if not count:
            return "数量不足"

        props[prop_code] -= count
        if props[prop_code] < 1:
            del props[prop_code]
        count = count * rare
        user.props["33101"] = user.props.get("33101",0) + count

        return f"精炼成功！你获得了{count}个{props_library['33101']['name']}"

def use_prop(event:MessageEvent, prop_name:str, count:int):
    if prop_code := props_index.get(prop_name):
        return Prop(prop_code).use(event,count)
    else:
        return f"没有【{prop_name}】这种道具。"

def props_refine(event:MessageEvent, prop_name:str, count:int):
    if prop_code := props_index.get(prop_name):
        return Prop.refine(event,prop_code,count)
    else:
        return f"没有【{prop_name}】这种道具。"

# 加载用户道具

datafile = path / "props_library.json"

if datafile.exists():
    with open(datafile, "r") as f:
        customer_props_library = json.load(f)
else:
    customer_props_library = {}

props_library.update(customer_props_library)
update_props_index(props_index)

def prop_create(*args):
    code,name,color,rare,intro,des = args
    prop = {
        "name":name,
        "color":color,
        "rare":rare,
        "intro":intro,
        "des":des
        }
    if name in props_index:
        return f"道具【{name}】已存在"
    def register():
        for i in range(51,100):
            prop_code = f"{code}{i}"
            if prop_code not in customer_props_library:
                return prop_code
    if not(prop_code := register()):
        return "新建道具已达上限"
    props_library[prop_code] = prop
    customer_props_library[prop_code] = prop
    props_index[prop_code] = prop_code
    props_index[name] = prop_code
    with open(datafile,"w") as f:
        json.dump(customer_props_library,f,ensure_ascii = False, indent = 4)
    return f"道具【{name}】创建成功"

def prop_delete(prop_name):
    if not (prop_code := props_index.get(prop_name)):
        return f"道具名【{prop_name}】不存在"
    if prop_code not in customer_props_library:
        return f"道具名【{prop_name}】无法删除"
    del props_library[prop_code]
    del customer_props_library[prop_code]
    update_props_index(props_index)
    for user in user_data.values():
        if prop_code in user.props:
            user.props ={k:v for k,v in user.props.items() if k in props_index} 
        for group_account in user.group_accounts.values():
            user.props ={k:v for k,v in group_account.props.items() if k in props_index} 
    with open(datafile,"w") as f:
        json.dump(customer_props_library,f,ensure_ascii = False, indent = 4)
    return f"【{prop_name}】删除成功"