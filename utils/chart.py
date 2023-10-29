from typing import Tuple, List
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as IMG
from fontTools.ttLib import TTFont
from collections import Counter

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np

import re

from .utils import download_url
from ..data import Company

from ..config import BG_image, fontname, fallback_fonts

sns.set(font=fontname)

default_BG = BG_image / "default.png"

if not default_BG.exists():
    Image.new("RGB", (200, 200), (0, 51, 102)).save(default_BG)

font_big = ImageFont.truetype(font=fontname, size=60, encoding="utf-8")
font_normal = ImageFont.truetype(font=fontname, size=40, encoding="utf-8")
font_small = ImageFont.truetype(font=fontname, size=30, encoding="utf-8")

cmap_default = TTFont(font_big.path, fontNumber=font_big.index).getBestCmap()

global fallback_fonts_cmap
fallback_fonts_cmap = {}
default_fallback_path = fm.findfont(fm.FontProperties())
for fallback in fallback_fonts:
    fallback_path = fm.findfont(fm.FontProperties(family=fallback))
    if fallback_path != default_fallback_path:
        fallback_fonts_cmap[fallback_path] = TTFont(
            fallback_path, fontNumber=0
        ).getBestCmap()
else:
    fallback_path = default_fallback_path
    fallback_fonts_cmap[fallback_path] = TTFont(
        fallback_path, fontNumber=0
    ).getBestCmap()
del default_fallback_path


def linecard_to_png(
    text: str,
    font_size=60,
    width: int = None,
    height: int = None,
    padding: tuple = (20, 20),
    spacing: float = 1.2,
    bg_color="white",
    autowrap: bool = False,
    endline=None,
):
    """
    文字转png
    """
    output = BytesIO()
    linecard(
        text=text,
        font_size=font_size,
        width=width,
        height=height,
        padding=padding,
        spacing=spacing,
        bg_color=bg_color,
        endline=endline,
    ).save(output, format="png")
    return output


class linecard_pattern:
    align = re.compile(r"\[left\]|\[right\]|\[center\]|\[pixel\]\[.*?\]")
    font = re.compile(
        r"\[font_big\]|\[font_normal\]|\[font_small\]|\[font\]\[.*?\]\[.*?\]"
    )
    color = re.compile(r"\[color\]\[.*?\]")
    passport = re.compile(r"\[passport\]")
    nowrap = re.compile(r"\[nowrap\]")
    noautowrap = re.compile(r"\[noautowrap\]")


def remove_tag(string, pattern):
    match = pattern.search(string)
    if match:
        start = match.start()
        end = match.end()
        return string[:start] + string[end:], string[start:end]
    else:
        return None


def line_wrap(line: str, width: int, font, start: int = 0):
    text_x = start
    new_str = ""
    for char in line:
        text_x += font.getlength(char)
        if text_x > width:
            new_str += "\n" + char
            text_x = 0
        else:
            new_str += char
    return new_str


