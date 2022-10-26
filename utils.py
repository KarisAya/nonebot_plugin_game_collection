from nonebot_plugin_imageutils import BuildImage,Text2Image
import os
import io
try:
    import ujson as json
except ModuleNotFoundError:
    import json

from PIL import Image

fname = os.path.dirname(__file__) + '/fonts/simsun.ttc'

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
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

def text_to_png(msg, spacing: int = 10):
    '''
    文字转png
    '''
    output = io.BytesIO()
    Text2Image.from_text(msg, 50, spacing = spacing, fontname = fname).to_image("white", (20,20)).save(output, format="png")
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
