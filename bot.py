import os
import time
import json
import logging
import schedule
import requests
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO,format='%(asctime)s [%(levelname)s] %(message)s',handlers=[logging.StreamHandler()])
log = logging.getLogger(__name__)
load_dotenv()

MAX_BET_USDC    = float(os.getenv("MAX_BET_USDC", "5"))
MIN_PROBABILITY = float(os.getenv("MIN_PROBABILITY", "0.65"))
MAX_PROBABILITY = float(os.getenv("MAX_PROBABILITY", "0.85"))
MIN_LIQUIDITY   = float(os.getenv("MIN_LIQUIDITY", "10"))
SLEEP_INTERVAL  = int(os.getenv("SLEEP_INTERVAL", "300"))
DRY_RUN         = os.getenv("DRY_RUN", "true").lower() == "true"
GAMMA_API = "https://gamma-api.polymarket.com"

def get_markets():
    try:
        r = requests.get(f"{GAMMA_API}/markets", params={"active":True,"closed":False,"_limit":100}, timeout=10)
        return r.json()
    except Exception as e:
        log.error(f"خطأ: {e}")
        return []

def evaluate(market):
    try:
        if float(market.get("volume24hr",0)) < MIN_LIQUIDITY:
            return None
        for token in market.get("tokens",[]):
            price = float(token.get("price",0))
            if token.get("outcome","").upper()=="YES" and MIN_PROBABILITY<=price<=MAX_PROBABILITY:
                edge = (1/price)-1
                if edge > 0.15:
                    return {"market_id":market.get("conditionId",""),"question":market.get("question",""),"price":price,"edge":round(edge,4),"token_id":token.get("token_id","")}
    except:
        pass
    return None

def load_portfolio():
    try:
        with open("portfolio.json") as f: return json.load(f)
    except:
        return {"bets":[],"stats":{"total":0,"spent":0.0}}

def save_portfolio(p):
    with open("portfolio.json","w") as f: json.dump(p,f,ensure_ascii=False,indent=2)

def run_cycle():
    log.info("🔍​​​​​​​​​​​​​​​​
