from pathlib import Path

import re
import random
import time
import math
import datetime
import unicodedata

from .Processor import Event, Result, reg_command, reg_regex
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
from .utils.utils import format_number
from .config import (
    sign_gold,
    revolt_gold,
    revolt_cd,
    revolt_gini,
    max_bet_gold,
    gacha_gold,
    BG_image,
)


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
        alchemy_info(user.alchemy, user.nickname, await event.avatar()),
        Manager.BG_path(user.user_id),
        5,
    )
