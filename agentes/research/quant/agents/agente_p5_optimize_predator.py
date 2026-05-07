# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Psiquis-X: Enterprise Multi-Agent Framework
# Proprietary Software - All Rights Reserved
# Copyright (c) 2026 SIXxMENDER & Bosniack-94
# -----------------------------------------------------------------------------
# WARNING: This source code is proprietary and confidential. 
# Unauthorized copying, distribution, or use via any medium is strictly 
# prohibited. This code is provided solely for authorized technical review 
# and evaluation purposes.
# -----------------------------------------------------------------------------

import sys
import os
import random
import json
import pandas as pd
import numpy as np
import copy
import yfinance as yf
sys.path.append(os.getcwd())
from agentes import agente_p4

# --- CONFIGURATION ---
POPULATION_SIZE = 30
GENERATIONS = 10
MUTATION_RATE = 0.2
ELITISM = 3

# Search Space (Regime-Adaptive Parameters)
PARAM_RANGES = {
    'ADX_PERIOD': (7, 21, int),
    'ADX_REGIME_THRESHOLD': (15, 40, float), # Critical: Defines when to switch
    'TREND_EMA_PERIOD': (20, 200, int),
    'RANGE_RSI_PERIOD': (7, 14, int),
    'RANGE_RSI_OB': (60, 80, float),
    'RANGE_RSI_OS': (20, 40, float),
    'RANGE_BB_LENGTH': (10, 30, int),
    'RANGE_BB_STD': (1.5, 2.5, float),
    'TREND_SL_ATR': (1.5, 4.0, float), # Trend needs room
    'TREND_TP_ATR': (3.0, 8.0, float), # Trend needs big targets
    'RANGE_SL_ATR': (1.0, 2.0, float), # Range needs tight stops
    'RANGE_TP_ATR': (1.0, 3.0, float)  # Range needs quick profits
}

STRATEGY_TEMPLATE_PATH = "strategies/regime_adaptive_v1.py"
OUTPUT_PATH = "strategies/optimized_regime_adaptive.py"

def load_data():
    print("Loading market data for optimization...")
    TICKER = "BTC-USD"
    PERIOD = "365d" # 1 Year
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
    
    if 'funding_rate' not in df.columns:
        df['funding_rate'] = np.random.normal(0, 0.0001, len(df))
        
    return df.to_dict('records')

def generate_individual():
    individual = {}
    for param, (min_val, max_val, type_) in PARAM_RANGES.items():
        if type_ == int:
            individual[param] = random.randint(min_val, max_val)
        else:
            individual[param] = round(random.uniform(min_val, max_val), 5)
    return individual

def construct_strategy_code(base_code, params):
    param_block = "# --- OPTIMIZED PARAMETERS ---\n"
    for param, value in params.items():
        param_block += f"{param} = {value}\n"
    
    # Add imports if missing in base code (template has no imports)
    imports = "import pandas as pd\nimport numpy as np\nimport pandas_ta as ta\n\n"
    
    return imports + param_block + "\n" + base_code

def evaluate(individual, data_records, base_code):
    # Debug: Check type
    if not isinstance(individual, dict):
        print(f"❌ Error: Individual is not a dict: {type(individual)}")
        return -999, {}

    try:
        strategy_code = construct_strategy_code(base_code, individual)
        
        result = agente_p4.ejecutar_backtest(
            datos_historicos=data_records,
            codigo_estrategia=strategy_code
        )
        
        if result['status'] != 'SUCCESS':
            return -999, {}
            
        metrics = result['metricas']
        sharpe = metrics.get('sharpe_ratio', -999)
        sortino = metrics.get('sortino_ratio', 0)
        calmar = metrics.get('calmar_ratio', 0)
        profit_factor = metrics.get('profit_factor', 0)
        cagr = metrics.get('cagr_pct', 0)
        dd = abs(metrics.get('max_drawdown_pct', 100))
        trades = metrics.get('trades_count', 0)
        
        # --- HIGH-TICKET FITNESS FUNCTION ---
        
        # 1. Hard Constraints
        if trades < 40: return -999, metrics # Need statistical significance
        if dd > 30: return -999, metrics # Max risk
        
        # 2. Weighted Score
        score = 0
        score += min(calmar, 8.0) * 2.0 
        score += min(sortino, 5.0) * 1.5
        score += min(profit_factor, 4.0) * 1.0
        
        if cagr > 85: score *= 1.2
        if dd > 20: score *= 0.8
        
        return score, metrics
        
    except Exception as e:
        print(f"Eval Error: {e}")
        return -999, {}

def crossover(parent1, parent2):
    child = {}
    for param in PARAM_RANGES:
        if random.random() > 0.5:
            child[param] = parent1[param]
        else:
            child[param] = parent2[param]
    return child

def mutate(individual):
    mutated = copy.deepcopy(individual)
    for param, (min_val, max_val, type_) in PARAM_RANGES.items():
        if random.random() < MUTATION_RATE:
            if type_ == int:
                mutated[param] = random.randint(min_val, max_val)
            else:
                mutated[param] = round(random.uniform(min_val, max_val), 5)
    return mutated

import asyncio
from concurrent.futures import ProcessPoolExecutor

def optimize_strategy_sync():
    """Synchronous CPU-bound optimization task."""
    print("🧬 [P5] Starting Genetic Optimization (CPU-Bound Process)...")
    
    data = load_data()
    print(f"   Loaded {len(data)} candles.")
    
    with open(STRATEGY_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        base_code = f.read()
        
    population = [generate_individual() for _ in range(POPULATION_SIZE)]
    
    best_fitness = -999
    best_individual = None
    best_metrics = None
    
    for gen in range(GENERATIONS):
        print(f"\n🧬 Generation {gen+1}/{GENERATIONS}")
        
        fitness_scores = []
        for i, ind in enumerate(population):
            fit, metrics = evaluate(ind, data, base_code)
            fitness_scores.append((ind, fit, metrics))
            
            if fit > best_fitness:
                best_fitness = fit
                best_individual = ind
                best_metrics = metrics
                print(f"   🚀 New Best! Sharpe: {metrics.get('sharpe_ratio'):.2f} | CAGR: {metrics.get('cagr_pct'):.2f}% | DD: {metrics.get('max_drawdown_pct'):.2f}%")
        
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        new_population = [x[0] for x in fitness_scores[:ELITISM]]
        
        while len(new_population) < POPULATION_SIZE:
            p1 = random.choice(fitness_scores[:10])[0]
            p2 = random.choice(fitness_scores[:10])[0]
            child = crossover(p1, p2)
            child = mutate(child)
            new_population.append(child)
            
        population = new_population
        
    print("\n🏆 Optimization Complete!")
    if best_individual:
        print("Best Parameters:", json.dumps(best_individual, indent=2))
        print("Best Metrics:", json.dumps(best_metrics, indent=2))
        
        final_code = construct_strategy_code(base_code, best_individual)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(final_code)
        print(f"💾 Optimized strategy saved to: {OUTPUT_PATH}")
        return best_individual
    else:
        print("❌ Optimization failed to find any valid strategy.")
        return None

async def run_optimization_async():
    """Async wrapper to run optimization in a separate process."""
    print("⏳ [P5] Offloading optimization to ProcessPoolExecutor...")
    loop = asyncio.get_running_loop()
    
    # Run the synchronous function in a separate process
    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, optimize_strategy_sync)
        
    return result

if __name__ == "__main__":
    asyncio.run(run_optimization_async())
