import asyncio
import uvicorn
from api import app
uvicorn.run(app, host = "127.0.0.1", port = 8000)