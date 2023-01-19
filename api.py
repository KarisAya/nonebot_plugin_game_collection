from .data_source import russian_manager,market_manager

def russian_data() -> dict:
    """
    获取玩家数据
    """
    return russian_manager._player_data

def russian_data_save() -> int:
    """
    保存玩家数据
    """
    russian_manager.save()
    return 0