import random
from .setting import  *

class horse:
    def __init__(self, horsename = "the_horse", uid = 0, id = "the_player", location = 0, round = 0 ):
        self.horse = horsename
        self.playeruid = uid
        self.player =  id
        self.buff = []
        self.delay_events = []
        self.horse_fullname = horsename
        self.round = round
        self.location = location
        self.location_add = 0
        self.location_add_move = 0
# =====替换为其他马,指定马（没用上，暂留）
    def replace_horse(self, horse_to):
        self.horse = horse_to.horse
        self.playeruid = horse_to.playeruid
        self.player = horse_to.player
        self.buff = horse_to.buff
        self.delay_events = horse_to.delay_events
        self.horse_fullname = horse_to.horse_fullname
        self.round = horse_to.round
        self.location = horse_to.location
        self.location_add = horse_to.location_add
        self.location_add_move = horse_to.location_add_move
#=====替换为其他马,指定数据（用于天灾马系列事件）
    def replace_horse_ex(self, horsename = "the_horse", uid = 0, id= "the_player"):
        self.horse = horsename
        self.playeruid = uid
        self.player =  id
        self.buff = []
        self.delay_events = []
        self.horse_fullname = horsename
        self.round = round
        self.location = location
        self.location_add = 0
        self.location_add_move = 0
#=====马儿buff增加：buff为list格式
    def add_buff(self, buff_name, round_start, round_end, buffs, move_min = 0, move_max = 0, event_in_buff = []):
        if  move_min > move_max:
            move_max = move_min
        buff = [buff_name, round_start, round_end, move_min, move_max, event_in_buff]
        buff.extend(buffs)
        self.buff.append(buff)
#=====马儿指定buff移除：
    def del_buff(self, del_buff_key):
        for i in range(0, len(self.buff)):
            try:
                self.buff[i].index(del_buff_key, 6)
                self.buff[i][2] = self.round
            except ValueError:
                pass
#=====马儿查找有无buff（查参数非名称）：(跳过计算回合数，只查有没有）
    def find_buff(self, find_buff_key):
        for i in range(0, len(self.buff)):
            try:
                self.buff[i].index(find_buff_key, 6)
                return True
            except ValueError:
                pass
        return False
#=====马儿超时buff移除：
    def del_buff_overtime(self, round):
        for i in range(len(self.buff) - 1, -1, -1):
            if self.buff[i][2] < round:
                del self.buff[i]
#=====马儿buff时间延长/减少：
    def buff_addtime(self, round_add):
        for i in range(0, len(self.buff)):
            self.buff[i][2] += round_add
#=====马儿是否止步：
    def is_stop(self) -> bool:
        for i in range(0, len(self.buff)):
            try:
                self.buff[i].index("locate_lock", 6)
                if self.buff[i][1] <= self.round:
                    return True
            except ValueError:
                pass
        return False
#=====马儿是否已经离开：
    def is_away(self) -> bool:
        for i in range(0, len(self.buff)):
            try:
                self.buff[i].index("away", 5)
                if self.buff[i][1] <= self.round:
                    return True 
            except ValueError:
                pass
        return False
#=====马儿是否已经死亡：
    def is_die(self) -> bool:
        for i in range(0, len(self.buff)):
            try:
                self.buff[i].index("die", 5)
                if self.buff[i][1] <= self.round:
                    return True
            except ValueError:
                pass
        return False
#=====马儿全名带buff显示：
    def fullname(self):
        fullname = f""
        for i in range(0, len(self.buff)):
            if self.buff[i][1] <= self.round:
                fullname += ( "<" + self.buff[i][0] + ">" )
        self.horse_fullname = fullname + self.horse
#=====马儿移动计算（事件提供的本回合移动）：
    def location_move_event(self, move):
        self.location_add_move += move
#=====马儿移动至特定位置计算（事件提供移动）：
    def location_move_to_event(self, move_to):
        self.location_add_move += move_to - self.location
#=====马儿移动计算：
    def location_move(self):
        if self.location != setting_track_length:
            self.location_add = self.move() + self.location_add_move
            self.location += self.location_add
            if self.location > setting_track_length:
                self.location_add -= self.location - setting_track_length
                self.location = setting_track_length
            if self.location < 0:
                self.location_add -= self.location
                self.location = 0
#=====马儿移动量计算：
    def move(self):
        if self.is_stop() == True:
            return 0
        if self.is_die() == True:
            return 0
        if self.is_away() == True:
            return 0
        move_min = 0
        move_max = 0
        for i in range(0, len(self.buff)):
            if self.buff[i][1] <= self.round:
                move_min += self.buff[i][3]
                move_max += self.buff[i][4]
        return random.randint(move_min + base_move_min, move_max + base_move_max)
#=====赛马玩家战况显示： 
    def display(self):
        display = f""
        if self.find_buff("hiding") == False:
            if self.location_add < 0:
                display += "[" + str(self.location_add) + "]"
            else:
                display += "[+" + str(self.location_add) + "]"
            for i in range(0, setting_track_length - self.location):
                display += "."
            display += self.horse_fullname
            for i in range(setting_track_length - self.location, setting_track_length):
                display += "."
        else:
            display += "[+？]"
            for i in range(0, setting_track_length):
                display += "."
        display += "\n"
        return display

