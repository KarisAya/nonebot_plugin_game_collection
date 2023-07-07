from typing import Dict,List
from pydantic import BaseModel
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import math
import random
try:
    import ujson as json
except ModuleNotFoundError:
    import json
from collections import Counter
from ..data import GroupAccount
from ..config import fontname
"""
ATK:对士兵攻击力
ATK_T:对建筑攻击力
DEF:对建筑防御值提升
"""

font = ImageFont.truetype(font = fontname, size = 30, encoding = "utf-8")
font_small = ImageFont.truetype(font = fontname, size = 22, encoding = "utf-8")

class Castle(BaseModel):
    """
    城池属性
    """
    HP:int = 10
    user_id:int = None
    army:Dict[int,int] = {}
    tower_L:int = 0
    tower_R:int = 0
    line_L:int = 0
    line_R:int = 0
    attack:Dict[int,int] = {}
    soldier = {
        1:{"name":"兵","ATK":1,"ATK_T":1},
        2:{"name":"超","ATK":5,"ATK_T":5},
        3:{"name":"卫","ATK":1,"ATK_T":1},
        4:{"name":"爆","ATK":1,"ATK_T":5},
        }

    cards_table:list = (
        ["超级兵*1"]*5 +
        ["兵*3"]*10 +
        ["兵*2"]*8 +
        ["兵*1"]*18 +
        ["核心血量+5"]*2 +
        ["防线*1（防御力+1）"]*3 +
        ["塔*1（塔血+2）"]*3 +
        ["兵力*2"]*1 +
        ["卫兵*1"]*2 +
        ["爆破兵*1"]*2)

    def turntable (self):
        result = random.choices(self.cards_table,k = 4)
        for x in result:
            if x == "超级兵*1":
                self.army[2] = self.army.get(2,0) + 1
            elif x == "兵*3":
                self.army[1] = self.army.get(1,0) + 3
            elif x == "兵*2":
                self.army[1] = self.army.get(1,0) + 2
            elif x == "兵*1":
                self.army[1] = self.army.get(1,0) + 1
            elif x == "核心血量+5":
                self.HP += 5
            elif x == "防线*1（防御力+1）":
                if self.line_L == 0:
                    self.line_L = 10
                elif self.line_R == 0:
                    self.line_R = 10
                else:
                    if random.randint(0,1) == 0:
                        self.line_L += 1
                    else:
                        self.line_R += 1
            elif x == "塔*1（塔血+2）":
                if self.tower_L == 0:
                    self.tower_L = 5
                elif self.tower_R == 0:
                    self.tower_R = 5
                else:
                    if random.randint(0,1) == 0:
                        self.tower_L += 2
                    else:
                        self.tower_R += 2
            elif x == "兵力*2":
                self.army = {k:v*2 for k,v in self.army.items()}
            elif x == "卫兵*1":
                self.army[3] = self.army.get(3,0) + 1
            elif x == "爆破兵*1":
                self.army[4] = self.army.get(4,0) + 1

        return "\n".join(result)

class Player(BaseModel):
    """
    玩家属性
    """
    group_account:GroupAccount = None
    team:str = None
    color:str = None
    castle_ids:list = []

