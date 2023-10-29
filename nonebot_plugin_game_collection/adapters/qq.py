from nonebot.adapters.qq import (
    Bot,
    MessageCreateEvent,
    Message,
    MessageSegment,
    GUILD_OWNER,
    GUILD_ADMIN,
    GUILD_CHANNEL_ADMIN
)
from typing import Coroutine
from io import BytesIO
from nonebot.permission import SUPERUSER
from ..Processor import Result

Adapters = {}

def arg_adapter(arg_name:str):
    def decorator(function:Coroutine): 
        Adapters[arg_name] = function
    return decorator

@arg_adapter("avatar")
async def _(bot:Bot,event:MessageCreateEvent):
    return event.author.avatar

@arg_adapter("image_list")
async def _(bot:Bot,event:MessageCreateEvent):
    return [f'https://{msg.data["url"]}' for msg in event.get_message() if msg.type == "attachment"]

@arg_adapter("at")
async def _(bot:Bot,event:MessageCreateEvent):
    return [msg.data["user_id"] for msg in event.get_message() if msg.type == "mention_user"]

@arg_adapter("to_me")
async def _(bot:Bot,event:MessageCreateEvent):
    return event.to_me

@arg_adapter("nickname")
async def _(bot:Bot,event:MessageCreateEvent):
    return event.author.username

@arg_adapter("permission")
async def _(bot:Bot,event:MessageCreateEvent):
    if await SUPERUSER(bot,event):
        return 3
    if await GUILD_OWNER(bot,event):
        return 2
    if await (GUILD_ADMIN|GUILD_CHANNEL_ADMIN)(bot,event):
        return 1
    return 0

async def send(send_mode:Coroutine,result:Result):
    if not result:
        return
    if isinstance(result,str):
        await send_mode(result)
    elif isinstance(result,BytesIO):
        await send_mode(MessageSegment.file_image(result))
    elif isinstance(result,list):
        message = Message()
        for seg in result:
            message += seg if isinstance(seg,str) else MessageSegment.file_image(seg)
        await send_mode(message)
    else:
        async for x in result():
            if isinstance(x,str): 
                await send_mode(x)
            elif isinstance(x,BytesIO): 
                await send_mode(MessageSegment.file_image(x))
            else:
                message = Message()
                for seg in x:
                    message += seg if isinstance(seg,str) else MessageSegment.file_image(seg)
                await send_mode(message)