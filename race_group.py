import random
import math
import time
from .horse import horse
from .events_main import event_main
from .setting import  *

class race_group:
#初始化
    def __init__(self):
        self.player = []
        self.round = 0
        self.start = 0
        self.time = time.time()
        self.race_only_keys = []
#start指示器变更 0为马儿进场未开始，1为开始，2为暂停（测试用）
    def start_change(self, key):
        self.start = key
#增加赛马位
    def add_player(self, horsename = "the_horse", uid = 0, id = "the_player",location = 0, round = 0):
        self.player.append(horse(horsename, uid, id, location, round))
#赛马位数量查看
    def query_of_player(self):
        return len(self.player)
#查找有无玩家
    def is_player_in(self, uid):
        for i in range(0, len(self.player)):
            if self.player[i].playeruid == uid:
                return True
        return False
#回合开始，回合数+1
    def round_add(self):
        self.round += 1
        for i in range(0, len(self.player)):
            self.player[i].round = self.round
            self.player[i].location_add_move = 0
#所有马儿移除多余buff
    def del_buff_overtime(self):
        for i in range(0, len(self.player)):
            self.player[i].del_buff_overtime(self.round)
#所有马儿buff+名称计算
    def fullname(self):
        for i in range(0, len(self.player)):
            self.player[i].fullname()
#所有马儿移动，移动计算已包含死亡/离开/止步判定
    def move(self):
        for i in range(0, len(self.player)):
            self.player[i].location_move()
#所有马儿数据显示（须先移动)
    def display(self):
        display = ""
        for i in range(0, len(self.player)):
            display += self.player[i].display()
        return display
#所有马儿是否死亡/离开
    def is_die_all(self) -> bool:
        for i in range(0, len(self.player)):
            if ( self.player[i].is_die() == False ) and ( self.player[i].is_away() == False ):
                return False
        return True
#所有马儿是否到终点
    def is_win_all(self):
        win_name = []
        for i in range(0, len(self.player)):
            if self.player[i].location >= setting_track_length:
                win_name.append([self.player[i].player,self.player[i].playeruid])

        return win_name
#事件触发
    def event_start(self, events_list):
        event_display = f""
        #延时事件触发：
        for i in range(0, len(self.player)):
            if len(self.player[i].delay_events) > 0:
                for j in range(len(self.player[i].delay_events)-1, -1, -1):
                    if self.player[i].delay_events[j][0] == self.round:
                        display_0 = event_main(self, i, self.player[i].delay_events[j][1], 1) + "\n"
                        if display_0 != "\n":
                            event_display += display_0
                        del self.player[i].delay_events[j]
        #buff随机事件触发
        for i in range(0, len(self.player)):
            for j in range(0, len(self.player[i].buff)):
                if self.player[i].buff[j][5] != []:
                    event_in_buff = self.player[i].buff[j][5]
                    event_in_buff_num = len(event_in_buff)
                    event_in_buff_rate = random.randint(0, event_in_buff[event_in_buff_num - 1][0])
                    for k in range(0, event_in_buff_num):
                        if event_in_buff_rate <= event_in_buff[k][0]:
                            event_in_buff_x = event_in_buff[k][1]
                            break
                    display_0 = event_main(self, i, event_in_buff_x, 1) + "\n"
                    if display_0 != "\n":
                        event_display += display_0
                        #随机事件判定：
        events_num = len(events_list)
        for i in range(0, len(self.player)):
            event_id = random.randint(0, math.ceil(1000 * events_num / event_rate) - 1)
            if event_id < events_num:
                event = events_list[event_id]
                display_0 = event_main(self, i, event) + "\n"
                if display_0 != "\n":
                    event_display += display_0
        return event_display
#事件唯一码查询
    def is_race_only_key_in(self, key):
        try:
            self.race_only_keys.index(key)
            return True
        except ValueError:
            return False
#事件唯一码增加
    def add_race_only_key(self, key):
        self.race_only_keys.append(key)