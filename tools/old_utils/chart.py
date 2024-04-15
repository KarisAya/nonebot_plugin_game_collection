from typing import Tuple, List
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont
from PIL.Image import Image as IMG
from fontTools.ttLib import TTFont
from collections import Counter

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np


def alchemy_info(alchemy: dict, nickname: str, avatar_: bytes):
    """
    炼金账户
    """
    canvas = Image.new("RGBA", (880, 400))
    avatar = Image.open(avatar_).resize((160, 160))
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
    tag = f'{"元素炼金师" if ethereum*4 > products else "传统炼金师"} Lv.{integer_log(ethereum,2)}'
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
