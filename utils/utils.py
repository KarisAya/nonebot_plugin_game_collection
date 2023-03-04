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

def line_wrap(msg:str, n:int= 24) -> str:
    """
    自动换行
    """
    newmsg = ""
    flag = 0
    for x in msg:
        newmsg += x
        if x == "\n":
            flag = 0
        elif flag > n:
            newmsg += "\n"
            flag = 0
        else:
            if ord(x) < 0x200:
                flag += 1
            else:
                flag += 2

    newmsg += "\n"
    newmsg = re.sub('[\r\n]+', '\n', newmsg)
    return newmsg