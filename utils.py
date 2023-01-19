from nonebot_plugin_imageutils import BuildImage,Text2Image
import os
import io
import unicodedata

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from PIL import Image

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.font_manager import FontProperties
import seaborn as sns

from .avatar import download_user_img

fname = os.path.dirname(__file__) + '/fonts/simsun.ttc'

sns.set(font = FontProperties(fname = fname, size=14).get_name())

def get_message_at(data: str) -> list:
    qq_list = []
    data = json.loads(data)
    try:
        for msg in data['message']:
            if msg['type'] == 'at':
                qq_list.append(int(msg['data']['qq']))
        return qq_list
    except Exception:
        return []

def is_number(s) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

def number(N) -> int:
    try:
        n = int(N)
    except ValueError:
        try:
            n = int(unicodedata.numeric(N))
        except (TypeError, ValueError):
            n = None
    return n

def text_to_png(msg, spacing: int = 10):
    '''
    文字转png
    '''
    output = io.BytesIO()
    Text2Image.from_text(msg, 50, spacing = spacing, fontname = fname).to_image("white", (20,20)).save(output, format="png")
    return output

def bbcode_to_png(msg, spacing: int = 10):
    '''
    bbcode文字转png
    '''
    output = io.BytesIO()
    Text2Image.from_bbcode_text(msg, 50, spacing = spacing, fontname = fname).to_image("white", (20,20)).save(output, format="png")
    return output

def img_Splicing(image_list:list) -> io.BytesIO:
    """
    合成图片
    """
    lst = []
    x = []
    y = []
    for img in image_list:
        image = Image.open(img)
        lst.append(image)
        x.append(image.size[0])
        y.append(image.size[1])

    image = Image.new("RGB", (max(x), sum(y)))

    i = 0
    l = 0
    while i < len(lst):
        image.paste(lst[i], (0, l))
        l += y[i]
        i += 1

    output = io.BytesIO()
    image.save(output, format="png")
    return output

def ohlc_Splicing(ohlc) -> io.BytesIO:
    """
    合成市场走势图
    """
    img1 = Image.open(ohlc[0])
    img2 = Image.open(ohlc[1])

    ohlc_x, ohlc_y = img1.size

    image = Image.new("RGB", (ohlc_x, ohlc_y + ohlc_y))
    image.paste(img1, (0, 0))
    image.paste(img2, (0, ohlc_y))

    output = io.BytesIO()
    image.save(output, format="png")
    return output

def company_info_Splicing(info, ohlc) -> io.BytesIO:
    """
    合成公司信息图
    """
    img1 = Image.open(text_to_png(info))
    img2 = Image.open(ohlc_Splicing(ohlc))

    size1, size2 = img1.size, img2.size

    ohlc_x, ohlc_y = int(size2[0]/2), int(size2[1]/2)
    x, y  = ohlc_x, int((size1[1] / size1[0])* ohlc_x)

    img1 = img1.resize((x,y))
    img2 = img2.resize((ohlc_x,ohlc_y))

    image = Image.new("RGB", (x, y + ohlc_y))
    image.paste(img1, (0, 0))
    image.paste(img2, (0, y))

    output = io.BytesIO()
    image.save(output, format="png")
    return output

async def survey_result(result):
    """
    生成调查结果
    result:调查结果原数据
    """
    nickname = result["nickname"]
    rank = result["rank"]
    all = round(result["all"],2)
    gold = result["gold"]
    stock = result["stock"]
    value = round(stock["value"],2)
    DIST = sorted(result["DIST"], key=lambda x:x[1],reverse=True)
    stock_info = ""
    for company in stock.keys():
        if company != "value":
            stock_info += f'{company}：{stock[company]}\n'
    bg_str = (
        f"           {nickname}\n"
        f"           金币：{gold}\n"
        f"           股票：{value}\n"
        f"           总计：{all}\n"
        f"           总排名：{rank}\n"
        "[color=gray][size=40]—————————————————————\n[/color][/size]"
        f"持股信息：\n"
        f"[color=gray][size=40]{stock_info}[/color][/size]"
        "[color=gray][size=40]—————————————————————\n[/color][/size]"
        f"资产分布：\n"
        "\n\n\n\n\n\n\n\n"
        )
    output = io.BytesIO()
    bg = Text2Image.from_bbcode_text(bg_str, 60, spacing = 10, fontname = fname).to_image("white", (20,20))
    avatar = Image.open(await download_user_img(result["user_id"]))
    avatar = avatar.resize((300,300))
    bg.paste(avatar, (20, 20))

    labels =[]
    x = []

    N = len(DIST)
    for i in range(N):
        seg = DIST[i]
        if i == 5:
            y = 0
            for j in range(i,N):
                y += seg[1]
            labels.append("其他")
            x.append(y)
            break
        else:
            labels.append(seg[0])
            x.append(seg[1])
            continue

    x = np.array(x)

    N = 6 if N > 6 else N

    colors = ["#6699CC","#6699FF","#66CCCC","#66CCFF","#66FFFF","#66FFCC"]

    output = io.BytesIO()

    plt.figure(figsize = (8.4,4.2))
    plt.pie(x,labels = labels, autopct='%1.1f%%',colors = colors[0:N], wedgeprops = {'width': 0.4}, pctdistance = 0.8, labeldistance = 1.1)
    plt.legend(edgecolor='#336699',facecolor='#EEFFFF')
    plt.axis('equal')
    plt.subplots_adjust(top = 0.95, bottom = 0.05, right = 1, left = 0, hspace = 0, wspace = 0)
    plt.savefig(output,format='png', dpi = 100)
    plt.close()

    pie = Image.open(output)
    bg.paste(pie, (20, (bg.size[1]) - 440))
    output = io.BytesIO()
    bg.save(output, format="png")
    return output