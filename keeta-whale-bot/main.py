
import api
import asyncio
from datetime import datetime, timezone
import discord
from setup import DISCORD_TOKEN

from whales import whale_watching


client = discord.Client(
    fetch_offline_members=False,
    guild_subscriptions=False,
    chunk_guilds_at_startup=False,
)


@client.event
async def on_ready():
    print("WHALE BOT READY")
    await whale_watching(client)


client.run(DISCORD_TOKEN)
