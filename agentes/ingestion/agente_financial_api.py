import os
import requests
import pandas as pd
from typing import Dict, Any

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    print("FinancialAPI WARNING: yfinance not found. Switching to raw API fallback.")
    YFINANCE_AVAILABLE = False

def descargar_datos_reales_fallback(ticker: str, output_path: str) -> str:
    """
    Downloads real market data using CoinGecko API (No Auth required for simple tests).
    """
    print(f"FinancialAPI [FALLBACK]: Downloading real data for {ticker} via CoinGecko...")
    
    coin_id = "bitcoin" if "BTC" in ticker else "ethereum"
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=1"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        prices = data.get("prices", [])
        if not prices:
            raise ValueError("Empty response from CoinGecko")
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
        with open(output_path, "w") as f:
            f.write("timestamp,price\n")
            for ts, price in prices:
                f.write(f"{ts},{price}\n")
                
        print(f"FinancialAPI: Real data saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"FinancialAPI CRITICAL: Fallback download failed: {e}")
        raise e

def descargar_datos_financieros(ticker: str, interval: str, period: str, output_path: str) -> str:
    """
    Downloads financial data using yfinance or CoinGecko fallback.
    """
    print(f"FinancialAPI: Downloading {ticker} ({interval}, {period})...")
    
    if not YFINANCE_AVAILABLE:
        return descargar_datos_reales_fallback(ticker, output_path)
        
    try:
        df = yf.download(ticker, interval=interval, period=period, progress=False)
        if df.empty:
            raise ValueError(f"No data found for {ticker}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df.to_csv(output_path)
        print(f"FinancialAPI: Data saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"FinancialAPI Error downloading data: {e}")
        raise e

async def ejecutar(**kwargs) -> Dict[str, Any]:
    """
    AgentProtocol implementation for FinancialAPI.
    """
    if "output_path" in kwargs and ("ticker" in kwargs or "symbol" in kwargs):
        ticker = kwargs.get("ticker") or kwargs.get("symbol")
        path = descargar_datos_financieros(
            ticker=ticker,
            interval=kwargs.get("interval", "1h"),
            period=kwargs.get("period", "730d"),
            output_path=kwargs["output_path"]
        )
        return {"data_path": path, "status": "COMPLETED"}
        
    return {"error": "Missing parameters for FinancialAPI", "status": "FAILED"}