def linecard(
    text: str,
    font_size: int = None,
    width: int = None,
    height: int = None,
    padding: tuple = (20, 20),
    spacing: float = 1.2,
    bg_color: str = None,
    autowrap: bool = False,
    endline=None,
    canvas=None,
):
    """
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
    """
    text = text.replace("\r\n", "\n")
    lines = text.split("\n")

    if font_size:
        font_default = ImageFont.truetype(
            font=fontname, size=font_size, encoding="utf-8"
        )
    else:
        font_default = font_normal

    cmap_default = TTFont(
        font_default.path, fontNumber=font_default.index
    ).getBestCmap()

    padding_x = padding[0]
    padding_y = padding[1]

    align = "left"

    font = font_default
    cmap = cmap_default
    color = None
    passport = 0
    noautowrap = True
    nowrap = False

    x, max_x, y, charlist = (0.0, 0.0, 0.0, [])
    for line in lines:
        passport -= 1
        if res := remove_tag(line, linecard_pattern.align):
            line, align = res
            if align.startswith("[pixel]["):
                align = align[8:-1]
                x = 0
            else:
                align = align[1:-1]
        elif nowrap:
            align = "nowrap"
        else:
            if passport == 1:
                pass
            else:
                align = "left"

        if res := remove_tag(line, linecard_pattern.font):
            line, font = res
            if font.startswith("[font]["):
                font = font[7:-1]
                inner_font_name, inner_font_size = font.split("][", 1)
                inner_font_size = int(inner_font_size)
                inner_font_size = inner_font_size if inner_font_size else font_size
                try:
                    font = ImageFont.truetype(
                        font=inner_font_name, size=inner_font_size, encoding="utf-8"
                    )
                    cmap = TTFont(font.path, fontNumber=font.index).getBestCmap()
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

        if res := remove_tag(line, linecard_pattern.color):
            line, color = res
            color = color[8:-1]
        else:
            if passport == 1:
                pass
            else:
                color = None

        if res := remove_tag(line, linecard_pattern.noautowrap):
            line = res[0]
            noautowrap = True
        else:
            if passport == 1:
                pass
            else:
                noautowrap = False

        if res := remove_tag(line, linecard_pattern.nowrap):
            line = res[0]
            nowrap = True
        else:
            nowrap = False

        if res := remove_tag(line, linecard_pattern.passport):
            line = res[0]
            passport = 2

        if autowrap and not noautowrap and width and font.getlength(line) > width:
            line = line_wrap(line, width - padding_x, font, x)

        if line == "----":
            inner_tmp = font.size * spacing
            charlist.append([line, None, y, inner_tmp, color, None])
            y += inner_tmp
        else:
            linesegs = line.split("\n")
            for seg in linesegs:
                for char in seg:
                    ordchar = ord(char)
                    if ordchar in cmap:
                        inner_font = font
                    else:
                        for fallback_font in fallback_fonts_cmap:
                            if ordchar in fallback_fonts_cmap[fallback_font]:
                                inner_font = ImageFont.truetype(
                                    font=fallback_font, size=font.size, encoding="utf-8"
                                )
                                break
                        else:
                            char = "□"
                            inner_font = font
                    charlist.append([char, x, y, inner_font, color, align])
                    x += inner_font.getlength(char)
                max_x = max(max_x, x)
                x, y = (x, y) if nowrap else (0, y + font.size * spacing)

    width = width if width else int(max_x + padding_x * 2)
    height = height if height else int(y + padding_y * 2)
    canvas = canvas if canvas else Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(canvas)

    for i, (char, x, y, font, color, align) in enumerate(charlist):
        if char == "----":
            color = color if color else "gray"
            inner_y = y + (font - 0.5) // 2 + padding_y
            draw.line(((0, inner_y), (width, inner_y)), fill=color, width=4)
        else:
            if align == "left":
                start_x = padding_x
            elif align == "nowrap":
                pass
            elif align.isdigit():
                start_x = int(align)
            else:
                for inner_i, inner_y in enumerate(map(lambda x: (x[2]), charlist[i:])):
                    if inner_y != y:
                        inner_index = charlist[i + inner_i - 1]
                        break
                else:
                    inner_index = charlist[-1]
                inner_char = inner_index[0]
                inner_font = inner_index[3]
                inner_x = inner_index[1]
                inner_x += inner_font.getlength(inner_char)
                if align == "right":
                    start_x = width - inner_x - padding_x
                elif align == "center":
                    start_x = (width - inner_x) // 2
                else:
                    start_x = padding_x
            color = color if color else "black"
            draw.text((start_x + x, y + padding_y), char, fill=color, font=font)

    if endline:
        draw.line(((0, height - 60), (width, height - 60)), fill="gray", width=4)
        text_x = int(width - font_small.getlength(endline) - 20)
        draw.text((text_x, height - 45), endline, fill="gray", font=font_small)

    return canvas


def line_splicing(info: list):
    """
    抽卡信息拼接
    """
    if len(info) == 1:
        return linecard_to_png(info[0])
    l = linecard(info[0], bg_color="white")
    r = linecard(info[1], bg_color="white")
    canvas = Image.new("RGB", (l.size[0] + r.size[0], l.size[1]), "white")
    canvas.paste(l, (0, 0))
    canvas.paste(r, (l.size[0], 0))
    output = BytesIO()
    canvas.save(output, "png")
    return output


def bar_chart(info: str, lenth: float):
    """
    带头像的条形图
    """
    canvas = Image.new("RGBA", (880, 60))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(((70, 10), (860, 50)), fill="#00000033")
    draw.rectangle(((70, 10), (80 + int(lenth * 780), 50)), fill="#99CCFF")
    draw.text((80, 10), info, fill=(0, 0, 0), font=font_normal)

    async def func(url: str):
        avatar = Image.open(await download_url(url))
        avatar = avatar.resize((60, 60))
        circle_mask = Image.new("RGBA", avatar.size, (255, 255, 255, 0))
        ImageDraw.Draw(circle_mask).ellipse(((0, 0), avatar.size), fill="black")
        canvas.paste(avatar, (5, 0), circle_mask)
        return canvas

    return func


