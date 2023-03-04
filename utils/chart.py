from typing import Tuple,Dict,List
from pathlib import Path
from io import BytesIO
from PIL import Image,ImageDraw,ImageFont
from PIL.Image import Image as IMG

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from nonebot_plugin_imageutils import Text2Image

from .avatar import download_avatar,download_groupavatar

from ..data.data import UserDict
from ..data.data import resourcefile

from ..config import BG_image,fontname

sns.set(font = fontname)

default_BG = BG_image / "default.png"

if not default_BG.exists():
    Image.new('RGB', (200, 200), (0, 51, 102)).save(default_BG)

font_big = ImageFont.truetype(font = fontname, size = 60, encoding = "utf-8")

font_small = ImageFont.truetype(font = fontname, size = 40, encoding = "utf-8")

def text_to_png(msg, spacing:int = 10, bg_colour = "white"):
    '''
    文字转png
    '''
    output = BytesIO()
    Text2Image.from_text(msg, 50, spacing = spacing, fontname = fontname).to_image(bg_colour, (20,20)).save(output, format="png")
    return output

def bbcode_to_PIL(msg:str, fontsize:int = 50,spacing:int = 10, fontname:str = fontname, bg_colour:str = None):
    '''
    bbcode文字转PIL
    '''
    return Text2Image.from_bbcode_text(msg, fontsize, spacing = spacing, fontname = fontname).to_image(bg_colour, (20,20))

def bbcode_to_png(msg, fontsize:int = 50, spacing:int = 10):
    '''
    bbcode文字转png
    '''
    output = BytesIO()
    bbcode_to_PIL(msg = msg ,fontsize = fontsize, spacing = spacing, bg_colour = "white").save(output, format="png")
    return output

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
    draw.line(((300, 120), (860, 120)), fill = "gray", width = 6)
    draw.text((300,140),f"金币 {'{:,}'.format(gold)}", fill = (0,0,0),font = font_small)
    draw.text((300,190),f"战绩 {win}:{lose}", fill = (0,0,0),font = font_small)
    draw.text((300,240),f"胜率 {(round(win * 100 / (win + lose), 2) if win > 0 else 0)}%\n", fill=(0,0,0),font = font_small)
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

    plt.figure(figsize = (8.8,4.4))
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
    plt.subplots_adjust(top = 0.95, bottom = 0.05, right = 1, left = 0, hspace = 0, wspace = 0)
    plt.savefig(output,format='png', dpi = 100, transparent = True)
    plt.close()
    return Image.open(output)

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
    draw.text((300,140),f"公司：{company_name if company_name else '未注册'}", fill = (0,0,0),font = font_small)
    draw.text((300,190),f"单位：{str(group_id)[:4]}...", fill = (0,0,0),font = font_small)
    draw.rectangle(((300,240), (740,280)), fill = "#00000033")
    draw.rectangle(((300,240), (300 + int(440 * member_count[0]/(member_count[1])),280)), fill = "#99CCFF")
    draw.text((310,240),f"{member_count[0]}/{member_count[1]}", fill = (0,0,0),font = font_small )
    draw.text((750,240),f"{round(100 * member_count[0]/member_count[1],1)}%", fill = (0,0,0),font = font_small)
    return canvas

def info_Splicing(info:List[IMG],BG_path):
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
        y += 40
    else:
        y -= 20

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
        y += 40
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