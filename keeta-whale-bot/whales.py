# whale_watcher_pretty.py
from setup import PAIR, CA, web3
import api
from datetime import datetime, timezone
import asyncio
from textwrap import shorten

# === your target channel ===

channel_ids = [1374073639204290732, 1438279901663985727]
channels = []

# === runtime state ===
seen: set[str] = set()
whale_addresses: list[str] = []


def _build_action_block(action: str) -> str:
    """Diff-style banner for BUY/SELL."""
    return "```diff\n+ BUY\n```" if action.lower(
    ) == "buy" else "```diff\n- SELL\n```"


def _build_alert_message(*,
                         action: str,
                         tx_hash: str,
                         address: str,
                         tokens_str: str,
                         percent_str: str,
                         usd_str: str,
                         balance_str: str,
                         timestamp: str,
                         tx_url: str,
                         marketcap: str = "N/A",
                         fdv: str = "N/A",
                         volume: str = "N/A",
                         cs: str = "N/A",
                         ath: str = "N/A",
                         symbol: str = "???") -> str:
    """Pretty Discord-friendly message."""
    action_block = _build_action_block(action)

    # Whale trade details
    trade_block = ("```py\n"
                   "# 🐋 Whale Trade\n"
                   f'action     = "{action.upper()}"\n'
                   f'tx_hash    = "{tx_hash}"\n'
                   f'address    = "{address}"\n'
                   f'tokens     = "{tokens_str}"  # {percent_str}\n'
                   f'usd_value  = "{usd_str}"\n'
                   f'balance    = "{balance_str}"\n'
                   f'timestamp  = "{timestamp} UTC"\n'
                   f'tx_link    = "{tx_url}"\n'
                   "```")

    msg = f"{action_block}\n{trade_block}"

    # Discord hard limit
    if len(msg) > 2000:
        msg = shorten(msg, width=1995, placeholder="…")
    return msg


async def _send_chunks(channel, text: str, limit: int = 2000):
    """Split messages if they go over Discord's 2k limit."""
    while text:
        await channel.send(text[:limit])
        text = text[limit:]


async def whale_watching(client):
    asyncio.create_task(whale_monitoring_loop(client))


async def whale_monitoring_loop(client):
    channels.clear()
    for channel in channel_ids:
        channels.append(await client.fetch_channel(channel))

    while True:
        trades = await api.get_latest_swaps(PAIR)

        for tx_hash, data in trades.items():
            # Expecting: (action, address, usd, tokens, timestamp)
            action, address, usd, tokens, timestamp = data

            usd_val = int(float(usd))
            tokens_val = int(float(tokens))

            # Time diff
            tx_url = f"https://basescan.org/tx/{tx_hash}"
            block_time = datetime.strptime(
                timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            minutes = (now - block_time).total_seconds() / 60.0

            if tx_hash in seen:
                continue
            seen.add(tx_hash)

            # Whale alert condition
            if usd_val >= 40_000 and minutes <= 5 and action.lower() == "buy":
                balance = await api.get_balance(web3, address, CA)
                balance_val = max(float(balance), float(tokens_val))
                balance_val = int(balance_val)

                percent = (float(tokens_val) / float(balance_val)
                           ) * 100 if balance_val > 0 else 0.0
                percent_str = f"{percent:.2f}%"

                balance_str = f"{balance_val:,}"
                tokens_str = f"{tokens_val:,}"
                usd_str = f"${usd_val:,}"

                print(f"DISCORD WHALE ALERT {datetime.now()} {tx_hash}")
                whale_addresses.append(address)

                msg = _build_alert_message(
                    action=action,
                    tx_hash=tx_hash,
                    address=address,
                    tokens_str=tokens_str,
                    percent_str=percent_str,
                    usd_str=usd_str,
                    balance_str=balance_str,
                    timestamp=timestamp,
                    tx_url=tx_url,
                )
                for channel in channels:
                    await _send_chunks(channel, msg)

        await asyncio.sleep(30)
