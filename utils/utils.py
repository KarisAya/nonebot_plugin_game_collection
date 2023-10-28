import httpx
import asyncio

from io import BytesIO
from nonebot import get_driver

driver = get_driver()
command_start = {x for x in driver.config.command_start if x}
def extract_command(msg:str):
    for command in command_start:
        if msg.startswith(command):
            return msg[len(command):]
    return msg
async def download_url(url:str) -> BytesIO:
    async with httpx.AsyncClient() as client:
        for _ in range(3):
            try:
                resp = await client.get(url, timeout=20)
                resp.raise_for_status()
                return BytesIO(resp.content)
            except Exception:
                await asyncio.sleep(3)
    return None



