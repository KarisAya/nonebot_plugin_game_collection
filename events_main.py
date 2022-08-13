import random
from .horse import horse
from .setting import  *
from nonebot.log import logger

def event_main(race, horse_i, event, event_delay_key = 0):
    try:
    #读取 event_name
        event_name = event["event_name"]
    #该马儿是否死亡/离开/眩晕，死亡则结束事件链
        if race.player[horse_i].is_die() == True and event_delay_key == 0:
            return f''
        elif race.player[horse_i].is_away() == True and event_delay_key == 0:
            return f''
        elif race.player[horse_i].find_buff("vertigo") == True and event_delay_key == 0:
            return f''
    #读取事件限定值
        if event["race_only_exist"] == 1:
            race_only_key = event["race_only"]
            if race.is_race_only_key_in(race_only_key)== True:
                return f''
            else:
                race.add_race_only_key(race_only_key)
    #读取 describe 事件描述
        describe = event["describe"]
    #读取 target 目标，计算<0><1>， target_name_0 ， target_name_1
        target = event["target"]
        targets = []
        target_name_0 = race.player[horse_i].horse_fullname
        for i in range(0, len(race.player)):
            targets.append(i)
        if target == 0:
            # 0目标为自己
            targets = [horse_i]
            target_name_1 = race.player[horse_i].horse_fullname
        elif target == 1:
            # 1为随机选择一个非自己的目标（即<1>）
    #        targets.pop(horse_i)
            del targets[horse_i]
            targets = random.sample(targets, 1)
            target_name_1 = race.player[targets[0]].horse_fullname
        elif target == 2:
            # 2为全部
            target_name_1 = "所有马儿"
        elif target == 3:
            # 3为除自身外全部
    #        targets.pop(horse_i)
            del targets[horse_i]
            target_name_1 = "其他所有马儿"
        elif target == 4:
            # 4为全场随机一个目标
            targets = random.sample(targets, 1)
            target_name_1 = race.player[targets[0]].horse_fullname
        elif target == 5:
            # 5自己和一位其他目标（该目标为<1>）
    #        targets.pop(horse_i)
            del targets[horse_i]
            a = random.sample(targets, 1)
            targets = [horse_i]
            targets.extend(a)
            target_name_1 = race.player[a[0]].horse_fullname
        elif target == 6:
            # 6为随机一侧赛道的马儿（即<1>）
            a = []
            try:
                targets.index(horse_i - 1)
                a.append(horse_i - 1)
            except:
                pass
            try:
                targets.index(horse_i + 1)
                a.append(horse_i + 1)
            except:
                pass
            targets = random.sample(a, 1)
            target_name_1 = race.player[targets[0]].horse_fullname
        elif target == 7:
            # 7为两侧赛道的马儿（即<1>，此<1>为马1和马2）,赛道最边上则结束事件链
            a = []
            try:
                targets.index(horse_i - 1)
                a.append(horse_i - 1)
            except:
                return f''
            try:
                targets.index(horse_i + 1)
                a.append(horse_i + 1)
            except:
                return f''
            targets = a
            target_name_1 = f'在{race.player[horse_i].horse_fullname}两侧的马儿'
            # 其他则结束事件链
        else:
            return f''
    #判定target_is_buff
        target_is_buff = event["target_is_buff"]
        if target_is_buff != f"":
            a = []
            for i in targets:
                if race.player[i].find_buff(target_is_buff) == True:
                    a.append(i)
            targets = a
    #判定target_no_buff
        target_no_buff = event["target_no_buff"]
        if target_no_buff != f"":
            a = []
            for i in targets:
                if race.player[i].find_buff(target_no_buff) == False:
                    a.append(i)
            targets = a
    #判定结束，无目标返回空值，结束事件
        if targets == []:
            return f''
    #目标判定完毕，目标为targets，list值
        logger.info(f'执行事件: {event_name}')
        logger.info(f'target：{str(targets)}，<0>为：{target_name_0}，<1>为：{target_name_1}')
    #describe值<0><1>解读
        describe = describe.replace('<0>', target_name_0)
        describe = describe.replace('<1>', target_name_1)

    #===============以下为一次性事件===============
    #复活事件：为1则目标复活
        if event["live"] == 1:
            event_live(race, targets)
    #位移事件：目标立即进行相当于参数值的位移
        if event["move"] != 0:
            event_move(race, targets, event["move"])
    #随机位置事件：有值则让目标移动到指定位置
        if event["track_to_location_exist"] == 1:
            move_to = event["track_to_location"]
            event_track_to_location(race, targets, move_to)
    #随机位置事件：为1则让目标随机位置（位置范围为可设定值，见setting.py）
        if event["track_random_location"] == 1:
            event_track_random_location(race, targets)
    #buff持续时间调整事件：目标所有buff增加/减少回合数
        if event["buff_time_add"] != 0:
            event_buff_time_add(race, targets, event["buff_time_add"])
    #删除buff事件：下回合删除目标含特定buff_tag的所有buff
        if event["del_buff"] != f"":
            del_buffs = event["del_buff"]
            event_del_buffs(race, targets, del_buffs)
    #换位事件：值为1则与目标更换位置 （仅target为1,6时生效）
        if event["track_exchange_location"] == 1 and (target == 1 or target == 6):
            event_track_exchange_location(race, horse_i, targets[0])
    #一次性随机事件
        if event["random_event_once"] != []:
            random_event_once = event["random_event_once"]
            random_event_once_num = len(random_event_once)
            for i in targets:
                for j in range(0, random_event_once_num):
                    random_event_once_rate = random.randint(0, random_event_once[random_event_once_num - 1][0])
                    if random_event_once_rate <= random_event_once[j][0]:
                        event_once = random_event_once[j][1]
                        break
                describe += event_main(race, i, event_once, 1)
    #===============以下为永久事件===============
    #buff_tag，死亡：为1则目标死亡，此参数生成的buff默认持续999回合
    #buff_tag：die的自定义名称，不填为“死亡”
        if event["die"] == 1:
            event_die(race, targets, event["die_name"])
    #buff_tag，离开：为1则目标离开，此参数生成的buff默认持续999回合
    #buff_tag：away的自定义名称，不填为“离开”
        if event["away"] == 1:
            event_away(race, targets, event["away_name"])
    #==============================连锁事件预留位置，暂时没做

    #===============以下为buff事件===============
    #"rounds": 0,                #buff持续回合数
    #"name": "xxx",              #buff名称，turn值>0时为必要值
    #"move_max": 0,              #该buff提供马儿每回合位移值区间的最大值（move_max若小于move_min，则move_max以move_min值为准）
    #"move_min": 0,              #该buff提供马儿每回合位移值区间的最小值
    #"locate_lock": 0,           #buff_tag，止步：若为1则目标无法移动
    #"vertigo": 0,               #buff_tag，眩晕：若为1则目标无法移动，且不主动执行事件（暂定）
    #"hiding": 0,                #buff_tag，隐身：不显示目标移动距离及位置
    #"other_buff": ["buff1", "buff2", ....]
    #                            #自定义buff_tag，仅标识用buff_tag填写处，也可以填入常规buff_tag并正常生效
    #"random_event": [[概率值1, {事件}], [概率值2, {事件}], ......],
                                #此为持续性随机事件，以buff形式存在，部分详见文末
        if event["rounds"] > 0:
            rounds = event["rounds"]
            buffs = []
            buff_name = event["name"]
            move_max = event["move_max"]
            move_min = event["move_min"]
            if event["locate_lock"] == 1:
                buffs.append("locate_lock")
            if event["vertigo"] == 1:
                buffs.append("locate_lock")
                buffs.append("vertigo")
            if event["hiding"] == 1:
                buffs.append("hiding")
            if event["other_buff"] != []:
                buffs.extend(event["other_buff"])
            event_in_buff = event["random_event"]
            event_add_buff(race, targets, buff_name, rounds, buffs, move_min, move_max, event_in_buff)
    #===============以下为延迟事件===============
    #延迟事件（以当前事件的targets为发起人的事件）：前者为多少回合后，需>1
        delay_event = event["delay_event"]
        if delay_event != []:
            event_delay_rounds = delay_event[0]
            if event_delay_rounds > 1:
                event_delay = delay_event[1]
                for i in targets:
                    race.player[i].delay_events.append([race.round + event_delay_rounds, event_delay])
    #延迟事件（以当前事件发起人为发起人的事件）：前者为多少回合后，需>1
        delay_event_self = event["delay_event_self"]
        if delay_event_self != []:
            event_delay_rounds_self = delay_event_self[0]
            if event_delay_rounds_self > 1:
                event_delay_self = delay_event_self[1]
                race.player[horse_i].delay_events.append([race.round + event_delay_rounds_self, event_delay_self])

    #===============以下同步事件===============
    #同步事件（以当前事件的targets为发起人的事件），执行此事件后立马执行该事件
        another_event = event["another_event"]
        if another_event != {}:
            for i in targets:
                describe += event_main(race, i, another_event, 1)
    #同步事件（以当前事件发起人为发起人的事件），执行此事件后立马执行该事件
        another_event_self = event["another_event_self"]
        if another_event_self != {}:
            describe += event_main(race, horse_i, another_event_self, 1)
    #==========永久事件2，换赛道/加马==========
    #增加一匹马事件
        if event["add_horse"] != {}:
            add_horse_event = event["add_horse"]
            add_horse_name = add_horse_event["horsename"]
            add_horse_id = add_horse_event["owner"]
            try:
                add_horse_uid = add_horse_event["uid"]
            except KeyError:
                add_horse_uid = 0
            try:
                add_horse_location = add_horse_event["location"]
            except KeyError:
                add_horse_location = 0
            logger.info(f'创建马{add_horse_name},{str(add_horse_uid)}, {add_horse_id}')
            race.add_player(add_horse_name, add_horse_uid, add_horse_id, add_horse_location, race.round)
    #替换一匹马事件
        replace_event = event["replace_horse"]
        if replace_event != {}:
            if target == 0 or target == 1 or target == 4 or target == 6:
                try:
                    replace_name = replace_event["horsename"]
                except KeyError:
                    replace_name = race.player[targets[0]].horse
                try:
                    replace_id = replace_event["owner"]
                except KeyError:
                    replace_id = race.player[targets[0]].player
                try:
                    replace_uid = replace_event["uid"]
                except KeyError:
                    replace_uid = race.player[targets[0]].playeruid
                logger.info(f'替换事件{replace_name}, {str(replace_uid)}, {replace_id}')
                race.player[targets[0]].replace_horse_ex(replace_name, replace_uid, replace_id)
        return describe
    except:
        logger.info(f"事件名 {event_name} 执行故障")
        return f"事件名 {event_name} 执行故障"
