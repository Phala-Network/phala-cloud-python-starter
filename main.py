from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, JSONResponse
from dstack_sdk import AsyncTappdClient
from dstack_sdk.ethereum import to_account
from dstack_sdk.solana import to_keypair

app = FastAPI()

@app.get("/")
async def get_info():
    client = AsyncTappdClient()
    info = await client.info()
    return JSONResponse(content=info)

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

@app.get('/eth_account')
async def eth_account():
    client = AsyncTappdClient()
    result = await client.derive_key('test')
    account = to_account(result)
    return { 'address': account.address }

@app.get('/sol_account')
async def sol_account():
    client = AsyncTappdClient()
    result = await client.derive_key('test')
    keypair = to_keypair(result)
    return { 'address': str(keypair.pubkey()) }