class World(BaseModel):
    """
    世界属性
    """
    start:int = 0
    castles:Dict[int,Castle] = {}
    players:Dict[int,Player] = {}
    ids = []
    teams:list = []
    team_color:list = ["#cc0000","#351c75","#e69138","#0b5394","#f1c232","#1155cc","#6aa84f","#134f5c","#45818e","#38761d","#3c78d8","#bf9000","#3d85c6","#b45f06"]
    act = 0
    round = 0
    attack:tuple = ()
    event:dict = None
    def draw(self):
        """
        绘制地图
        """
        # 创建画布
        width, height = 880, 880
        image = Image.new("RGB", (width, height), "#FFFFFF")
        draw = ImageDraw.Draw(image)
        # 圆心坐标和半径
        center_x, center_y = width // 2, height // 2
        radius = 280
        # 协约线
        if self.round < 5:
            inner_outline = "black"
        else:
            inner_outline = "#CCCCCC"

        draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius),outline = inner_outline ,width = 4)

        radius = 380
        # 计算每个等分的角度
        num_slices = 28
        angle_per_slice = 360 / num_slices
        coordinate = {}
        for index,i in enumerate(range(0,num_slices,2)):
            angle = math.radians((i - 0.7) * angle_per_slice - 90)
            cos = math.cos(angle)
            sin = math.sin(angle)
            x1 = center_x + radius * cos
            y1 = center_y + radius * sin
            xL_T = center_x + (radius - 100) * cos
            yL_T = center_y + (radius - 100) * sin
            angle = math.radians((i + 0.7) * angle_per_slice - 90)
            cos = math.cos(angle)
            sin = math.sin(angle)
            x4 = center_x + radius * cos
            y4 = center_y + radius * sin
            xR_T = center_x + (radius - 100) * cos
            yR_T = center_y + (radius - 100) * sin
            angle = math.radians(i* angle_per_slice - 90)
            cos = math.cos(angle)
            sin = math.sin(angle)
            x2 = x1 + 40 * cos
            y2 = y1 + 40 * sin
            x3 = x4 + 40 * cos
            y3 = y4 + 40 * sin

            index += 1
            castle = self.castles.get(index)
            if castle and (user_id := castle.user_id):
                color = self.players[user_id].color
                color_TL = color if castle.tower_L > 1 else "#CCCCCC"
                color_TR = color if castle.tower_R > 1 else "#CCCCCC"
                color_LL = color if castle.line_L > 1 else "#CCCCCC"
                color_LR = color if castle.line_R > 1 else "#CCCCCC"
            else:
                color = "#CCCCCC"
                color_TL = "#CCCCCC"
                color_TR = "#CCCCCC"
                color_LL = "#CCCCCC"
                color_LR = "#CCCCCC"

            draw.polygon([(x1,y1),(x2,y2),(x3,y3),(x4,y4)],outline = "gray",width = 1,fill = color)
            draw.line([(x1,y1),(xL_T,yL_T)],width = 1,fill = color_LL)
            draw.line([(x4,y4),(xR_T,yR_T)],width = 1,fill = color_LR)
            draw.ellipse((xL_T - 10, yL_T - 10, xL_T + 10, yL_T + 10),outline = "gray",fill = color_TL)
            draw.ellipse((xR_T - 10, yR_T - 10, xR_T + 10, yR_T + 10),outline = "gray",fill = color_TR)

            if castle:
                inner_x = center_x + (radius - 140) * cos
                inner_y = center_x + (radius - 140) * sin
                coordinate[index] = (inner_x,inner_y)
                index = str(index)
                inner_x -= font.getlength(index)//2
                inner_y -= font.size//2
                draw.text((inner_x,inner_y),index,fill = "black",font = font)
                HP = str(castle.HP + 10*castle.army.get(3,0))
                inner_x = center_x + (radius + 15) * cos
                inner_y = center_x + (radius + 15) * sin
                inner_x -= font.getlength(HP)//2
                inner_y -= font.size//2
                draw.text((inner_x,inner_y),HP,fill = "white",font = font)

                tmp = []
                inner_maxx = 0
                inner_maxy = 0
                for k in range(1,5):
                    if v:= castle.army.get(k):
                        msg = f"{castle.soldier[k]['name']}{v}"
                        inner_maxx = max(font_small.getlength(msg),inner_maxx)
                        inner_maxy += font_small.size + 2
                        tmp.append(msg)

                inner_x = center_x + (radius - 50) * cos - inner_maxx//2
                inner_y = center_x + (radius - 50) * sin - inner_maxy//2
                for x in tmp:
                    draw.text((inner_x,inner_y),x,fill = "red",font = font_small)
                    inner_y += font_small.size + 2

                if castle.tower_L > 1:
                    tower_L = str(castle.tower_L)
                    inner_x = xL_T - font_small.getlength(tower_L)//2
                    inner_y = yL_T - 11
                    draw.text((inner_x,inner_y),tower_L,fill = "white",font = font_small)
                if castle.tower_R > 1:
                    tower_R = str(castle.tower_R)
                    inner_x = xR_T - font_small.getlength(tower_R)//2
                    inner_y = yR_T - 11
                    draw.text((inner_x,inner_y),tower_R,fill = "white",font = font_small)
                if castle.line_L > 1:
                    line_L = str(castle.line_L)
                    inner_x = ((x1 + xL_T) - font_small.getlength(line_L))//2
                    inner_y = ((y1 + yL_T) - font_small.size)//2
                    draw.text((inner_x,inner_y),line_L,fill = color,font = font_small)
                if castle.line_R > 1:
                    line_R = str(castle.line_R)
                    inner_x = ((x4 + xR_T) - font_small.getlength(line_R))//2
                    inner_y = ((y4 + yR_T) - font_small.size)//2
                    draw.text((inner_x,inner_y),line_R,fill = color,font = font_small)

        if self.attack:
            ATK = self.attack[0]
            color = self.players[self.castles[ATK].user_id].color
            DEF = self.attack[1]
            draw.line((coordinate[ATK],coordinate[DEF]),width = 2,fill = color)

        output = BytesIO()
        image.save(output, format = "png")
        return output

    def add_player(self,group_account:GroupAccount,index:int,team:str):
        """
        增加玩家
        """
        if team not in self.teams:
            self.teams.append(team)
        user_id = group_account.user_id
        self.players[user_id] = Player(
            group_account = group_account,
            team = team,
            color = self.team_color[self.teams.index(team)],
            castle_ids = [index]
            )
        self.ids.append(user_id)
        self.castles[index] = Castle(user_id = user_id)