def alchemy_info(alchemy: dict, nickname: str, avatar: bytes):
    """
    炼金账户
    """
    canvas = Image.new("RGBA", (880, 400))
    avatar = Image.open(avatar).resize((160, 160))
    circle_mask = Image.new("RGBA", avatar.size, (255, 255, 255, 0))
    ImageDraw.Draw(circle_mask).ellipse(((0, 0), avatar.size), fill="black")
    canvas.paste(avatar, (20, 20), circle_mask)
    draw = ImageDraw.Draw(canvas)
    draw.line(((20, 200), (480, 200)), fill="gray", width=4)

    alchemy = Counter(alchemy)
    # 创建变量标签
    labels = ["蒸汽", "雷电", "岩浆", "尘埃", "沼泽", "寒冰"]
    # 创建变量值
    values = [
        alchemy["5"],
        alchemy["9"],
        alchemy["8"],
        alchemy["0"],
        alchemy["6"],
        alchemy["7"],
    ]
    products = max(values)
    # 计算角度
    angles = np.linspace(0.5 * np.pi, 2.5 * np.pi, 6, endpoint=False).tolist()
    angles = [(x if x < 2 * np.pi else x - 2 * np.pi) for x in angles]
    # 闭合雷达图
    values.append(values[0])
    angles.append(angles[0])
    # 绘制雷达图
    mainproduct = max(values)
    mainproduct = max(mainproduct, 1)
    values = [x * 4 / mainproduct for x in values]
    sns.set(font="simsun")
    plt.figure(figsize=(4, 4))
    ax = plt.subplot(111, polar=True)
    ax.plot(angles, values, linewidth=2, linestyle="solid")
    ax.fill(angles, values, "b", alpha=0.1)
    ax.set_yticklabels([])
    plt.xticks(angles[:-1], labels, fontsize=12)
    output = BytesIO()
    plt.savefig(output, transparent=True)
    canvas.paste(Image.open(output), (480, 0))

    water, fire, earth, wind = alchemy["1"], alchemy["2"], alchemy["3"], alchemy["4"]
    elements = [water, fire, earth, wind]
    max_value = max(elements)
    ethereum = max(min([water, fire, earth, wind]) - 2, 0)
    tag = (
        f'{"元素炼金师" if ethereum*4 > products else "传统炼金师"} Lv.{integer_log(ethereum,2)}'
    )
    draw.text((20, 240), tag, fill=(0, 0, 0), font=font_big)
    draw.text((21, 241), tag, fill=(0, 0, 0), font=font_big)
    tag = f"主要元素 {'|'.join({0:'水',1:'火',2:'土',3:'风'}[i] for i, value in enumerate(elements) if value == max_value)}"
    draw.text((20, 320), tag, fill=(0, 0, 0), font=font_big)
    draw.text((21, 321), tag, fill=(0, 0, 0), font=font_big)
    draw.text((200, 70), nickname, fill=(0, 0, 0), font=font_big)
    info = [canvas]

    def bar_chart(info: str, lenth: float, color: str = "99CCFF"):
        """
        条形图
        """
        canvas = Image.new("RGBA", (880, 60))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle(((20, 10), (860, 50)), fill="#00000033")
        draw.rectangle(((20, 10), (80 + int(lenth * 780), 50)), fill=color)
        draw.text((30, 10), info, fill=(0, 0, 0), font=font_normal)
        return canvas

    level = integer_log(water, 2)
    info.append(bar_chart(f"水元素Lv.{level}", water / 2 ** (level + 1), "#66CCFFCC"))
    level = integer_log(fire, 2)
    info.append(bar_chart(f"火元素Lv.{level}", fire / 2 ** (level + 1), "#CC3300CC"))
    level = integer_log(earth, 2)
    info.append(bar_chart(f"土元素Lv.{level}", earth / 2 ** (level + 1), "#996633CC"))
    level = integer_log(wind, 2)
    info.append(bar_chart(f"风元素Lv.{level}", wind / 2 ** (level + 1), "#99CCFFCC"))

    element = alchemy["5"]
    level = integer_log(element, 2)
    info.append(bar_chart(f"蒸汽Lv.{level}", element / 2 ** (level + 1), "#CCFFFFCC"))
    element = alchemy["6"]
    level = integer_log(element, 2)
    info.append(bar_chart(f"沼泽Lv.{level}", element / 2 ** (level + 1), "#666633CC"))
    element = alchemy["7"]
    level = integer_log(element, 2)
    info.append(bar_chart(f"寒冰Lv.{level}", element / 2 ** (level + 1), "#0099FFCC"))
    element = alchemy["8"]
    level = integer_log(element, 2)
    info.append(bar_chart(f"岩浆Lv.{level}", element / 2 ** (level + 1), "#990000CC"))
    element = alchemy["9"]
    level = integer_log(element, 2)
    info.append(bar_chart(f"雷电Lv.{level}", element / 2 ** (level + 1), "#9900FFCC"))
    element = alchemy["0"]
    level = integer_log(element, 2)
    info.append(bar_chart(f"尘埃Lv.{level}", element / 2 ** (level + 1), "#99CCCCCC"))
    return info


