import requests
import json
from setup import chainbase, CA, PAIR 
from web3 import Web3
import aiohttp
import cloudscraper
import asyncio


# from is sell
# to is buy
async def get_latest_swaps(pair):

    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/base/pools/{pair}/trades"
        data = requests.get(url).json()
    except:
        return {} 

    trades = {}

    data = data["data"]
    for trade in data:
        if trade["type"] != "trade":
            continue

        attr = trade["attributes"]
        tx_hash = attr["tx_hash"]
        action = attr["kind"]
        address = attr["tx_from_address"]
        usd = attr["volume_in_usd"]
        timestamp = attr["block_timestamp"]

        if action == "sell":
            tokens = attr["from_token_amount"]
        else:
            tokens = attr["to_token_amount"]

        trades[tx_hash] = [action, address, usd, tokens, timestamp]
    return trades


async def get_murph_price():
    try:
        url = "https://anchor.murf.fi/api/getEstimate"
        headers = {"content-type": "application/json"}

       
        payload = {
            "request": {
                "from": "keeta_ao7nitutebhm2pkrfbtniepivaw324hecyb43wsxts5rrhi2p5ckgof37racm",
                "to": "keeta_anqdilpazdekdu4acw65fj7smltcp26wbrildkqtszqvverljpwpezmd44ssg",
                "amount": "0x1",
                "affinity": "from"
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()

        # Hex → decimal → token amount
        raw_amount = data["estimate"]["convertedAmount"]
        keeta_amount = int(raw_amount, 16) / (10 ** 18)

      
        keeta_usd = await get_price(
            ca=CA, 
            pair_address=PAIR    
        )

        keeta_usd_float = float(keeta_usd.replace("$", ""))
        murph_price_usd = keeta_amount * keeta_usd_float
        print(f"${murph_price_usd:.8f}")
        return f"${murph_price_usd:.8f}"
    except Exception as e:
        print("Failed get_murph_price()", e)
        await asyncio.sleep(5)
        return await get_murph_price()


async def get_price(ca, pair_address):
    try:

        url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        for pair in data["pairs"]:
            if pair["pairAddress"].lower() == pair_address.lower():

                return "$" + str(float(pair["priceUsd"]))
    except Exception as e:
        print(f"Failed to fetch price {e}")
        await asyncio.sleep(30)
        return await get_price(ca, pair_address)


def get_dexscreener_price(pair_address):
    url = f"https://api.dexscreener.com/latest/dex/pairs/ethereum/{pair_address}"
    r = requests.get(url).json()
    return r["pair"]["priceUsd"]


async def get_stats(symbol="kta"):
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&symbols={symbol}"
    data = requests.get(url).json()

    volume, marketcap, ath = -1, -1, -1

    marketcap = await reformat(data[0]["market_cap"], True, True)
    fdv = await reformat(data[0]["fully_diluted_valuation"], True, True)
    volume = await reformat(data[0]["total_volume"], True, True)
    cs = await reformat(data[0]["circulating_supply"], False, True)
    ath = await reformat(data[0]["ath"], True)

    return marketcap, fdv, volume, cs, ath


async def get_holder(ca, pos):
    if pos % 100 == 0:
        page = pos // 100
    else:
        page = (pos // 100) + 1

    page_pos = pos % 100
    if not page_pos:
        page_pos = 100

    url = f"https://api.chainbase.online/v1/token/top-holders?page={page}&limit=100&contract_address={ca}&chain_id=8453"

    headers = {"x-api-key": chainbase}

    data = requests.get(url, headers=headers).json()

    address = data["data"][page_pos - 1]["wallet_address"]
    amount = await reformat(data["data"][page_pos - 1]["amount"], integer=True)
    print(address, amount)
    return address, amount


async def reformat(data, dollar=False, integer=False):
    if integer:
        res = "{:,}".format(int(float(data)))
    else:
        res = "{:,}".format(float(data))
    if dollar:
        return "$" + res
    return res


async def get_balance(w3, wallet_address, ca):
    contract_address = Web3.to_checksum_address(ca)
    wallet_address = Web3.to_checksum_address(wallet_address)

    # Minimal ABI just to get balanceOf and decimals
    erc20_abi = [
        {
            "constant": True,
            "inputs": [{
                "name": "_owner",
                "type": "address"
            }],
            "name": "balanceOf",
            "outputs": [{
                "name": "balance",
                "type": "uint256"
            }],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{
                "name": "",
                "type": "uint8"
            }],
            "type": "function",
        },
    ]

    # Load the contract
    contract = w3.eth.contract(address=contract_address, abi=erc20_abi)

    # Call balanceOf and decimals
    balance = contract.functions.balanceOf(wallet_address).call()
    decimals = contract.functions.decimals().call()

    # Convert to human-readable
    adjusted_balance = balance / (10**decimals)

    return f"{adjusted_balance:.6f}"