#===============子函数区===============
#复活对象
def event_live(race, targets):
    for i in targets:
        if race.player[i].find_buff("die") == True:
            race.player[i].del_buff("die")
        logger.info(f'{race.player[i].horse} 复活了')

#位移对象
def event_move(race, targets, move):
    for i in targets:
        race.player[i].location_move_event(move)
        logger.info(f'{race.player[i].horse} 移动了{str(move)}')

#移动对象至特定位置
def event_track_to_location(race, targets, move_to):
    for i in targets:
        race.player[i].location_move_to_event(move_to)
        logger.info(f'{race.player[i].horse} 移动到了指定位置{str(move_to)}')

#移动对象至随机位置
def event_track_random_location(race, targets):
    for i in targets:
        move_to = random.randint(setting_random_min_length, setting_random_max_length)
        race.player[i].location_move_to_event(move_to)
        logger.info(f'{race.player[i].horse} 移动到了随机位置{str(move_to)}')

#buff持续时间变更
def event_buff_time_add(race, targets, time_add):
    for i in targets:
        race.player[i].buff_addtime(time_add)
        logger.info(f'{race.player[i].horse} 的buff事件增加了{str(time_add)}')

#移除buff
def event_del_buffs(race, targets, del_buffs):
    for i in targets:
        for j in del_buffs:
            race.player[i].del_buff(j)
            logger.info(f'{race.player[i].horse} 移除了buff：{j}')
