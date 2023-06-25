from typing import Tuple,Dict,List
from pathlib import Path
from io import BytesIO
from PIL import Image,ImageDraw,ImageFont
from PIL.Image import Image as IMG
from fontTools.ttLib import TTFont

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np

import re

from .avatar import download_avatar,download_groupavatar

from ..data import UserDict, GroupAccount
from ..data import resourcefile

from ..config import BG_image,fontname,fallback_fonts

sns.set(font = fontname)

default_BG = BG_image / "default.png"

if not default_BG.exists():
    Image.new('RGB', (200, 200), (0, 51, 102)).save(default_BG)

font_big = ImageFont.truetype(font = fontname, size = 60, encoding = "utf-8")
font_normal = ImageFont.truetype(font = fontname, size = 40, encoding = "utf-8")
font_small = ImageFont.truetype(font = fontname, size = 30, encoding = "utf-8")

cmap_default = TTFont(font_big.path, fontNumber = font_big.index).getBestCmap()

global fallback_fonts_cmap
fallback_fonts_cmap = {}
for fallback in fallback_fonts:
    fallback_path = fm.findfont(fm.FontProperties(family=fallback))
    fallback_fonts_cmap[fallback_path] = TTFont(fallback_path, fontNumber = 0).getBestCmap()

def linecard_to_png(
    text:str,
    font_size = 60,
    width:int = None,
    height:int = None,
    padding:tuple = (20,20),
    spacing:float = 1.2,
    bg_color = "white",
    autowrap:bool = False,
    endline = None
    ):
    '''
    文字转png
    '''
    output = BytesIO()
    linecard(
        text = text,
        font_size = font_size,
        width = width,
        height = height,
        padding = padding,
        spacing = spacing,
        bg_color = bg_color,
        endline = endline).save(output, format = "png")
    return output

class linecard_pattern:
    align = re.compile(r"\[left\]|\[right\]|\[center\]|\[pixel\]\[.*?\]")
    font = re.compile(r"\[font_big\]|\[font_normal\]|\[font_small\]|\[font\]\[.*?\]\[.*?\]")
    color = re.compile(r"\[color\]\[.*?\]")
    passport = re.compile(r"\[passport\]")
    nowrap = re.compile(r"\[nowrap\]")
    noautowrap = re.compile(r"\[noautowrap\]")

def remove_tag(string, pattern):
    match = pattern.search(string)
    if match:
        start = match.start()
        end = match.end()
        return string[:start] + string[end:],string[start:end]
    else:
        return None

def line_wrap(line:str,width:int,font, start:int = 0):
    text_x = start
    line_count = 1
    new_str = ""
    for char in line:
        text_x += font.getlength(char)
        if text_x > width:
            new_str += "\n" + char
            text_x = 0
            line_count += 1 
        else:
            new_str += char
    return new_str,line_count

