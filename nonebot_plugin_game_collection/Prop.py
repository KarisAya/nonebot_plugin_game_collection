from typing import Tuple, Dict, Callable
import random

from .data import UserDict, GroupAccount, props_library
from .Processor import Event, Result
from .Alchemy import Alchemy
from . import Manager
from .utils.chart import linecard_to_png, line_splicing
from .config import bot_name, sign_gold, revolt_gold, max_bet_gold, gacha_gold

props_index: Dict[str, str] = {}

for prop_code, prop in props_library.items():
    props_index[prop["name"]] = prop_code
    props_index[prop_code] = prop_code


def get_prop(prop_code: str):
    return props_library.get(
        prop_code,
        {"name": prop_code, "color": "black", "rare": 1, "intro": "未知", "des": "未知"},
    )


def get_prop_name(prop_code: str) -> str:
    return get_prop(prop_code)["name"]


def get_prop_code(prop_name: str) -> str:
    return props_index.get(prop_name)


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
    code = random.randint(1, 100)
    if 0 < code <= 30:
        props = random.choice(["31001", "32001", "32002", "33001", "33101"])
    elif 30 < code <= 40:
        props = random.choice(["41001", "42001", "42002"])
    elif 40 < code <= 50:
        props = random.choice(["51001", "51002", "52001", "52002", "52101", "52102"])
    elif code == 51:
        props = random.choice(["61001", "62101"])
    elif code == 52:
        props = random.choice(["63101", "63102"])
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
    code = random.randint(1, 100)
    if 0 < code <= 30:
        props = "31001"
    elif 30 < code <= 40:
        props = "41001"
    elif 40 < code <= 50:
        props = random.choice(["51001", "51002"])
    elif code == 51:
        props = "61001"
    else:
        props = "11001"
    return props


def gacha(target: Tuple[UserDict, GroupAccount], N: int):
    """
    抽卡
    """
    user, group_account = target
    res = {}
    star = 0
    airstar = 0
    air = 0
    for i in range(N):
        prop_code = random_props()
        res.setdefault(prop_code, 0)
        res[prop_code] += 1
        rare = int(prop_code[0])
        star += rare
        if prop_code[1] == "1":
            airstar += rare
            air += 1
    else:
        data = sorted(res.items(), key=lambda x: int(x[0]), reverse=True)

    msg = ""
    airdata = []
    for prop_code, n in data:
        if prop_code[1] == "2":
            props = group_account.props
            props.setdefault(prop_code, 0)
            props[prop_code] += n
            quant = "天" if prop_code[2] == "0" else "个"
        elif prop_code[1] == "3":
            props = user.props
            props.setdefault(prop_code, 0)
            props[prop_code] += n
            quant = "天" if prop_code[2] == "0" else "个"
        else:
            airdata.append((prop_code, n))
            continue
        prop_info = props_library.get(
            prop_code,
            {
                "name": prop_code,
                "color": "black",
                "rare": 1,
                "intro": "未知",
                "des": "未知",
            },
        )
        color = prop_info["color"]
        name = prop_info["name"]
        rare = prop_info["rare"]
        msg += (
            f"[color][{color}]{name}[nowrap][passport]\n"
            f"[pixel][450]{rare*'☆'}[nowrap][passport]\n"
            f"[right]{n}{quant}\n"
        )

    user.props = {k: v if k in {"33101"} else min(v, 30) for k, v in user.props.items()}
    group_account.props = {
        k: v if k in {"62102"} else min(v, 30) for k, v in group_account.props.items()
    }
    for prop_code, n in airdata:
        prop_info = props_library.get(
            prop_code,
            {
                "name": prop_code,
                "color": "black",
                "rare": 1,
                "intro": "未知",
                "des": "未知",
            },
        )
        color = prop_info["color"]
        name = prop_info["name"]
        rare = prop_info["rare"]
        msg += (
            f"[color][{color}]{name}[nowrap][passport]\n"
            f"[pixel][450]{rare*'☆'}[nowrap][passport]\n"
            f"[right]{n}个\n"
        )

    if N >= 10:
        pt = star / N
        if pt < 1.6 or (air / N) > 0.8:
            if air == N:
                cost = N * gacha_gold
                level = "[center][color][#003300]只 有 空 气"
                user.gold += cost
                group_account.gold += cost
                msg = f"本次抽卡已免费（{cost}金币）\n" + msg
            else:
                level = "[center][color][#003300]理 想 气 体"
            n = N // 10
            user.props.setdefault("03103", 0)
            user.props["03103"] += n
            prop_info = props_library.get(
                "03103",
                {
                    "name": "03103",
                    "color": "black",
                    "rare": 1,
                    "intro": "未知",
                    "des": "未知",
                },
            )
            color = prop_info["color"]
            name = prop_info["name"]
            msg += f"[color][{color}]{name}[nowrap][passport]\n" f"[right]{n}个\n"
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
            f"抽卡次数：{N}[nowrap]\n"
            f"[pixel][450]空气占比：{round(air*100/N,2)}%\n"
            f"获得☆：{star}[nowrap]\n"
            f"[pixel][450]获得☆：{airstar}\n"
            f"平均每抽☆数：{round(pt,3)}[nowrap]\n"
            f"[pixel][450]空气质量：{round(airstar/air,3)}\n"
            f"数据来源：{group_account.nickname}\n"
            "----\n"
        ) + msg
    else:
        msg = (f"{group_account.nickname}\n" "----\n" f"抽卡次数：{N}\n" "----\n") + msg

    return linecard_to_png(msg, font_size=40, width=880, endline="抽卡结果")