def my_info_head(gold: int, win: int, lose: int, nickname: str, avatar: bytes):
    """
    我的资料卡第一个信息
    """
    canvas = Image.new("RGBA", (880, 300))
    avatar = Image.open(avatar).resize((260, 260))
    circle_mask = Image.new("RGBA", avatar.size, (255, 255, 255, 0))
    ImageDraw.Draw(circle_mask).ellipse(((0, 0), avatar.size), fill="black")
    canvas.paste(avatar, (20, 20), circle_mask)
    draw = ImageDraw.Draw(canvas)
    draw.text((300, 40), f"{nickname}", fill=(0, 0, 0), font=font_big)
    draw.line(((300, 120), (860, 120)), fill="gray", width=4)
    draw.text((300, 140), f"金币 {'{:,}'.format(gold)}", fill=(0, 0, 0), font=font_normal)
    draw.text((300, 190), f"战绩 {win}:{lose}", fill=(0, 0, 0), font=font_normal)
    draw.text(
        (300, 240),
        f"胜率 {(round(win * 100 / (win + lose), 2) if win > 0 else 0)}%\n",
        fill=(0, 0, 0),
        font=font_normal,
    )
    return canvas


def my_exchange_head(gold: int, nickname: str, invest: dict, avatar: bytes):
    """
    我的交易信息第一个信息
    """
    canvas = Image.new("RGBA", (880, 250))
    avatar = Image.open(avatar).resize((210, 210))
    circle_mask = Image.new("RGBA", avatar.size, (255, 255, 255, 0))
    ImageDraw.Draw(circle_mask).ellipse(((0, 0), avatar.size), fill="black")
    canvas.paste(avatar, (20, 20), circle_mask)
    draw = ImageDraw.Draw(canvas)
    draw.text((250, 40), f"{nickname}", fill=(0, 0, 0), font=font_big)
    draw.line(((250, 120), (860, 120)), fill="gray", width=4)
    draw.text((250, 140), f"金币 {'{:,}'.format(gold)}", fill=(0, 0, 0), font=font_normal)
    draw.text((250, 190), f"股票 {len(invest)}", fill=(0, 0, 0), font=font_normal)
    return canvas


def my_info_account(msg: str, dist):
    """
    我的资料卡账户分析
    """
    canvas = Image.new("RGBA", (880, 400))

    dist.sort(key=lambda x: x[0], reverse=True)
    labels = []
    x = []
    for N, (gold, group_name) in enumerate(dist):
        if N < 5:
            x.append(gold)
            labels.append(group_name)
        else:
            labels.append("其他")
            x.append(sum(seg[0] for seg in dist[N:]))
            break
    N += 1
    colors = ["#6699CC", "#66CCFF", "#669999", "#66CCCC", "#669966", "#66CC99"]
    output = BytesIO()

    plt.figure(figsize=(6.6, 3.4))
    plt.pie(
        np.array(x),
        labels=labels,
        autopct=lambda pct: "" if pct < 1 else f"{pct:.1f}%",
        colors=colors[0:N],
        wedgeprops={
            "width": 0.38,
            "edgecolor": "none",
        },
        textprops={"fontsize": 20},
        pctdistance=0.81,
        labeldistance=1.05,
    )
    plt.axis("equal")
    plt.subplots_adjust(top=0.95, bottom=0.05, left=0.32, hspace=0, wspace=0)
    plt.savefig(output, format="png", dpi=100, transparent=True)
    plt.close()

    statistics = Image.open(output)
    canvas.paste(statistics, (880 - statistics.size[0], 0))
    linecard(
        msg, width=880, height=400, padding=(20, 30), endline="账户信息", canvas=canvas
    )
    return canvas


def group_info_head(company_name: str, group_id: int, member_count: int):
    """
    群资料卡第一个信息
    """
    canvas = Image.new("RGBA", (880, 250))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (20, 40), company_name if company_name else "未注册", fill=(0, 0, 0), font=font_big
    )
    draw.line(((0, 120), (880, 120)), fill="gray", width=4)
    draw.text((20, 140), f"注册：{str(group_id)[:4]}...", fill=(0, 0, 0), font=font_normal)
    draw.text((20, 190), f"成员：{member_count}", fill=(0, 0, 0), font=font_normal)
    return canvas


