from nonebot.plugin import PluginMetadata
from nonebot_plugin_clovers import clovers

__plugin_meta__ = PluginMetadata(
    name="小游戏合集",
    description="各种群内小游戏",
    usage="金币签到",
    type="application",
    homepage="https://github.com/KarisAya/nonebot_plugin_game_collection",
    supported_adapters={"nonebot.adapters.onebot.v11"},
)

clovers.load_plugin("clovers_apscheduler")
clovers.load_plugin("clovers_leafgame")