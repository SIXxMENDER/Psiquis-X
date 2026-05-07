import requests
import csv
import time
from datetime import datetime
import os

def fetch_binance_klines(symbol="BTCUSDT", interval="1h", limit=1000):
    print(f"[FETCH] Fetching {limit} {interval} candles for {symbol} from Binance...")
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"[ERROR] Error fetching data: {response.text}")
        return []
        
    data = response.json()
    print(f"[SUCCESS] Successfully fetched {len(data)} candles.")
    return data

def save_to_csv(data, filename="missions/sovereign_quant/data/btc_data.csv"):
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    print(f"[SAVE] Saving data to {filename}...")
    # Binance kline format: [Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Ignore]
    headers = ["timestamp", "open", "high", "low", "close", "volume"]
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        
        for kline in data:
            # Convert milliseconds timestamp to readable format
            ts = int(kline[0])
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            volume = float(kline[5])
            
            writer.writerow([ts, open_price, high_price, low_price, close_price, volume])
            
    print(f"[DONE] Data successfully saved to {filename}")

if __name__ == "__main__":
    # Fetch ~6 months of 1h data (approx 4320 candles). 
    # Binance limits to 1000 per request, so we will just fetch the latest 1000 for the demo
    # For a real backtest, we would paginate. 1000 hours is ~41 days, which is enough to prove the engine.
    # To get more, we would need to loop and pass 'endTime'. For demo simplicity, 1000 is perfect.
    
    klines = fetch_binance_klines("BTCUSDT", "1h", 1000)
    if klines:
        save_to_csv(klines, "missions/sovereign_quant/data/btc_1h.csv")
