import sys
import os
import pandas as pd
import numpy as np
import yfinance as yf
import json
import time

# Add root to path
sys.path.append(os.getcwd())

from agentes import agente_p4
from agentes.monte_carlo_engine import MonteCarloEngine

# --- CONFIG ---
STRATEGY_PATH = "strategies/optimized_trend_pullback.py" # Default, can be arg
TICKER = "BTC-USD"
PERIOD = "729d"
INTERVAL = "1h"

def load_data():
    print(f"Loading data for {TICKER}...")
    try:
        df = yf.download(TICKER, period=PERIOD, interval=INTERVAL, progress=False)
        if df.empty: raise ValueError("Empty DataFrame")
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
    
    # Fake funding for now (or load from file if available)
    df['funding_rate'] = 0.0 
    
    return df.to_dict('records')

def load_strategy(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Strategy file not found: {path}")
        sys.exit(1)

def main():
    print("🚀 Starting Institutional Robustness Validation...")
    print("="*60)
    
    # 1. Load Data & Strategy
    data = load_data()
    strategy_code = load_strategy(STRATEGY_PATH)
    
    # 2. Run Base Backtest
    print("\n1️⃣  Running Base Backtest...")
    start_time = time.time()
    result = agente_p4.ejecutar_backtest(
        datos_historicos=data,
        codigo_estrategia=strategy_code
    )
    duration = time.time() - start_time
    
    if result['status'] != 'SUCCESS':
        print(f"❌ Backtest Failed: {result.get('error')}")
        sys.exit(1)
        
    metrics = result['metricas']
    print(f"   ✅ Done in {duration:.2f}s")
    print(f"   CAGR: {metrics.get('cagr_pct')}% | Sharpe: {metrics.get('sharpe_ratio')}")
    print(f"   Trades: {metrics.get('trades_count')}")
    
    # 3. Extract Trade Returns
    # Agente P4 currently returns metrics but maybe not the raw trade list easily.
    # We need to modify P4 or re-calculate trades from the equity curve/signals if possible.
    # For now, let's assume P4 returns a list of trades or we can infer them.
    # EDIT: P4 returns 'metricas'. We need to access the DataFrame inside P4 or modify P4 to return trades.
    # HACK: Since we can't easily modify P4 return signature without breaking other things, 
    # let's re-run a simplified extraction here or rely on P4 returning 'trades_list' if we add it.
    # Let's check P4 code... P4 calculates 'strategy_return'. We can use that.
    # But 'strategy_return' is per candle. Monte Carlo needs per-trade returns.
    # We will approximate per-trade returns by grouping consecutive non-zero returns? No, that's hard.
    # BETTER: Let's modify P4 slightly to return the 'trades' list in the result dict.
    # For this script, I will simulate extracting trades from the 'strategy_return' series if P4 doesn't provide it.
    # Actually, let's just assume for this step we have the returns. 
    # Since I cannot modify P4 in this turn easily without context switch, I will try to infer it from the result if possible.
    # Wait, I can modify P4. I should modify P4 to return 'trades_returns' list.
    
    # ... (Self-correction: I will modify P4 in the next step to return trade_returns. 
    # For now, I will write this script assuming result['trade_returns'] exists).
    
    trade_returns = result.get('trade_returns', [])
    
    if not trade_returns:
        print("⚠️  No trade returns found (or P4 not updated). Skipping Monte Carlo.")
        # Fallback for demo: Generate fake returns based on metrics
        # avg_ret = metrics.get('total_return_pct') / max(1, metrics.get('trades_count'))
        # trade_returns = np.random.normal(avg_ret/100, 0.02, metrics.get('trades_count'))
        pass

    # 4. Run Monte Carlo
    if len(trade_returns) > 10:
        print("\n2️⃣  Running Monte Carlo Simulation (10,000 runs)...")
        mc = MonteCarloEngine(trade_returns, initial_capital=10000)
        mc_results = mc.run_simulation()
        
        print(f"   🎲 Risk of Ruin (<50% cap): {mc_results['risk_of_ruin_pct']}%")
        print(f"   🎲 Probability of Profit: {mc_results['prob_profit_pct']}%")
        print(f"   🎲 Median Drawdown: {mc_results['median_max_dd_pct']}%")
        print(f"   🎲 Worst Case Return (VaR 95%): {mc_results['worst_case_return_pct_var95']}%")
        
        # 5. Run Stress Tests
        print("\n3️⃣  Running Stress Tests...")
        stress_results = mc.run_stress_test()
        print(f"   🔥 Black Swan Impact: {stress_results['black_swan_impact_pct']}%")
        print(f"   🔥 Volatility Spike Impact: {stress_results['high_volatility_impact_pct']}%")
        
        # Save Full Report
        full_report = {
            "base_metrics": metrics,
            "monte_carlo": mc_results,
            "stress_test": stress_results
        }
        
        with open("validation_report.json", "w") as f:
            json.dump(full_report, f, indent=2)
        print("\n💾 Full Report saved to validation_report.json")
        
    else:
        print("⚠️  Not enough trades for Monte Carlo.")

if __name__ == "__main__":
    main()