def refine(target: Tuple[UserDict, GroupAccount], prop_code: str, count: int) -> str:
    """
    道具精炼
    """
    rare = {"1": 1, "3": 1, "4": 3, "5": 5, "6": 10}.get(prop_code[0])
    if not rare:
        return "此道具不可精炼"
    user, group_account = target
    props = user.props if prop_code[1] == "3" else group_account.props
    count = min(count, props.get(prop_code, 0))
    if not count:
        return "数量不足"

    props[prop_code] -= count
    if props[prop_code] < 1:
        del props[prop_code]
    count = count * rare
    user.props["33101"] = user.props.get("33101", 0) + count

    return f"精炼成功！你获得了{count}个{props_library['33101']['name']}"


def use_prop(event: Event, prop_name: str, count: int) -> Result:
    if prop_code := props_index.get(prop_name):
        prop = use.get(prop_code)
        if prop:
            return prop(event, count)
        else:
            return f"{prop_name}不是可用道具。"
    else:
        return f"没有【{prop_name}】这种道具。"


use: Dict[str, Callable] = {}


def add_prop(prop_name: str):
    """
    添加道具
    """
    prop_code = get_prop_code(prop_name)

    def decorator(function: Callable):
        if prop_code[1] == "3":
            locate_props_account = lambda user, group_account: user.props
        else:
            locate_props_account = lambda user, group_account: group_account.props

        def wrapper(event: Event, count: int) -> Result:
            user, group_account = Manager.locate_user(event)
            if not group_account:
                return "未关联账户，请发送【关联账户】关联群内账户。"
            props_account = locate_props_account(user, group_account)
            if props_account.get(prop_code, 0) < count:
                return "数量不足"
            props_account[prop_code] -= count
            if props_account[prop_code] < count:
                del props_account[prop_code]
            return function(user, group_account, event, count)

        use[prop_code] = wrapper

    return decorator


@add_prop("测试金库")
def _(user: UserDict, group_account: GroupAccount, event: Event, count: int) -> Result:
    return "你获得了10亿金币，100万钻石。祝你好运！"


@add_prop("被冻结的资产")
def _(user: UserDict, group_account: GroupAccount, event: Event, count: int) -> Result:
    gold = count * max_bet_gold
    user.gold += gold
    group_account.gold += gold
    return f"你获得了{gold}金币。"


