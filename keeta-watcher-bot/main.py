import asyncio
from datetime import datetime, timezone
import api
from setup import PAIR

# record the moment we start (UTC-aware)
launch_time = datetime.now(timezone.utc)
seen = set()


async def run_api():
    print("KEETA TWITTER BOT LAUNCHING...")
    while True:
        trades = await api.get_latest_swaps(PAIR)

        for tx_hash, (action, address, usd, tokens,
                      timestamp) in trades.items():
            usd, tokens = int(float(usd)), int(float(tokens))
            tx_url = f"basescan.org/tx/{tx_hash}"

            block_time = datetime.strptime(
                timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

            if tx_hash in seen or block_time < launch_time or action.lower(
            ) != "buy":
                continue

            seen.add(tx_hash)

            if (usd >= 100000 and
                (datetime.now(timezone.utc) - block_time).total_seconds() / 60
                    <= 5):
                # Format numbers with commas
                tokens_formatted = "{:,}".format(tokens)
                usd_formatted = "$" + "{:,}".format(usd)

                print(f"Reporting twitter whale trade {tx_hash}")

                message = f"🐋🐋🐋🐋🐋🐋🐋🐋 {tokens_formatted} $KTA ({usd_formatted}) bought on #Aerodrome (0xd9eD...) Liquidity Pool \n\n {tx_url}"

                await api.post_tweet(message)
                await asyncio.sleep(5)

        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run_api())
