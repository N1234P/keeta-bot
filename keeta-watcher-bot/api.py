import requests
from setup import client


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


async def post_tweet(text):
    try:
        response = client.create_tweet(text=text)
        print(f"Tweet posted successfully! Tweet ID: {response.data['id']}")
        return response.data["id"]
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return None