@add_prop("空气礼包")
def _(user: UserDict, group_account: GroupAccount, event: Event, count: int) -> Result:
    N = count * 10

    res = {}
    star = 0
    airstar = 0
    air = 0
    for _ in range(N):
        prop_code = random_airs()
        res.setdefault(prop_code, 0)
        res[prop_code] += 1
        rare = int(prop_code[0])
        star += rare
        airstar += rare
        air += 1
    else:
        data = sorted(res.items(), key=lambda x: int(x[0]), reverse=True)

    msg = ""
    props = group_account.props
    for prop_code, n in data:
        props.setdefault(prop_code, 0)
        props[prop_code] += n
        prop_info = get_prop(prop_code)
        color = prop_info["color"]
        name = prop_info["name"]
        rare = prop_info["rare"]
        msg += (
            f"[color][{color}]{name}[nowrap][passport]\n"
            f"[pixel][450]{rare*'☆'}[nowrap][passport]\n"
            f"[right]{n}个\n"
        )

    pt = star / N
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
        f"抽卡次数：{N}[nowrap]\n"
        f"[pixel][450]空气占比：{round(air*100/N,2)}%\n"
        f"获得☆：{star}[nowrap]\n"
        f"[pixel][450]获得☆：{airstar}\n"
        f"平均每抽☆数：{round(pt,3)}[nowrap]\n"
        f"[pixel][450]空气质量：{round(airstar/air,3)}\n"
        f"数据来源：{group_account.nickname}\n"
        "----\n"
    ) + msg
    return linecard_to_png(msg, font_size=40, width=880, endline="抽卡结果")


@add_prop("初级元素")
def _(user: UserDict, group_account: GroupAccount, event: Event, count: int) -> Result:
    res = {}
    info = []
    if count <= 20:
        msg = ""
        for _ in range(count):
            originproduct = random.choices(Alchemy.elements, k=3)
            product = Alchemy.ProductsLibrary.get("".join(list(set(originproduct))), "")
            msg += f'|{"|".join(Alchemy.ProductsName[x] for x in originproduct)}| >>>> {Alchemy.ProductsName[product]}\n'
            res[product] = res.get(product, 0) + 1
        info.append(f"合成结果：\n----\n{msg[:-1]}")
    else:
        res = Alchemy.do(count)
    msg = ""
    for product, N in res.items():
        if product:
            user.alchemy[product] = user.alchemy.get(product, 0) + N
        msg += f"{Alchemy.ProductsName[product]}：{N}个\n"
    info.append(f"你获得了：\n----\n{msg[:-1]}")
    if count < 3:
        return "\n".join(info) + "\n祝你好运"
    else:
        return line_splicing(info)


@add_prop("神秘天平")
def _(user: UserDict, group_account: GroupAccount, event: Event, count: int) -> Result:
    group_id = group_account.group_id
    group = Manager.locate_group(group_id)
    ranklist = Manager.group_ranklist(group_id, "金币")
    info = []
    prop_name = get_prop_name("42001")
    for _ in range(count):
        target_id = random.choice([x[0] for x in ranklist if x[1] > revolt_gold[0]])
        if target_id == event.user_id:
            info.append(f"道具使用失败，你损失了一个『神秘天平』")
        target_user, target_group_account = Manager.locate_user_at(event, target_id)
        change = int((group_account.gold - target_group_account.gold) / 2)
        limit = min((group_account.gold, target_group_account.gold))
        limit = 0 if limit < 0 else limit
        if change > limit:
            change = limit
        if change < -limit:
            change = -limit
        abschange = abs(change)
        fee = int(abschange / 20)
        tag1, tag2 = "失去", "获得" if change > 0 else "获得", "失去"
        if group_account.props.get("42001", 0) > 0:
            user.gold -= change
            group_account.gold -= change
            msg1 = f"\n你{tag1}了{abschange}金币『{prop_name}』。"
        else:
            user.gold -= change
            group_account.gold -= change
            Manager.pay_tax((user, group_account), group, fee)
            msg1 = f"\n你{tag1}了{abs(change + fee)}金币(扣除5%手续费：{fee})。"
        if target_group_account.props.get("42001", 0) > 0:
            target_user.gold += change
            target_group_account.gold += change
            msg2 = f"\n对方{tag2}了{abschange}金币『{prop_name}』。"
        else:
            target_user.gold += change
            target_group_account.gold += change
            Manager.pay_tax((target_user, target_group_account), group, fee)
            msg2 = f"\n对方{tag2}了{abs(change - fee)}金币(扣除5%手续费：{fee})。"
        info.append(f"你与{target_group_account.nickname}平分了金币。" + msg1 + msg2)
    result = "\n".join(info)
    return linecard_to_png(result) if count > 3 else result


