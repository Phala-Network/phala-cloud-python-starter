from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from dstack_sdk import AsyncTappdClient

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/tdx_quote")
async def tdx_quote():
    client = AsyncTappdClient()
    result = await client.tdx_quote('test')
    return result

@app.get('/derive_key')
async def derive_key():
    client = AsyncTappdClient()
    result = await client.derive_key('test')
    return result