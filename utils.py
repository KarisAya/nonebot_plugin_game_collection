from nonebot_plugin_imageutils import BuildImage,Text2Image
import os
import io
try:
    import ujson as json
except ModuleNotFoundError:
    import json

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

def text_to_png(msg,spacing: int = 10):
    '''
    文字转png
    '''
    output = io.BytesIO()
    Text2Image.from_text(msg, 50, spacing = spacing, fontname = fname).to_image("white", (20,20)).save(output, format="png")
    return output