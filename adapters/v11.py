from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    Message,
    MessageSegment,
    GROUP_ADMIN,
    GROUP_OWNER,
)
from typing import Coroutine
from io import BytesIO
from nonebot.adapters.onebot.v11.event import Sender
from nonebot.permission import SUPERUSER
from ..Processor import Result

Adapters = {}

def arg_adapter(arg_name:str):
    def decorator(function:Coroutine): 
        Adapters[arg_name] = function
    return decorator

@arg_adapter("avatar")
async def _(bot:Bot,event:MessageEvent):
    return f"https://q1.qlogo.cn/g?b=qq&nk={event.user_id}&s=640"

@arg_adapter("image_list")
async def _(bot:Bot,event:MessageEvent):
    url = [msg.data["url"] for msg in event.message if msg.type == "image"]
    if event.reply:
        url += [msg.data["url"] for msg in event.reply.message if msg.type == "image"]
    return url

@arg_adapter("at")
async def _(bot:Bot,event:MessageEvent):
    return [msg.data["qq"] for msg in event.message if msg.type == "at"]

@arg_adapter("to_me")
async def _(bot:Bot,event:MessageEvent):
    return event.to_me

@arg_adapter("nickname")
async def _(bot:Bot,event:MessageEvent):
    return event.sender.nickname or event.sender.card

@arg_adapter("permission")
async def _(bot:Bot,event:MessageEvent):
    if await SUPERUSER(bot,event):
        return 3
    if await GROUP_OWNER(bot,event):
        return 2
    if await GROUP_ADMIN(bot,event):
        return 1
    return 0

async def send(send_mode:Coroutine,result:Result):
    if not result:
        return
    if isinstance(result,str):
        await send_mode(result)
    elif isinstance(result,BytesIO):
        await send_mode(MessageSegment.image(result))
    elif isinstance(result,list):
        message = Message()
        for seg in result:
            message += seg if isinstance(seg,str) else MessageSegment.image(seg)
        await send_mode(message)
    else:
        async for x in result():
            if isinstance(x,str): 
                await send_mode(x)
            elif isinstance(x,BytesIO): 
                await send_mode(MessageSegment.image(x))
            else:
                message = Message()
                for seg in x:
                    message += seg if isinstance(seg,str) else MessageSegment.image(seg)
                await send_mode(message)