def linecard(
    text:str,
    font_size:int = None,
    width:int = None,
    height:int = None,
    padding:tuple = (20,20),
    spacing:float = 1.2,
    bg_color:str = None,
    autowrap:bool = False,
    endline = None,
    canvas = None
    ):
    '''
    指定宽度单行文字
        ----:横线

        [left]靠左
        [right]靠右
        [center]居中
        [pixel][400]指定像素

        [font_big]大字体
        [font_normal]正常字体
        [font_small]小字体
        [font][font_name][font_size]指定字体

        [color][#000000]指定本行颜色

        [nowrap]不换行
        [noautowrap]不自动换行
        [passport]保持标记
    '''
    text = text.replace("\r\n","\n")
    lines = text.split('\n')

    if font_size:
        font_default = ImageFont.truetype(font = fontname, size = font_size, encoding = "utf-8")
    else:
        font_default = font_normal

    cmap_default = TTFont(font_default.path, fontNumber = font_default.index).getBestCmap()

    padding_x = padding[0]
    padding_y = padding[1]

    X = []
    Y = [0,]
    Text = []

    text_y = 0
    maxFontLine = 0 # 如果本行是通过[nowrap]不换行标记拼接的多个行，那么记录最大的字体宽度以在换行时使用最大的字体

    align = "left"
    font = font_default
    cmap = cmap_default
    color = None
    passport = 0
    noautowrap = True

    for line in lines:
        passport -= 1

        if res := remove_tag(line,linecard_pattern.align):
            line, align = res
            if align.startswith("[pixel]["):
                align = align[8:-1]
            else:
                align = align[1:-1]
        else:
            if passport == 1:
                pass
            else:
                align = "left"

        if res := remove_tag(line,linecard_pattern.font):
            line, font = res
            if font.startswith("[font]["):
                font = font[7:-1]
                inner_font_name,inner_font_size = font.split("][",1)
                inner_font_size = int(inner_font_size)
                inner_font_size = inner_font_size if inner_font_size else font_size
                try:
                    font = ImageFont.truetype(font = inner_font_name, size = inner_font_size, encoding = "utf-8")
                    cmap = TTFont(font.path, fontNumber = font.index).getBestCmap()
                except OSError:
                    font, cmap = font_default, cmap_default
            elif font == "[font_big]":
                font, cmap = font_big, cmap_default
            elif font == "[font_normal]":
                font, cmap = font_normal, cmap_default
            elif font == "[font_small]":
                font, cmap = font_small, cmap_default
            else:
                font, cmap = font_default, cmap_default
        else:
            if passport == 1:
                pass
            else:
                font, cmap = font_default, cmap_default

        if res := remove_tag(line,linecard_pattern.color):
            line, color = res
            color = color[8:-1]
        else:
            if passport == 1:
                pass
            else:
                color = None

        if res := remove_tag(line,linecard_pattern.noautowrap):
            line = res[0]
            noautowrap = True
        else:
            if passport == 1:
                pass
            else:
                noautowrap = False

        if res := remove_tag(line,linecard_pattern.nowrap):
            line = res[0]
            maxFontLine = max(maxFontLine,int(font.size * spacing))
        else:
            if autowrap and not noautowrap and width and font.getlength(line) > width:
                line,inner_line_count = line_wrap(line,width - padding_x,font)
                text_y += max(maxFontLine,inner_line_count * int(font.size * spacing))
            else:
                text_y += max(maxFontLine,int(font.size * spacing))
            maxFontLine = 0

        if res := remove_tag(line,linecard_pattern.passport):
            line = res[0]
            passport = 2

        X.append(int(font.getlength(line)))
        Y.append(text_y)
        Text.append([line, font, cmap, color, align])
    
    width = width if width else (max(X) + padding_x*2)
    height = height if height else (Y[-1] + padding_y*2)

    Text_XY = []
    for i, (line, font, cmap, color, align) in enumerate(Text):
        if align == "right":
            text_x = int(width - font.getlength(line) - padding_x)
        elif align == "center":
            text_x = (width - font.getlength(line) )//2
        elif align.isdigit():
            text_x = int(align)
        else:
            if Y[i] == Y[i-1]:
                inner_x = X[i-1]
                X[i] += X[i-1]
            else:
                inner_x = 0
            text_x = inner_x + padding_x

        text_y = Y[i] + padding_y

        # 这一行的起始位置
        Text_XY.append([None,None,None,text_x,text_y])
        new_line = ""
        inner_index = 0
        inner_iterations = len(line)
        flag = False
        while inner_index < inner_iterations:
            char = line[inner_index]
            ordchar = ord(char)
            if ordchar in cmap:
                new_line += char
            else:
                flag = True
                if new_line:
                    Text_XY[-1][0] = new_line
                    Text_XY[-1][1] = font
                    Text_XY[-1][2] = color
                    Text_XY.append([None,None,None,int(Text_XY[-1][3] + font.getlength(new_line)),text_y])
                for inner_font in fallback_fonts_cmap:
                    if ordchar in fallback_fonts_cmap[inner_font]:
                        inner_fallback_font = ImageFont.truetype(font = inner_font, size = font.size, encoding="utf-8")
                        break
                else:
                    char = "□"
                    inner_fallback_font = font

                Text_XY[-1][0] = char
                Text_XY[-1][1] = inner_fallback_font
                Text_XY[-1][2] = color
                Text_XY.append([None,None,None,int(Text_XY[-1][3] + inner_fallback_font.getlength(char)),text_y])
                new_line = ""
            inner_index += 1
        if new_line:
            Text_XY[-1][0] = new_line
            Text_XY[-1][1] = font
            Text_XY[-1][2] = color
        else:
            del Text_XY[-1]
        if flag:
            X[i] = Text_XY[-1][3]

    canvas = canvas if canvas else Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(canvas)

    for i,(line,font,color,text_x,text_y)in enumerate(Text_XY):
        if line == "----":
            color = color if color else 'gray'
            tmp = text_y + font.size//2
            draw.line(((0, tmp), (width, tmp)), fill = color, width = 4)
        else:
            color = color if color else 'black'
            draw.text((text_x, text_y),line, fill = color, font = font)

    if endline:
        draw.line(((0, height - 60), (width, height - 60)), fill = "gray", width = 4)
        text_x = int(width - font_small.getlength(endline) - 20)
        draw.text((text_x,height - 45),endline, fill = "gray", font = font_small)

    return canvas