#马儿互换位置
def event_track_exchange_location(race, a, b):
    x = race.player[a].location
    race.player[a].location_move_to_event(race.player[b].location)
    race.player[b].location_move_to_event(x)
    logger.info(f'{race.player[a].horse} 和{race.player[b].horse}互换位置')


#死亡事件
def event_die(race, targets, buff_name):
    for i in targets:
        if race.player[i].find_buff("die") == False:
            race.player[i].add_buff(buff_name, race.round + 1, 9999, ["die"])
            logger.info(f'死亡事件判定 {race.player[i].horse} 死了')

#离开事件
def event_away(race, targets, buff_name):
    for i in targets:
        if race.player[i].find_buff("away") == False:
            race.player[i].add_buff(buff_name, race.round + 1, 9999, ["away"])
        logger.info(f'{race.player[i].horse} 离开')

#增加buff事件
def event_add_buff(race, targets, buff_name, rounds, buffs, move_min, move_max, event_in_buff):
    for i in targets:
        if race.player[i].find_buff(buff_name) == False:
            logger.info(f'{race.player[i].horse} 增加了 buff: {buff_name}, 第{str(race.round + 1)}~{str(race.round + rounds)}回合')
        else:
            race.player[i].del_buff(buff_name)
        race.player[i].add_buff(buff_name, race.round + 1, race.round + rounds, buffs, move_min, move_max, event_in_buff)