@add_prop("随机红包")
def _(user: UserDict, group_account: GroupAccount, event: Event, count: int) -> Result:
    gold = random.randint(sign_gold[0], revolt_gold[1]) * count
    user.gold += gold
    group_account.gold += gold
    return f"你获得了{gold}金币。祝你好运~"


@add_prop("重开券")
def _(user: UserDict, group_account: GroupAccount, event: Event, count: int) -> Result:
    for company_id in group_account.invest:
        company = Manager.locate_group(company_id).company
        company.Buyback(group_account)
    user.gold -= group_account.gold
    group_account.__init__(
        user_id=event.user_id,
        group_id=event.group_id,
        nickname=event.nickname,
    )
    return "你在本群的账户已重置，祝你好运~"


def add_prop_extra(prop_name: str):
    """
    添加特殊道具
    """
    prop_code = get_prop_code(prop_name)

    def decorator(function: Callable):
        use[prop_code] = function

    return decorator


@add_prop_extra("幸运硬币")
def _(event: Event, count: int) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "未关联账户，请发送【关联账户】关联群内账户。"
    props_account = group_account.props
    if props_account.get("52102", 0) < 1:
        return "数量不足"

    if count == 1:
        gold = int(group_account.gold / 2)
        X = 1
    else:
        if props_account.get("62101", 0) > 0:
            props_account["62101"] -= 1
            if props_account["62101"] < 1:
                del props_account["62101"]
        else:
            return "钻石数量不足"
        if count == 2:
            gold = int(group_account.gold / 2)
            X = 2
        else:
            gold = group_account.gold
            X = 1

    gold = gold if gold < (limit := 50 * max_bet_gold) else limit

    props_account["52102"] -= 1
    if props_account["52102"] < 1:
        del props_account["52102"]

    if random.randint(0, X) > 0:
        user.gold += gold
        group_account.gold += gold
        return f"你获得了{gold}金币"
    else:
        user.gold -= gold
        group_account.gold -= gold
        redpack = get_prop_code("随机红包")
        group_account.props.setdefault(redpack, 0)
        group_account.props[redpack] += 1
        return f"你失去了{gold}金币。\n{bot_name}送你1个『随机红包』，祝你好运~"


@add_prop_extra("超级幸运硬币")
def _(event: Event, count: int) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    props_account = user.props
    if props_account.get("63101", 0) < 1:
        return "数量不足"

    props_account["63101"] -= 1
    if props_account["63101"] < 1:
        del props_account["63101"]

    gold = group_account.gold

    if random.randint(0, 1) == 0:
        user.gold += gold
        group_account.gold += gold
        return f"你获得了{gold}金币"
    else:
        user.gold -= gold
        group_account.gold -= gold
        redpack = get_prop_code("随机红包")
        group_account.props.setdefault(redpack, 0)
        group_account.props[redpack] += 1
        return f"你失去了{gold}金币。\n{bot_name}送你1个『随机红包』，祝你好运~"


@add_prop_extra("道具兑换券")
def _(event: Event, count: int) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "私聊未关联账户，请发送【关联账户】关联群内账户。"
    props_account = group_account.props
    prop_name = "道具兑换券"
    if len(event.args) == 1:
        pass
    elif len(event.args) == 2:
        if event.args[1].isdigit():
            count = int(event.args[1])
        else:
            prop_name = event.args[1]
    else:
        event.args = event.args[1:]
        prop_name, count, _ = event.args_parse()
    prop_code = get_prop_code(prop_name)
    if not prop_code:
        return f"没有【{prop_name}】这种道具。"
    if prop_code[0] == "0":
        return "不能兑换特殊道具。"
    # 购买道具兑换券，价格 50抽
    props_account.setdefault("62102", 0)
    buy = max(count - props_account["62102"], 0)
    gold = buy * gacha_gold * 50
    if group_account.gold < gold:
        return f"金币不足。你还有{group_account.gold}枚金币。（需要：{gold}）"
    # 购买结算
    group_account.gold -= gold
    props_account["62102"] += buy
    # 道具结算
    if prop_code[1] == "3":
        account = user
    else:
        account = group_account
    account.props[prop_code] = account.props.get(prop_code, 0) + count
    props_account["62102"] -= count
    if props_account["62102"] < 1:
        del props_account["62102"]
    return f"你获得了{count}个【{prop_name}】！（使用金币：{gold}）"
