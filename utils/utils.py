import re
import unicodedata

from nonebot.adapters.onebot.v11 import MessageEvent, Message

def get_message_at(message:Message) -> list:
    '''
    获取at列表
    '''
    qq_list = []
    for msg in message:
        if msg.type == "at":
            qq_list.append(msg.data["qq"])
    return qq_list

def image_url(event:MessageEvent) -> list:
    '''
    获取图片url
    '''
    url = []
    for msg in event.message:
        if msg.type == "image":
            url.append(msg.data["url"])
    if event.reply:
        for msg in event.reply.message:
            if msg.type == "image":
                url.append(msg.data["url"])
    return url

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
            n = 0
    return n