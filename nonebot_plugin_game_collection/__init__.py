from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from clovers.core.plugin import PluginLoader
from nonebot_plugin_clovers import clovers

__plugin_meta__ = PluginMetadata(
    name="小游戏合集",
    description="各种群内小游戏",
    usage="金币签到",
    type="application",
    homepage="https://github.com/KarisAya/nonebot_plugin_game_collection",
    supported_adapters={"nonebot.adapters.onebot.v11"},
)


def load_plugin(name: str):
    plugin = PluginLoader.load(name)
    if plugin is None:
        logger.error(f"未找到{name}")
    elif plugin not in clovers.plugins:
        clovers.plugins.append(plugin)
        logger.success(f"{name}加载成功")
    else:
        logger.success(f"{name}已存在")


load_plugin("clovers_apscheduler")
load_plugin("clovers_leafgame")
