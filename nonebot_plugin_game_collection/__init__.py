from nonebot import require
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_clovers")
from nonebot_plugin_clovers import client

__plugin_meta__ = PluginMetadata(
    name="小游戏合集",
    description="各种群内小游戏",
    usage="金币签到",
    type="application",
    homepage="https://github.com/KarisAya/nonebot_plugin_game_collection",
    supported_adapters=None,
)
IMPORT_NAME = "clovers_sarof"
require("nonebot_plugin_clovers")
from nonebot_plugin_clovers import client

client.load_plugin(IMPORT_NAME)
client.load_plugin("clovers_apscheduler")
