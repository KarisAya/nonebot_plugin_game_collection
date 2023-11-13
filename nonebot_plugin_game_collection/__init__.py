from nonebot import require, on_message, on_command, on_fullmatch
from nonebot.permission import SUPERUSER
from nonebot.matcher import Matcher
from nonebot.log import logger

import time
import datetime
import shutil

from .Processor import Event, run

from . import Manager
from . import Market
from . import Account as _
from . import Game as _

from .data import menu_data
from .utils.utils import extract_command
from .config import Config, path, backup

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="小游戏合集",
    description="各种群内小游戏",
    usage="金币签到",
    config=Config,
    extra={"menu_data": menu_data, "menu_template": "default"},
)

from nonebot.adapters.qq import Bot as QQBot, MessageEvent as QQMessageEvent
from .adapters.qq import Adapters as QQAdapters, send as QQsend

main = on_message(priority=20, block=False)


@main.handle()
async def _(matcher: Matcher, bot: QQBot, event: QQMessageEvent):
    data_list = Event.check(
        extract_command(event.get_plaintext()),
        event.get_user_id(),
        str(getattr(event, "guild_id", "private")),
    )
    if not data_list:
        await main.finish()
    matcher.stop_propagation()
    for _data in data_list:
        await QQsend(main.send, await run(_data, QQAdapters, bot, event))
    await main.finish()


from nonebot.adapters.onebot.v11 import (
    Bot as OneBot,
    MessageEvent as OneBotMessageEvent,
)
from .adapters.v11 import Adapters as OneBotAdapters, send as OneBotsend


@main.handle()
async def _(matcher: Matcher, bot: OneBot, event: OneBotMessageEvent):
    data_list = Event.check(
        extract_command(event.get_plaintext()),
        event.get_user_id(),
        str(getattr(event, "group_id", "private")),
    )
    if not data_list:
        await main.finish()
    matcher.stop_propagation()
    for _data in data_list:
        await OneBotsend(main.send, await run(_data, OneBotAdapters, bot, event))
    await main.finish()


"""+++++++++++++++++++++++++++++++++++++
————————————————————
   ᕱ⑅ᕱ。    不需要使用依赖的指令
  (｡•ᴗ-)_
————————————————————
+++++++++++++++++++++++++++++++++++++"""


scheduler = require("nonebot_plugin_apscheduler").scheduler


# 市场更新
@scheduler.scheduled_job("cron", minute="*/5", misfire_grace_time=120)
async def _():
    log = Market.update()
    if log:
        logger.info("\n" + log)


# 数据验证
DataVerif = on_command(
    "数据验证", aliases={"数据校验"}, permission=SUPERUSER, priority=20, block=True
)


@DataVerif.handle()
async def _():
    log = Manager.data.verification()
    logger.info(f"\n{log}")


# 数据备份
Backup = on_command(
    "Backup", aliases={"数据备份", "游戏备份"}, permission=SUPERUSER, priority=20, block=True
)


@Backup.handle()
@scheduler.scheduled_job("cron", hour="*/4", misfire_grace_time=120)
async def _():
    now = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(time.time()))
    now = now.split()
    backup_today = backup / now[0]
    if not backup_today.exists():
        backup_today.mkdir()
    Manager.data.save()
    shutil.copy(
        f"{path}/russian_data.json", f"{backup_today}/russian_data {now[1]}.json"
    )
    logger.info(f"russian_data.json 备份成功！")


# 刷新每日
Newday = on_command(
    "Newday", aliases={"刷新每日", "刷新签到"}, permission=SUPERUSER, priority=20, block=True
)


@Newday.handle()
@scheduler.scheduled_job("cron", hour=0, misfire_grace_time=120)
async def _():
    log = Manager.data.verification()
    logger.info(f"\n{log}")
    Market.update_company_index()
    Market.new_order()
    Manager.data.Newday()
    with open(path / "Newday.log", "a", encoding="utf8") as f:
        f.write(
            f"\n{datetime.datetime.fromtimestamp(time.time()).strftime('%Y 年 %m 月 %d 日 %H:%M:%S')}\n"
            "——————————————\n"
            f"{log}\n"
            "——————————————\n"
        )
    folders = [f for f in backup.iterdir() if f.is_dir()]
    for folder in folders:
        if time.time() - folder.stat().st_ctime > 604800:
            shutil.rmtree(folder)
            logger.info(f"备份 {folder} 已删除！")


# 保存数据
DataSave = on_command(
    "DataSave", aliases={"保存数据", "保存游戏"}, permission=SUPERUSER, priority=20, block=True
)


@DataSave.handle()
@scheduler.scheduled_job("cron", minute="*/10", misfire_grace_time=120)
async def _():
    Manager.data.save()
    Manager.market_history.save()
    logger.info(f"游戏数据已保存！！")


# 清理市场账户
cancellation = on_fullmatch("清理市场账户", permission=SUPERUSER, priority=20, block=True)


@cancellation.handle()
async def _():
    await cancellation.send("正在启动清理程序。")
    result = "\n".join(await Manager.cancellation())
    Market.update_company_index()
    await cancellation.finish(f"清理完成！\n已删除以下公司：\n{result}")
