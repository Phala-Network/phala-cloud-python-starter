from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dstack_sdk import AsyncDstackClient
from dstack_sdk.ethereum import to_account
from dstack_sdk.solana import to_keypair

app = FastAPI()

@app.get("/")
async def get_info():
    client = AsyncDstackClient()
    info = await client.info()
    return JSONResponse(content=info.model_dump())

@app.get("/get_quote")
async def tdx_quote():
    client = AsyncDstackClient()
    result = await client.get_quote('test')
    return result

@app.get('/get_key')
async def derive_key():
    client = AsyncDstackClient()
    result = await client.get_key('test')
    return result

@app.get('/eth_account')
async def eth_account():
    client = AsyncDstackClient()
    result = await client.get_key('test')
    account = to_account(result)
    return { 'address': account.address }

@app.get('/sol_account')
async def sol_account():
    client = AsyncDstackClient()
    result = await client.get_key('test')
    keypair = to_keypair(result)
    return { 'address': str(keypair.pubkey()) }
