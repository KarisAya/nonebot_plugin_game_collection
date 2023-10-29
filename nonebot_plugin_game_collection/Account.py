from pathlib import Path

import re
import random
import time
import math
import datetime
import unicodedata

from .Processor import Event, Result, reg_command, reg_regex
from .Exceptions import SupArgsException
from . import Market
from . import Prop
from . import Alchemy
from . import Manager

from .utils.chart import (
    bar_chart,
    my_info_head,
    my_info_account,
    my_exchange_head,
    alchemy_info,
    linecard,
    info_splicing,
)
from .config import (
    sign_gold,
    revolt_gold,
    revolt_cd,
    revolt_gini,
    max_bet_gold,
    gacha_gold,
    BG_image,
)


@reg_command("sign", {"金币签到", "轮盘签到"}, need_extra_args={"avatar"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    user.avatar_url = event.extra_args.get("avatar")
    if not group_account:
        return "未关联账户，请发送【关联账户】关联群内账户。"
    if group_account.is_sign:
        return "你已经签过到了哦"
    else:
        gold = random.randint(sign_gold[0], sign_gold[1])
        user.gold += gold
        group_account.gold += gold
        group_account.is_sign = True
    return random.choice(["祝你好运~", "可别花光了哦~"]) + f"\n你获得了 {gold} 金币"


@reg_command("new_sign", {"重置签到", "领取金币"}, need_extra_args={"avatar"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    user.avatar_url = event.extra_args.get("avatar")
    if not group_account:
        return "未关联账户，请发送【关联账户】关联群内账户。"
    if group_account.revolution:
        return "你没有待领取的金币"
    else:
        gold = random.randint(revolt_gold[0], revolt_gold[1])
        user.gold += gold
        group_account.gold += gold
        group_account.revolution = True
    return f"这是你重置后获得的金币，你获得了 {gold} 金币"


@reg_command("revolution", {"发起重置"})
async def _(event: Event) -> Result:
    group_id = event.group_id
    group = Manager.locate_group(group_id)
    if time.time() - group.revolution_time < revolt_cd:
        return f"重置正在冷却中，结束时间：{datetime.datetime.fromtimestamp(group.revolution_time + revolt_cd).strftime('%H:%M:%S')}"
    if (group_gold := Manager.group_wealths(group_id)) < (limit := 15 * max_bet_gold):
        return f"本群金币（{round(group_gold,2)}）小于{limit}，未满足重置条件。"
    if (gini := Manager.gini_coef(group_id)) < revolt_gini:
        return f"当前基尼系数为{round(gini,3)}，未满足重置条件。"
    namelist = group.namelist
    level = group.company.level
    rank = []
    for user_id in namelist:
        group_account = Manager.locate_user_at(user_id, group_id)[1]
        rank.append(
            [
                user_id,
                group_account.gold + Manager.invest_value(group_account.invest) / level,
            ]
        )
    rank = [x for x in rank if x[1]]
    if rank:
        rank.sort(key=lambda x: x[1], reverse=True)
    else:
        return "群内没有排名"

    user_id = rank[0][0]
    group_account = Manager.locate_user_at(user_id, group_id)[1]
    group_account.props.setdefault("02101", 0)
    group_account.props["02101"] += 1
    group.revolution_time = time.time()
    group.Achieve_revolution[user_id] = group.Achieve_revolution.get(user_id, 0) + 1
    first_name = group_account.nickname
    i = 0.0
    for user_id, value in rank[:10]:
        user, group_account = Manager.locate_user_at(user_id, group_id)
        gold = int(value * i)
        user.gold = user.gold - group_account.gold + gold
        group_account.gold = gold
        for company_id, stock in group_account.invest.items():
            company = Manager.locate_group(company_id).company
            if user_id in company.exchange:
                del company.exchange[user_id]
            company.stock += stock
        group_account.invest.clear()
        i += 0.1

    users = Manager.locate_user_all(group_id)
    for user, group_account in users:
        group_account.revolution = False
    group.company.bank = int(group.company.bank * level / (level + 1))
    return f"重置成功！恭喜{first_name}进入挂件榜☆！\n当前系数为：{round(gini,3)}，重置签到已刷新。"


@reg_command("send_gold", {"发红包", "赠送金币"}, need_extra_args={"at"})
async def _(event: Event) -> Result:
    at = event.at()
    if not at:
        return
    at = at[0]
    gold = event.args_to_int()
    self_user, self_group_account = Manager.locate_user(event)
    target_user, target_group_account = Manager.locate_user_at(at, event.group_id)

    if self_group_account.gold < gold:
        return f"你没有足够的金币，无法完成结算。\n——你还有{self_group_account.gold}枚金币。"
    code = "42001"  # 钻石会员卡

    self_user.gold -= gold
    self_group_account.gold -= gold
    target_user.gold += gold
    target_group_account.gold += gold

    if target_group_account.props.get(code, 0):
        tips = f"『{Prop.get_prop_name(code)}』免手续费"
    else:
        fee = int(gold * 0.02)
        Manager.pay_tax(
            (target_user, target_group_account),
            Manager.locate_group(event.group_id),
            fee,
        )
        tips = f"扣除2%手续费：{fee}，实际到账金额{gold - fee}"

    return f"向 {target_group_account.nickname} 赠送{gold}金币\n" + tips


@reg_command("send_props", {"送道具", "赠送道具"}, need_extra_args={"at"})
async def _(event: Event) -> Result:
    at = event.at()
    if not at:
        return
    at = at[0]
    prop_name, count, _ = event.args_parse()
    prop_code = Prop.get_prop_code(prop_name)
    if not prop_code:
        return f"没有【{prop_name}】这种道具。"

    self_user, self_group_account = Manager.locate_user(event)
    target_user, target_group_account = Manager.locate_user_at(at, event.group_id)

    if prop_code[1] == "3":
        self_account = self_user
        target_account = target_user
    else:
        self_account = self_group_account
        target_account = target_group_account

    n = self_account.props.get(prop_code, 0)
    if n < count:
        return f"你没有足够的道具，无法完成结算。\n——你有{n}个【{prop_name}】。"
    self_account.props[prop_code] -= count
    target_account.props[prop_code] = target_account.props.get(prop_code, 0) + count
    return f"向 {target_group_account.nickname} 送出{count}个【{prop_name}】！"


@reg_command("my_gold", {"我的金币"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if group_account:
        return f"你还有 {group_account.gold} 枚金币"
    else:
        return "你的账户\n" + "\n".join(
            f"{group_id} 金币：{x.gold}枚" for group_id, x in user.group_accounts.items()
        )


@reg_command("my_info", {"我的信息", "我的资料"}, need_extra_args={"avatar"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "未关联账户，请发送【关联账户】关联群内账户。"
    info = []
    # 加载全局信息
    avatar = await event.avatar()
    user.avatar_url = event.extra_args.get("avatar")
    info.append(
        my_info_head(user.gold, user.win, user.lose, group_account.nickname, avatar)
    )
    # 加载卡片
    PropsCard = Manager.PropsCard_list((user, group_account))
    msg = ""
    for x in PropsCard:
        msg += f"----\n[center]{x}\n"
    if msg:
        info.append(
            linecard(msg + "----", width=880, padding=(0, -28), spacing=1, font_size=60)
        )
    # 加载成就卡片
    Achieve = Manager.Achieve_list((user, group_account))[:2]
    # 加载本群账户
    gold = group_account.gold
    value = Manager.invest_value(group_account.invest)
    is_sign = group_account.is_sign
    if is_sign:
        is_sign = ["已签到", "green"]
    else:
        is_sign = ["未签到", "red"]
    security = group_account.security
    if security:
        security = [security, "green"]
    else:
        security = [security, "red"]
    msg = ""
    for x in Achieve:
        msg += f"{x}\n"
    msg += (2 - len(Achieve)) * "\n"
    msg += (
        f"金币 {'{:,}'.format(gold)}\n"
        f"股票 {'{:,}'.format(round(value,2))}\n"
        "签到 [nowrap]\n"
        f"[color][{is_sign[1]}]{is_sign[0]}\n"
        "补贴 还剩 [nowrap]\n"
        f"[color][{security[1]}]{security[0]}[nowrap]\n 次"
    )
    # 加载资产分析
    dist = []
    for group_id, group_account in user.group_accounts.items():
        group_name = Manager.locate_group(group_id).company.company_name
        group_name = group_name if group_name else f"（{str(group_id)[:4]}）"
        dist.append(
            [
                group_account.gold + Manager.invest_value(group_account.invest),
                group_name,
            ]
        )
    dist = [x for x in dist if x[0] > 0]
    info.append(my_info_account(msg, dist or [(1.0, "None")]))
    # 加载股票信息
    msg = "\n".join(
        f"{Manager.locate_group(stock).company.company_name}[nowrap]\n[right][color][green]{i}"
        for stock, i in group_account.invest
        if i
    )
    if msg:
        info.append(linecard(msg, width=880, endline="股票信息"))

    return info_splicing(info, Manager.BG_path(event.user_id))


@reg_command("my_exchange", {"我的交易信息", "我的报价", "我的股票"}, need_extra_args={"avatar"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "未关联账户，请发送【关联账户】关联群内账户。"
    info = []
    # 加载股票信息
    for company_id, stock in group_account.invest.items():
        msg = ""
        if stock:
            account_name = "无报价"
            company = Manager.locate_group(company_id).company
            msg += f"[pixel][20]公司 {company.company_name}\n[pixel][20]结算 [nowrap]\n[color][green]{'{:,}'.format(round(company.float_gold/company.issuance,2))}[nowrap]\n[pixel][400]数量 [nowrap]\n[color][green]{stock}\n"
            if (exchange := company.exchange.get(user.user_id)) and exchange.n:
                if exchange.group_id == group_account.group_id:
                    account_name = "本群"
                else:
                    account_name = Manager.locate_group(
                        exchange.group_id
                    ).company.company_name
                    account_name = (
                        account_name
                        if account_name
                        else f"({str(exchange.group_id)[4]}...)"
                    )
                msg += f"[pixel][20]报价 [nowrap]\n[color][green]{exchange.quote}[nowrap]\n[pixel][400]发布 [nowrap]\n[color][green]{exchange.n}\n"
            info.append(linecard(msg, width=880, endline=f"报价账户：{account_name}"))
    if info:
        avatar = await event.avatar()
        user.avatar_url = event.extra_args.get("avatar")
        info.insert(
            0,
            my_exchange_head(
                group_account.gold, group_account.nickname, group_account.invest, avatar
            ),
        )
        return info_splicing(info, Manager.BG_path(event.user_id))
    else:
        return "你的股票信息为空。"


@reg_command("my_props", {"我的道具", "我的仓库"})
async def _(event: Event) -> Result:
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "未关联账户，请发送【关联账户】关联群内账户。"
    props = {}
    props.update(user.props)
    props.update(group_account.props)
    props = sorted(props.items(), key=lambda x: int(x[0]), reverse=True)
    if event.single_arg(" ") in {"信息", "介绍", "详情"}:

        def result(prop_code, n):
            quant = "天" if prop_code[2] == "0" else "个"
            prop = Manager.get_prop(prop_code)
            rare = prop["rare"]
            return linecard(
                (
                    f"[font_big][color][{prop['color']}]【{prop['name']}】[nowrap][passport]\n[right]{n}{quant}\n"
                    "----\n"
                    f"{prop['intro']}\n[right]{prop['des']}\n"
                ),
                width=880,
                padding=(0, 20),
                endline="特殊道具" if rare == 0 else rare * "☆",
                bg_color=(255, 255, 255, 153),
                autowrap=True,
            )

    else:

        def result(prop_code, n):
            quant = "天" if prop_code[2] == "0" else "个"
            prop = Prop.get_prop(prop_code)
            return linecard(
                f"[font_big][color][{prop['color']}]【{prop['name']}】[nowrap][passport]\n[right]{n}{quant}",
                width=880,
                padding=(0, 0),
                spacing=1.0,
                bg_color=(255, 255, 255, 153),
            )

    info = [result(prop_code, n) for prop_code, n in props if n > 0]
    return (
        info_splicing(info, Manager.BG_path(event.user_id), spacing=5)
        if info
        else "您的仓库空空如也。"
    )


@reg_regex("gacha", "^.+连抽?卡?|单抽", need_extra_args={"to_me"})
async def _(event: Event) -> Result:
    if not event.to_me():
        return
    N = re.search(r"^(.*)连抽?卡?$", event.raw_command)
    if not N:
        N = 1
    else:
        N = N.group(1)
        try:
            N = int(N)
        except ValueError:
            try:
                N = int(unicodedata.numeric(N))
            except (TypeError, ValueError):
                N = 1
    if N > 200:
        N = 200
    elif N < 1:
        N = 1

    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "未关联账户，请发送【关联账户】关联群内账户。"
    gold = N * gacha_gold
    if group_account.gold < gold:
        return f"{N}连抽卡需要{gold}金币，你的金币：{group_account.gold}。"
    user.gold -= gold
    group_account.gold -= gold
    return Prop.gacha((user, group_account), N)


@reg_command("use_prop", {"使用道具"})
async def _(event: Event) -> Result:
    prop_name, count, _ = event.args_parse()
    return Prop.use_prop(event, prop_name, count)


@reg_command("props_refine", {"道具精炼"})
async def _(event: Event) -> Result:
    prop_name, count, _ = event.args_parse()
    prop_code = Prop.get_prop_code(prop_name)
    if not prop_code:
        return f"没有【{prop_name}】这种道具。"
    target = Manager.locate_user(event)
    if not target[1]:
        return "未关联账户，请发送【关联账户】关联群内账户。"
    return Prop.refine(target, prop_code, count)


@reg_command("alchemy_refine", {"元素精炼"})
async def _(event: Event) -> Result:
    user = Manager.get_user(event.user_id)
    if not user:
        return
    if not event.args:
        return "未指定需要精炼的元素"
    return Alchemy.refine(user, event.args)


@reg_command("alchemy_info", {"炼金账户", "炼金资料"}, need_extra_args={"avatar"})
async def _(event: Event) -> Result:
    user = Manager.get_user(event.user_id)
    if not user:
        return
    return info_splicing(
        alchemy_info(user.alchemy, user.nickname, await event.avatar()).BG_path(
            user.user_id
        ),
        5,
    )


@reg_command("transfer_gold", {"金币转移"})
async def _(event: Event) -> Result:
    company_name, gold, _ = event.args_parse()
    user, group_account_out = Manager.locate_user(event)
    if not group_account_out:
        return "未关联账户，请发送【关联账户】关联群内账户。"
    if gold > group_account_out.gold:
        return f"你没有足够的金币，无法完成结算。\n——你还有{group_account_out.gold}枚金币。"

    company_id = Market.company_index.get(company_name)
    if not company_id:
        return f"没有 {company_name} 的注册信息"
    group_account_in = user.group_accounts.get(company_id)
    if not group_account_in:
        return f"你在 {company_name} 没有创建账户"
    company_out = Manager.locate_group(group_account_out.group_id).company
    company_in = Manager.locate_group(company_id).company
    ExRate = company_out.level / company_in.level
    # 计算转出
    transfer = company_out.transfer_limit + company_out.transfer
    if transfer < 1:
        return f"本群今日转出已达到限制({company_out.transfer_limit})"
    # 计算转入
    gold = int(ExRate * min(gold, transfer))
    transfer = company_out.transfer_limit - company_out.transfer
    if transfer < 1:
        return f"{company_in.company_name}今日转入已达到限制({company_in.transfer_limit})"
    # 转入
    gold_in = min(gold, transfer)
    company_in.transfer += gold_in
    user.gold += gold_in
    group_account_in.gold += gold_in
    # 转出
    gold_out = math.ceil(gold_in / ExRate)
    company_out.transfer -= gold_out
    user.gold -= gold_out
    group_account_out.gold -= gold_out

    return (
        f"向 {company_in.company_name} 转移{gold_out}金币。\n"
        f"汇率 {round(ExRate,2)}\n"
        f"实际到账金额 {gold_in}"
    )


@reg_command("add_BG_image", {"设置背景图片"}, need_extra_args={"image_list"})
async def _(event: Event) -> Result:
    user = Manager.get_user(event.user_id)
    if not user or user.props.get("33001", 0) < 1:
        return f"你的【{Prop.get_prop_name('33001')}】已失效"
    image = await event.image()
    if not image:
        return "图片下载失败"
    with open(BG_image / f"{str(event.user_id)}.png", "wb") as f:
        f.write(image.getvalue())
    return "图片下载成功"


@reg_command("del_BG_image", {"删除背景图片"})
async def _(event: Event) -> Result:
    Path.unlink(BG_image / f"{str(event.user_id)}.png", True)
    return "背景图片删除成功！"


def format_ranktitle(x: int, title: str = "金币"):
    """
    根据排行榜将数据格式化
    """
    if title == "金币" or title == "总金币":
        return "{:,}".format(x)
    elif title == "总资产" or title == "资产" or title == "财富":
        return "{:,}".format(round(x, 2))
    elif title == "胜率":
        return f"{round(x*100,2)}%"
    else:
        return x


async def draw_rank(
    ranklist: list, title: str = "金币", top: int = 20, group_id=None, bg_id=None
):
    """
    排名信息
    """
    first = ranklist[0][1]
    if group_id:
        nicname = lambda user: user.group_accounts[group_id].nickname
    else:
        nicname = lambda user: user.nickname
    info = []
    for i, (user_id, x) in enumerate(ranklist[:top]):
        user = Manager.get_user(user_id)
        info.append(
            await bar_chart(
                f"{i+1}.{nicname(user)}：{format_ranktitle(x,title)}\n", x / first
            )(user.avatar_url)
        )
    return info_splicing(info, Manager.BG_path(bg_id), spacing=5)


@reg_regex("group_rank", r"^(总金币|总资产|金币|资产|财富|胜率|胜场|败场|路灯挂件)(排行|榜)")
async def _(event: Event):
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "未关联账户，请发送【关联账户】关联群内账户。"
    title = re.search(
        r"^(总金币|总资产|金币|资产|财富|胜率|胜场|败场|路灯挂件)(排行|榜)", event.raw_command.strip()
    ).group(1)
    user_id = user.user_id
    group_id = group_account.group_id
    if not (ranklist := Manager.group_ranklist(group_id, title)):
        return "无数据。"
    return await draw_rank(ranklist, title, 20, group_id=group_id, bg_id=user_id)


@reg_regex("all_rank", r"^(金币|资产|财富|胜率|胜场|败场|路灯挂件)(总排行|总榜)")
async def _(event: Event) -> Result:
    title = re.search(
        r"^(金币|资产|财富|胜率|胜场|败场|路灯挂件)(总排行|总榜)", event.raw_command.strip()
    ).group(1)
    if not (ranklist := Manager.All_ranklist(title)):
        return None
    return await draw_rank(ranklist, title, 20, bg_id=event.user_id)


"""+++++++++++++++++++++++++++++++++++++
————————————————————
   ᕱ⑅ᕱ。    超管权限指令
  (｡•ᴗ-)_
————————————————————
+++++++++++++++++++++++++++++++++++++"""


@reg_command("gain_gold", {"获取金币"}, need_extra_args={"permission"})
async def _(event: Event) -> Result:
    if event.permission() != 3:
        return
    gold = event.args_to_int()
    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "未关联账户，请发送【关联账户】关联群内账户。"

    user.gold += gold
    group_account.gold += gold
    return f"你获得了 {gold} 金币"


@reg_command("gain_prop", {"获取道具"}, need_extra_args={"permission"})
async def _(event: Event) -> Result:
    if event.permission() != 3:
        return
    prop_name, count, _ = event.args_parse()
    prop_code = Prop.get_prop_code(prop_name)
    if not prop_code:
        return f"没有【{prop_name}】这种道具。"

    user, group_account = Manager.locate_user(event)
    if not group_account:
        return "未关联账户，请发送【关联账户】关联群内账户。"

    if prop_code[1] == "3":
        account = user
    else:
        account = group_account

    account.props.setdefault(prop_code, 0)
    account.props[prop_code] += count
    return f"你获得了{count}个【{prop_name}】！"


@reg_command("freeze", {"冻结资产"}, need_extra_args={"permission", "at"})
async def _(event: Event) -> Result:
    if event.permission() != 3:
        return
    at = event.at()
    if not at:
        return
    at = at[0]
    user = Manager.locate_user_at(at, event.group_id)[0]
    confirm = "".join(str(random.randint(0, 9)) for _ in range(4))

    @event.got()
    async def _(inner_event: Event) -> str:
        if inner_event.args[0] != confirm:
            inner_event.finish()
            return "【冻结】已取消。"
        gold = 0
        value = 0.0
        for group_id, group_account in user.group_accounts.items():
            group = Manager.locate_group(group_id)
            gold += group_account.gold * group.company.level
            for company_id, n in group_account.invest.items():
                inner_company = Manager.locate_group(company_id).company
                unit = inner_company.float_gold / inner_company.issuance
                value += unit * n
                inner_company.Buyback(group_account)
            group.namelist.remove(user.user_id)
        user.gold = 0
        user.group_accounts = {}
        x = gold + value
        count = math.ceil(x / max_bet_gold)
        count = 500 if count > 500 else count
        user.props.setdefault("03101", 0)
        user.props["03101"] += count
        inner_event.finish()
        return f"【冻结】清算完成，总价值为 {round(x,2)}（金币 {gold} 股票 {round(value,2)}）"

    return f"您即将冻结 {user.nickname}（{at}），请输入{confirm}来确认。"