def group_info_account(company: Company, dist):
    """
    群资料卡账户分析
    """
    canvas = Image.new("RGBA", (880, 320))
    plt.figure(figsize=(8.8, 3.2))
    explode = [0, 0.1, 0.19, 0.27, 0.34, 0.40, 0.45, 0.49, 0.52]
    # 投资占比
    plt.subplot(1, 2, 1)
    plt.title("投资占比")
    plt.pie(
        [company.group_gold, int(sum(x[0] for x in dist))],
        labels=["", ""],
        autopct="%1.1f%%",
        colors=["#FFCC33", "#0066CC"],
        wedgeprops={
            "edgecolor": "none",
        },
        textprops={"fontsize": 15},
        pctdistance=1.2,
        explode=explode[0:2],
    )
    plt.legend(["金币", "股票"], loc=(-0.2, 0), frameon=False)
    # 资产分布
    plt.subplot(1, 2, 2)
    plt.title("资产分布")
    dist.sort(key=lambda x: x[0], reverse=True)
    labels = []
    x = []
    for N, (gold, group_name) in enumerate(dist):
        if N < 8:
            x.append(gold)
            labels.append(group_name)
        else:
            labels.append("其他")
            x.append(sum(seg[0] for seg in dist[N:]))
            break
    N += 1
    colors = [
        "#351c75",
        "#0b5394",
        "#1155cc",
        "#134f5c",
        "#38761d",
        "#bf9000",
        "#b45f06",
        "#990000",
        "#741b47",
    ]
    output = BytesIO()
    plt.pie(
        x,
        labels=[""] * N,
        autopct=lambda pct: "" if pct < 1 else f"{pct:.1f}%",
        colors=colors[0:N],
        wedgeprops={
            "edgecolor": "none",
        },
        textprops={"fontsize": 15},
        pctdistance=1.2,
        explode=explode[0:N],
    )
    plt.legend(labels, loc=(-0.6, 0), frameon=False)
    plt.subplots_adjust(
        top=0.9, bottom=0.1, left=0.05, right=0.95, hspace=0, wspace=0.6
    )
    plt.savefig(output, format="png", dpi=100, transparent=True)
    plt.close()

    return Image.open(output)


def info_splicing(info: List[IMG], BG_path, spacing: int = 20):
    """
    信息拼接
        info:信息图片列表
        bg_path:背景地址
    """
    bg = Image.open(BG_path).convert("RGBA")
    x = 880  # 设定信息宽度880像素
    y = 20
    for image in info:
        # x = image.size[0] if x < image.size[0] else x
        y += image.size[1]
        y += spacing * 2
    else:
        y = y - spacing + 20

    size = (x + 40, y)

    canvas = Image.new("RGBA", size)
    bg = CropResize(bg, size)
    # bg = bg.filter(ImageFilter.GaussianBlur(radius=4))
    canvas.paste(bg, (0, 0))
    y = 20
    for image in info:
        whiteBG = Image.new("RGBA", (x, image.size[1]), (255, 255, 255, 150))
        canvas.paste(whiteBG, (20, y), mask=whiteBG)
        canvas.paste(image, (20, y), mask=image)
        y += image.size[1]
        y += spacing * 2
    output = BytesIO()
    canvas.convert("RGB").save(output, format="png")
    return output


def CropResize(img, size: Tuple[int, int]):
    """
    修改图像尺寸
    """

    test_x = img.size[0] / size[0]
    test_y = img.size[1] / size[1]

    if test_x < test_y:
        width = img.size[0]
        height = size[1] * test_x
    else:
        width = size[0] * test_y
        height = img.size[1]

    center = (img.size[0] / 2, img.size[1] / 2)
    output = img.crop(
        (
            int(center[0] - width / 2),
            int(center[1] - height / 2),
            int(center[0] + width / 2),
            int(center[1] + height / 2),
        )
    )
    output = output.resize(size)
    return output


# 上面是图片


def gini_coef(wealths: list) -> float:
    """
    计算基尼系数
    """
    wealths.insert(0, 0)
    wealths_cum = np.cumsum(wealths)
    wealths_sum = wealths_cum[-1]
    N = len(wealths_cum)
    S = np.trapz(wealths_cum / wealths_sum, np.array(range(N)) / (N - 1))
    return 1 - 2 * S


def integer_log(number, base):
    result = 0
    while number >= base:
        number //= base
        result += 1
    return result
