from web3 import Web3
import os


DISCORD_TOKEN = os.environ["DISCORD"]
CA = "0xc0634090f2fe6c6d75e61be2b949464abb498973"
PAIR = "0xd9edc75a3a797ec92ca370f19051babebfb2edee"
chainbase = os.environ["CHAINBASE"]
rpc_url = f"https://base-mainnet.g.alchemy.com/v2/{os.environ['WEB3']}"
web3 = Web3(Web3.HTTPProvider(rpc_url))
