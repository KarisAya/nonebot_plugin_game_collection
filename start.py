from nonebot.log import logger
from nonebot import get_driver
import json
import os

async def load_dlcs():
    events_list = []
    logs = f""
    files = os.listdir(os.path.dirname(__file__) + '/events/horserace')
    for file in files:
        try:
            with open(f'{os.path.dirname(__file__)}/events/horserace/{file}', "r", encoding="utf-8") as f:
                logger.info(f'加载事件文件：{file}')
                events = deal_events(json.load(f))
                events_list.extend(events)
            logger.info(f"加载 {file} 成功")
            logs += f'加载 {file} 成功\n'
        except:
            logger.info(f"加载 {file} 失败！失败！失败！")
            logs += f"加载 {file} 失败！失败！失败！\n"
    return events_list



def deal_events(events):
    events_out = []
    for i in range(0,len(events)):
        event_i = deal(events[i])
        if event_i != {}:
            events_out.append(event_i)
    return events_out

def deal(event):
    event_out = {}
    # 读取事件限定值
    try:
        event_out["race_only"] = event["race_only"]
        event_out["race_only_exist"] = 1
    except KeyError:
        event_out["race_only_exist"] = 0
    # 读取 event_name 无则未知事件
    try:
        event_out["event_name"] = event["event_name"]
    except KeyError:
        event_out["event_name"] = "未知事件"
    # 读取 describe 事件描述，无描述则空
    try:
        event_out["describe"] = event["describe"]
    except KeyError:
        event_out["describe"] = f""
    # 读取 target 目标，无则销毁事件
    try:
        event_out["target"] = event["target"]
    except KeyError:
        return {}
    # 判定target_is_buff
    try:
        event_out["target_is_buff"] = event["target_is_buff"]
    except KeyError:
        event_out["target_is_buff"] = f""
    # 判定target_no_buff
    try:
        event_out["target_no_buff"] = event["target_no_buff"]
    except KeyError:
        event_out["target_no_buff"] = f""
    # ===============以下为一次性事件===============
    # 复活事件：为1则目标复活
    try:
        event_out["live"] = event["live"]
    except KeyError:
        event_out["live"] = 0
    # 位移事件：目标立即进行相当于参数值的位移
    try:
        event_out["move"] = event["move"]
    except KeyError:
        event_out["move"] = 0
    # 随机位置事件：有值则让目标移动到指定位置
    try:
        event_out["track_to_location"] = event["track_to_location"]
        event_out["track_to_location_exist"] = 1
    except KeyError:
        event_out["track_to_location_exist"] = 0
    # 随机位置事件：为1则让目标随机位置（位置范围为可设定值，见setting.py）
    try:
        event_out["track_random_location"] = event["track_random_location"]
    except KeyError:
        event_out["track_random_location"] = 0
    # buff持续时间调整事件：目标所有buff增加/减少回合数
    try:
        event_out["buff_time_add"] = event["buff_time_add"]
    except KeyError:
        event_out["buff_time_add"] = 0
    # 删除buff事件：下回合删除目标含特定buff_tag的所有buff
    try:
        event_out["del_buff"] = event["del_buff"]
    except KeyError:
        event_out["del_buff"] = f""
    # 换位事件：值为1则与目标更换位置 （仅target为1,6时生效）
    try:
        event_out["track_exchange_location"] = event["track_exchange_location"]
    except KeyError:
        event_out["track_exchange_location"] = 0
    # 一次性随机事件
    try:
        event_out["random_event_once"] = event["random_event_once"]
        if event_out["random_event_once"] != []:
            for i in range(0, len(event_out["random_event_once"])):
                event_out["random_event_once"][i][1] = deal(event_out["random_event_once"][i][1])
    except KeyError:
        event_out["random_event_once"] = []
    # ===============以下为永久事件===============
    # buff_tag，死亡：为1则目标死亡，此参数生成的buff默认持续999回合
    # buff_tag：die的自定义名称，不填为“死亡”
    try:
        event_out["die"] = event["die"]
    except KeyError:
        event_out["die"] = 0
    try:
        event_out["die_name"] = event["die_name"]
    except KeyError:
        event_out["die_name"] = "死亡"
    # buff_tag，离开：为1则目标离开，此参数生成的buff默认持续999回合
    # buff_tag：away的自定义名称，不填为“离开”
    try:
        event_out["away"] = event["away"]
    except KeyError:
        event_out["away"] = 0
    try:
        event_out["away_name"] = event["away_name"]
    except KeyError:
        event_out["away_name"] = "离开"
    # ==============================连锁事件预留位置，暂时没做

    # ===============以下为buff事件===============
    # "rounds": 0,                #buff持续回合数
    # "name": "xxx",              #buff名称，turn值>0时为必要值
    # "move_max": 0,              #该buff提供马儿每回合位移值区间的最大值（move_max若小于move_min，则move_max以move_min值为准）
    # "move_min": 0,              #该buff提供马儿每回合位移值区间的最小值
    # "locate_lock": 0,           #buff_tag，止步：若为1则目标无法移动
    # "vertigo": 0,               #buff_tag，眩晕：若为1则目标无法移动，且不主动执行事件（暂定）
    # "hiding": 0,                #buff_tag，隐身：不显示目标移动距离及位置
    # "other_buff": ["buff1", "buff2", ....]
    #                            #自定义buff_tag，仅标识用buff_tag填写处，也可以填入常规buff_tag并正常生效
    # "random_event": [[概率值1, {事件}], [概率值2, {事件}], ......],
    # 此为持续性随机事件，以buff形式存在，部分详见文末
    try:
        event_out["rounds"] = event["rounds"]
    except KeyError:
        event_out["rounds"] = 0
    try:
        event_out["name"] = event["name"]
    except KeyError:
        event_out["name"] = "未命名buff"
    try:
        event_out["move_max"] = event["move_max"]
    except KeyError:
        event_out["move_max"] = 0
    try:
        event_out["move_min"] = event["move_min"]
    except KeyError:
        event_out["move_min"] = 0
    if event_out["move_max"] < event_out["move_min"]:
        event_out["move_max"] = event_out["move_min"]
    try:
        event_out["locate_lock"] = event["locate_lock"]
    except KeyError:
        event_out["locate_lock"] = 0
    try:
        event_out["vertigo"] = event["vertigo"]
    except KeyError:
        event_out["vertigo"] = 0
    try:
        event_out["hiding"] = event["hiding"]
    except KeyError:
        event_out["hiding"] = 0
    try:
        event_out["other_buff"] = event["other_buff"]
    except KeyError:
        event_out["other_buff"] = []
    try:
        event_out["random_event"] = event["random_event"]
        if event_out["random_event"] != []:
            for i in range(0, len(event_out["random_event"])):
                event_out["random_event"][i][1] = deal(event_out["random_event"][i][1])
    except KeyError:
        event_out["random_event"] = []
    # ===============以下为延迟事件===============
    # 延迟事件（以当前事件的targets为发起人的事件）：前者为多少回合后，需>1
    try:
        delay_event = event["delay_event"]
        if event_out["delay_event"] != []:
            event_out["delay_event"][1] = deal(event_out["delay_event"][1])
    except KeyError:
        event_out["delay_event"] = []
    # 延迟事件（以当前事件发起人为发起人的事件）：前者为多少回合后，需>1
    try:
        event_out["delay_event_self"] = event["delay_event_self"]
        if event_out["delay_event_self"] != []:
            event_out["delay_event_self"][1] = deal(event_out["delay_event_self"][1])
    except KeyError:
        event_out["delay_event_self"] = []
    # ===============以下同步事件===============
    # 同步事件（以当前事件的targets为发起人的事件），执行此事件后立马执行该事件
    try:
        event_out["another_event"] = event["another_event"]
        event_out["another_event"] = deal(event_out["another_event"])
    except KeyError:
        event_out["another_event"] = {}
    # 同步事件（以当前事件发起人为发起人的事件），执行此事件后立马执行该事件
    try:
        event_out["another_event_self"] = event["another_event_self"]
        event_out["another_event_self"] = deal(event_out["another_event_self"])
    except KeyError:
        event_out["another_event_self"] = {}
    # ==========永久事件2，换赛道/加马==========
    # 增加一匹马事件
    try:
        event_out["add_horse"] = event["add_horse"]
    except KeyError:
        event_out["add_horse"] = {}
    # 替换一匹马事件
    try:
        event_out["replace_horse"] = event["replace_horse"]
    except KeyError:
        event_out["replace_horse"] = {}
    return event_out
