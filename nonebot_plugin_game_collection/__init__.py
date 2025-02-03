from nonebot import on_message, get_driver
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from clovers import Leaf
from nonebot_plugin_clovers import extract_command
from nonebot_plugin_clovers.adapters.onebot.v11 import __adapter__ as onebot_v11
from clovers_apscheduler import __plugin__ as apscheduler
from clovers_leafgame import __plugin__ as leafgame

__plugin_meta__ = PluginMetadata(
    name="小游戏合集",
    description="各种群内小游戏",
    usage="金币签到",
    type="application",
    homepage="https://github.com/KarisAya/nonebot_plugin_game_collection",
    supported_adapters={"nonebot.adapters.onebot.v11"},
)

leaf = Leaf(onebot_v11)

leaf.plugins.append(apscheduler)
leaf.plugins.append(leafgame)


driver = get_driver()

Bot_NICKNAME = Bot_NICKNAMEs[0] if (Bot_NICKNAMEs := list(driver.config.nickname)) else "bot"


@leaf.adapter.property_method("Bot_Nickname")
async def _():
    return Bot_NICKNAME


driver.on_startup(leaf.startup)
driver.on_shutdown(leaf.shutdown)

main = on_message(priority=20, block=False)


@main.handle()
async def _(bot: Bot, event: MessageEvent, matcher: Matcher):
    if await leaf.response(extract_command(event.get_plaintext()), bot=bot, event=event):
        matcher.stop_propagation()
