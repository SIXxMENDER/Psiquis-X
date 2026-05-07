import sys
import os
import pandas as pd
import numpy as np
import yfinance as yf
import json
sys.path.append(os.getcwd())
from agentes import agente_p4

# --- CONFIG ---
STRATEGY_PATH = "strategies/optimized_regime_adaptive.py"
WINDOW_DAYS = 30
STEP_DAYS = 15

def load_data():
    print("Loading market data for Walk-Forward Validation...")
    TICKER = "BTC-USD"
    PERIOD = "729d"
    INTERVAL = "1h"
    try:
        df = yf.download(TICKER, period=PERIOD, interval=INTERVAL, progress=False)
        if df.empty: raise ValueError("Empty DF")
    except:
        df = yf.download(TICKER, period="59d", interval=INTERVAL, progress=False)
        
    df.reset_index(inplace=True)
    new_cols = []
    for c in df.columns:
        if isinstance(c, tuple): new_cols.append(c[0].lower())
        else: new_cols.append(c.lower())
    df.columns = new_cols
    
    if 'date' in df.columns: df.rename(columns={'date': 'timestamp'}, inplace=True)
    elif 'datetime' in df.columns: df.rename(columns={'datetime': 'timestamp'}, inplace=True)
    
    # Funding Rate (Real or Dummy)
    print("💰 Descargando Funding Rates (Binance Futures)...")
    try:
        import ccxt
        exchange = ccxt.binanceusdm()
        start_ts = int(df['timestamp'].iloc[0].timestamp() * 1000)
        funding_rates = exchange.fetch_funding_rate_history('BTC/USDT:USDT', since=start_ts, limit=1000)
        
        if funding_rates:
            df_fr = pd.DataFrame(funding_rates)
            df_fr['timestamp'] = pd.to_datetime(df_fr['timestamp'], unit='ms')
            df_fr = df_fr[['timestamp', 'fundingRate']]
            df_fr.rename(columns={'fundingRate': 'funding_rate'}, inplace=True)
            df = pd.merge_asof(df.sort_values('timestamp'), df_fr.sort_values('timestamp'), on='timestamp', direction='backward')
            df['funding_rate'].fillna(0, inplace=True)
        else:
            df['funding_rate'] = 0
    except:
        df['funding_rate'] = 0
        
    return df

def run_walk_forward():
    # 1. Load Data & Strategy
    df = load_data()
    
    try:
        with open(STRATEGY_PATH, "r", encoding="utf-8") as f:
            strategy_code = f.read()
    except FileNotFoundError:
        print(f"❌ Strategy file not found: {STRATEGY_PATH}")
        return

    print(f"\n🏃 Running Walk-Forward Validation (Window: {WINDOW_DAYS}d, Step: {STEP_DAYS}d)...")
    
    # 2. Run Full Backtest first to get the equity curve
    full_records = df.to_dict('records')
    result = agente_p4.ejecutar_backtest(
        datos_historicos=full_records,
        codigo_estrategia=strategy_code
    )
    
    if result['status'] != 'SUCCESS':
        print(f"❌ Full backtest failed: {result.get('error')}")
        return

    # We need the equity curve with timestamps to calculate rolling metrics.
    # agente_p4 returns 'equity_curve' as a list, but we need it aligned with the DF.
    # Let's re-run the logic locally or assume agente_p4 can return the full DF if modified.
    # For now, let's just slice the input DF and run backtests on chunks. This is slower but safer.
    
    start_date = df['timestamp'].min()
    end_date = df['timestamp'].max()
    
    current_date = start_date
    results = []
    
    while current_date + pd.Timedelta(days=WINDOW_DAYS) <= end_date:
        window_end = current_date + pd.Timedelta(days=WINDOW_DAYS)
        
        # Slice DF
        mask = (df['timestamp'] >= current_date) & (df['timestamp'] < window_end)
        window_df = df.loc[mask]
        
        if len(window_df) < 100: # Skip if too few candles
            current_date += pd.Timedelta(days=STEP_DAYS)
            continue
            
        window_records = window_df.to_dict('records')
        
        # Run Backtest on Window
        w_result = agente_p4.ejecutar_backtest(
            datos_historicos=window_records,
            codigo_estrategia=strategy_code
        )
        
        if w_result['status'] == 'SUCCESS':
            m = w_result['metricas']
            results.append({
                'start': current_date,
                'end': window_end,
                'sharpe': m.get('sharpe_ratio', 0),
                'return': m.get('total_return_pct', 0),
                'dd': m.get('max_drawdown_pct', 0),
                'trades': m.get('trades_count', 0)
            })
            print(f"   📅 {current_date.date()} -> {window_end.date()} | Sharpe: {m.get('sharpe_ratio'):.2f} | Ret: {m.get('total_return_pct'):.2f}%")
        
        current_date += pd.Timedelta(days=STEP_DAYS)
        
    # 3. Analyze Results
    if not results:
        print("❌ No valid windows found.")
        return
        
    df_res = pd.DataFrame(results)
    
    print("\n📊 Walk-Forward Analysis Report")
    print("="*40)
    print(f"Total Windows: {len(df_res)}")
    print(f"Profitable Windows: {len(df_res[df_res['return'] > 0])} ({len(df_res[df_res['return'] > 0])/len(df_res)*100:.1f}%)")
    print(f"Avg Sharpe: {df_res['sharpe'].mean():.2f}")
    print(f"Avg Return (Monthly): {df_res['return'].mean():.2f}%")
    print(f"Avg Drawdown: {df_res['dd'].mean():.2f}%")
    print("="*40)
    
    # Save Report
    df_res.to_csv("walk_forward_results.csv", index=False)
    print("💾 Detailed results saved to walk_forward_results.csv")

if __name__ == "__main__":
    run_walk_forward()
