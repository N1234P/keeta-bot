import api
import asyncio
import discord
from setup import DISCORD_TOKEN, PAIR, CA
from raider import raider
import sys 



client = discord.Client(
    fetch_offline_members=False,
    guild_subscriptions=False,
    chunk_guilds_at_startup=False,
)


@client.event
async def on_ready():
    print("RAID BOT READY")
    # schedule your long-running tasks instead of awaiting them here
    client.loop.create_task(raider(client))


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