def gacha_info0(report:IMG, info:List[IMG]):
    """
    抽卡信息拼接
        report:抽卡报告
        info:信息图片列表
    """
    x = 880
    y = report.size[1] + 10
    length = len(info)
    if length%2 == 1:
        info.append(None)
        length += 1

    canvas = Image.new("RGB", (880,(130*length)//2 + report.size[1]), '#99CCFF')
    canvas.paste(report)
    for i in range(0, length, 2):
        l,r = info[i:i+2]
        canvas.paste(l, (0, y))
        if r:
            canvas.paste(r, (442, y))
        y += 130
    output = BytesIO()
    canvas.save(output,'png')
    return output
    
async def bar_chart(user_id:int, info:str, lenth:float):
    """
    带头像的条形图
    """
    canvas = Image.new("RGBA", (880, 60))
    avatar = Image.open(await download_avatar(user_id))
    avatar = avatar.resize((60,60))
    circle_mask = Image.new("RGBA", avatar.size, (255, 255, 255, 0))
    ImageDraw.Draw(circle_mask).ellipse(((0,0),avatar.size), fill="black")
    canvas.paste(avatar, (5, 0), circle_mask)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(((70,10), (860, 50)), fill = "#00000033")
    draw.rectangle(((70,10), (80 + int(lenth*780), 50)), fill = "#99CCFF")
    draw.text((80,10), info, fill = (0,0,0), font = font_normal)
    return canvas

async def my_info_head(user:UserDict, nickname:str):
    """
    我的资料卡第一个信息
    """
    gold = user.gold
    win = user.win
    lose = user.lose
    canvas = Image.new("RGBA", (880, 300))
    avatar = Image.open(await download_avatar(user.user_id))
    avatar = avatar.resize((250,250))
    circle_mask = Image.new("RGBA", avatar.size, (255, 255, 255, 0))
    ImageDraw.Draw(circle_mask).ellipse(((0,0),avatar.size), fill="black")
    canvas.paste(avatar, (25, 25), circle_mask)
    draw = ImageDraw.Draw(canvas)
    draw.text((300,40),f"{nickname}", fill = (0,0,0),font = font_big)
    draw.line(((300, 120), (860, 120)), fill = "gray", width = 4)
    draw.text((300,140),f"金币 {'{:,}'.format(gold)}", fill = (0,0,0),font = font_normal)
    draw.text((300,190),f"战绩 {win}:{lose}", fill = (0,0,0),font = font_normal)
    draw.text((300,240),f"胜率 {(round(win * 100 / (win + lose), 2) if win > 0 else 0)}%\n", fill=(0,0,0),font = font_normal)
    return canvas

def my_info_statistics(dist):
    """
    我的资料卡跨群资产统计图
    """
    dist.sort(key=lambda x:x[0],reverse=True)
    N = len(dist)
    labels = []
    x = []
    for i in range(N):
        seg = dist[i]
        if i == 5:
            y = 0
            for j in range(i,N):
                seg = dist[j]
                y += seg[0]
            labels.append("其他")
            x.append(y)
            break
        labels.append(seg[1])
        x.append(seg[0])

    N = 6 if N > 6 else N

    colors = ["#6699CC","#66CCFF","#669999","#66CCCC","#669966","#66CC99"]

    output = BytesIO()

    plt.figure(figsize = (6.6,3.4))
    plt.pie(
        np.array(x),
        labels = labels,
        autopct='%1.1f%%',
        colors = colors[0:N],
        wedgeprops = {
            'width':0.38,
            'edgecolor':"none",
            }, 
        textprops = {'fontsize':20},
        pctdistance = 0.81,
        labeldistance = 1.05
        )
    plt.axis('equal')
    plt.subplots_adjust(top = 0.95, bottom = 0.05, left = 0.32, hspace = 0, wspace = 0)
    plt.savefig(output,format='png', dpi = 100, transparent = True)
    plt.close()
    return Image.open(output)

def my_info_account(msg:str, dist):
    """
    我的资料卡账户分析
    """
    canvas = Image.new("RGBA", (880, 400))
    statistics = my_info_statistics(dist)
    canvas.paste(statistics, (880 - statistics.size[0], 0))
    linecard(msg, width = 880, height = 400,padding = (20,30),endline = "账户信息",canvas = canvas)
    return canvas

async def group_info_head(group_name:str, company_name:str, group_id:int, member_count:Tuple[int,int]):
    """
    群资料卡第一个信息
    """
    canvas = Image.new("RGBA", (880, 300))
    avatar = Image.open(await download_groupavatar(group_id))
    avatar = avatar.resize((250,250))
    circle_mask = Image.new("RGBA", avatar.size, (255, 255, 255, 0))
    ImageDraw.Draw(circle_mask).ellipse(((0,0),avatar.size), fill="black")
    canvas.paste(avatar, (25, 25), circle_mask)
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(font = fontname, size = 40, encoding = "utf-8")
    draw.text((300,40),f"{group_name}", fill = (0,0,0),font = font_big)
    draw.line(((300, 120), (860, 120)), fill = "gray", width = 6)
    draw.text((300,140),f"公司：{company_name if company_name else '未注册'}", fill = (0,0,0),font = font_normal)
    draw.text((300,190),f"单位：{str(group_id)[:4]}...", fill = (0,0,0),font = font_normal)
    draw.rectangle(((300,240), (740,280)), fill = "#00000033")
    draw.rectangle(((300,240), (300 + int(440 * member_count[0]/(member_count[1])),280)), fill = "#99CCFF")
    draw.text((310,240),f"{member_count[0]}/{member_count[1]}", fill = (0,0,0),font = font_normal )
    draw.text((750,240),f"{round(100 * member_count[0]/member_count[1],1)}%", fill = (0,0,0),font = font_normal)
    return canvas

def info_Splicing(info:List[IMG],BG_path, spacing:int = 20):
    """
    信息拼接
        info:信息图片列表
        bg_path:背景地址
    """
    bg = Image.open(BG_path).convert("RGBA")
    x = 880 # 设定信息宽度880像素
    y = 20
    for image in info:
        # x = image.size[0] if x < image.size[0] else x
        y += image.size[1]
        y += spacing*2
    else:
        y = y - spacing + 20

    size = (x + 40, y)

    canvas = Image.new("RGBA", size)
    bg = CropResize(bg,size)
    #bg = bg.filter(ImageFilter.GaussianBlur(radius=4))
    canvas.paste(bg, (0, 0))
    y = 20
    for image in info:
        whiteBG = Image.new("RGBA", (x,image.size[1]), (255, 255, 255, 150))
        canvas.paste(whiteBG,(20, y), mask = whiteBG)
        canvas.paste(image, (20, y), mask = image)
        y += image.size[1]
        y += spacing*2
    output = BytesIO()
    canvas.convert("RGB").save(output, format = "png")
    return output

def CropResize(img,size:Tuple[int,int]):
    """ 
    修改图像尺寸
    """

    test_x = img.size[0]/size[0]
    test_y = img.size[1]/size[1]

    if test_x < test_y:
        width = img.size[0]
        height = size[1] * test_x
    else:
        width = size[0] * test_y
        height = img.size[1]

    center = (img.size[0]/2,img.size[1]/2)
    output = img.crop(
        (
            int(center[0] - width/2),
            int(center[1] - height/2),
            int(center[0] + width/2),
            int(center[1] + height/2)
            )
        )
    output = output.resize(size)
    return output

def gini_coef(wealths:list) -> float:
    """
    计算基尼系数
    """
    wealths.insert(0,0)
    wealths_cum = np.cumsum(wealths)
    wealths_sum = wealths_cum[-1]
    N = len(wealths_cum)
    S = np.trapz(wealths_cum / wealths_sum,np.array(range(N))/(N-1))
    return 1 - 2*S