import httpx
import asyncio
from io import BytesIO
from PIL import Image

async def download_avatar(user_id:int) -> bytes:
    url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
    if data := await download_url(url):
        return BytesIO(data)
    url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=100"
    if data := await download_url(url):
        return BytesIO(data)

    output = BytesIO()
    Image.new("RGBA", (300, 300),color = "gray").save(output, format = "png")
    return output

async def download_groupavatar(group_id:int) -> bytes:
    url = f"https://p.qlogo.cn/gh/{group_id}/{group_id}/640"
    if data := await download_url(url):
        return BytesIO(data)
    url = f"https://p.qlogo.cn/gh/{group_id}/{group_id}/100"
    if data := await download_url(url):
        return BytesIO(data)

    output = BytesIO()
    Image.new("RGBA", (300, 300),color = "gray").save(output, format = "png")
    return output

async def download_url(url:str) -> bytes:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                resp = await client.get(url, timeout=20)
                resp.raise_for_status()
                return resp.content
            except Exception:
                await asyncio.sleep(3)
    return None