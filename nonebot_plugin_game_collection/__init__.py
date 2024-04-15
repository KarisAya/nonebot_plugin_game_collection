from clovers.core.plugin import PluginLoader
from nonebot_plugin_clovers import adapter
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="小游戏合集",
    description="各种群内小游戏",
    usage="金币签到",
    type="application",
    homepage="https://github.com/KarisAya/nonebot_plugin_game_collection",
)


plugin = PluginLoader.load("clovers_leafgame")
if plugin is None:
    logger.error(f"未找到clovers_leafgame")
elif plugin not in adapter.plugins:
    adapter.plugins.append(plugin)
    logger.success(f"clovers_leafgame加载成功")
else:
    logger.success(f"clovers_leafgame已存在")
