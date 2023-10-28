from typing import List
import random
import math

from .horse import horse
from .events_main import event_main

from ..config import setting_track_length, event_rate

class race_group():
    def __init__(self):
        """
        初始化
        """
        self.player:List[horse] = []
        self.round = 0
        self.start = 0 # start指示器：0为马儿进场未开始，1为开始，2为暂停（测试用）
        self.race_only_keys = []

    def add_player(self, horsename = "the_horse", uid = 0, id = "the_player",location = 0, round = 0):
        """
        增加赛马位
        """
        self.player.append(horse(horsename, uid, id, location, round))

    def query_of_player(self):
        """
        赛马位数量查看
        """
        return len(self.player)

    def is_player_in(self, uid):
        """
        查找有无玩家
        """
        for i in range(0, len(self.player)):
            if self.player[i].playeruid == uid:
                return True
        return False

    def round_add(self):
        """
        回合开始，回合数+1
        """
        self.round += 1
        for i in range(0, len(self.player)):
            self.player[i].round = self.round
            self.player[i].location_add_move = 0

    def del_buff_overtime(self):
        """
        所有马儿移除多余buff
        """
        for i in range(0, len(self.player)):
            self.player[i].del_buff_overtime(self.round)

    def fullname(self):
        """
        所有马儿buff+名称计算
        """
        for i in range(0, len(self.player)):
            self.player[i].fullname()

    def move(self):
        """
        所有马儿移动，移动计算已包含死亡/离开/止步判定
        """
        for i in range(0, len(self.player)):
            self.player[i].location_move()

    def display(self):
        """
        所有马儿数据显示（须先移动)
        """
        return [player.display() for player in self.player]

    def is_die_all(self) -> bool:
        """
        所有马儿是否死亡/离开
        """
        for i in range(0, len(self.player)):
            if ( self.player[i].is_die() == False ) and ( self.player[i].is_away() == False ):
                return False
        return True

    def is_win_all(self):
        """
        所有马儿是否到终点
        """
        win_name = []
        for i in range(0, len(self.player)):
            if self.player[i].location >= setting_track_length:
                win_name.append([self.player[i].player,self.player[i].playeruid])

        return win_name

    def event_start(self, events_list):
        """
        事件触发
        """
        event_display = ""
        # 延时事件触发：
        for i in range(0, len(self.player)):
            if len(self.player[i].delay_events) > 0:
                for j in range(len(self.player[i].delay_events)-1, -1, -1):
                    if self.player[i].delay_events[j][0] == self.round:
                        display_0 = event_main(self, i, self.player[i].delay_events[j][1], 1) + "\n"
                        if display_0 != "\n":
                            event_display += display_0
                        del self.player[i].delay_events[j]
        # buff随机事件触发
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
                        # 随机事件判定：
        events_num = len(events_list)
        for i in range(0, len(self.player)):
            event_id = random.randint(0, math.ceil(1000 * events_num / event_rate) - 1)
            if event_id < events_num:
                event = events_list[event_id]
                display_0 = event_main(self, i, event) + "\n"
                if display_0 != "\n":
                    event_display += display_0
        return event_display

    def is_race_only_key_in(self, key):
        """
        事件唯一码查询
        """
        try:
            self.race_only_keys.index(key)
            return True
        except ValueError:
            return False

    def add_race_only_key(self, key):
        """
        事件唯一码增加
        """
        self.race_only_keys.append(key)