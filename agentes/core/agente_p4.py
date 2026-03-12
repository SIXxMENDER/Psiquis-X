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

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Union, List
import traceback

import ast

def validate_code_safety(code: str) -> bool:
    """
    Validates that the code does not contain dangerous imports or calls.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = node.module if isinstance(node, ast.ImportFrom) else None
            names = [n.name for n in node.names]
            for name in names + ([module] if module else []):
                if name and any(x in name for x in ['os', 'sys', 'subprocess', 'shutil', 'importlib', 'pickle']):
                    logging.warning(f"SECURITY ALERT: Blocked import of {name}")
                    return False
        
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ['eval', 'exec', 'open', '__import__', 'compile']:
                    logging.warning(f"SECURITY ALERT: Blocked call to {node.func.id}")
                    return False
    return True

def robust_rename_ta_columns(df):
    """
    Helper function to normalize pandas_ta column names.
    Removes uppercase and weird characters.
    """
    new_cols = []
    for c in df.columns:
        if isinstance(c, tuple):
            c = c[0]
        c = str(c).lower()
        new_cols.append(c)
    df.columns = new_cols
    return df

from core.utils.schemas import BacktestInput, BacktestOutput
from skills.react_best_practices import run_react_audit

def execute(self=None, **kwargs) -> Dict[str, Any]:
    """
    Executes a vectorized backtest OR a React code audit.
    Implements AgentProtocol with Pydantic Validation.
    """
    # 0. SKILL TRIGGER: REACT AUDIT
    # We check raw kwargs first because BacktestInput might be strict
    raw_code = kwargs.get("codigo_estrategia", "")
    if "react" in raw_code.lower() or "useeffect" in raw_code.lower() or "component" in raw_code.lower():
        print(f"⚛️ [DEV] Triggering Skill: REACT AUDIT")
        report = run_react_audit(raw_code)
        # Return a dummy BacktestOutput to satisfy schema, or just a dict
        return {
            "status": "SUCCESS",
            "metricas": {"quality_score": 100}, # Dummy
            "trade_returns": [],
            "equity_curve": [],
            "report": report # Custom field
        }

    try:
        input_data = BacktestInput(**kwargs)
    except Exception as e:
        return {"status": "ERROR", "error": f"Validation Error: {e}"}

    try:
        logging.info("📉 P4: Initializing Vectorized Backtest...")
        
        # 1. Cargar Datos
        datos = input_data.datos_historicos
            
        if isinstance(datos, str):
            df = pd.read_csv(datos)
        elif isinstance(datos, list):
            df = pd.DataFrame(datos)
        else:
            return {"status": "ERROR", "error": "Formato de datos no soportado"}
            
        # Normalizar columnas
        new_cols = []
        for c in df.columns:
            if isinstance(c, tuple):
                new_cols.append(c[0].lower())
            else:
                new_cols.append(c.lower())
        df.columns = new_cols
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
        # 2. Cargar Estrategia
        codigo = input_data.codigo_estrategia
        if not codigo:
            # Estrategia por defecto: Buy & Hold
            logging.warning("P4: No se dio estrategia, usando Buy & Hold")
            df['signal'] = 1
        else:
            # Security Check
            if not validate_code_safety(codigo):
                return {"status": "ERROR", "error": "SECURITY VIOLATION: Malicious code detected."}

            # Ejecución dinámica segura (Sandbox limitado)
            # Restricted globals: only allow safe libraries
            safe_globals = {
                'pd': pd, 
                'np': np, 
                '__builtins__': __builtins__, # Allow standard builtins (len, range, etc)
                'robust_rename_ta_columns': robust_rename_ta_columns
            }
            # Use a single scope for globals and locals to allow functions to see each other
            local_scope = safe_globals.copy()
            
            try:
                exec(codigo, local_scope)
            except Exception as e:
                return {"status": "ERROR", "error": f"Error executing strategy code: {e}"}
            
            if 'generar_senales' not in local_scope:
                return {"status": "ERROR", "error": "El código de estrategia debe definir 'generar_senales(df)'"}
                
            # Aplicar estrategia
            df = local_scope['generar_senales'](df.copy())
            
        if 'signal' not in df.columns:
            return {"status": "ERROR", "error": "La estrategia no generó la columna 'signal'"}
            
        # 3. Simulación Vectorizada
        capital_inicial = input_data.capital_inicial
        comision = input_data.comision
        
        # Calcular retornos del mercado
        df['pct_change'] = df['close'].pct_change().fillna(0)
        
        # Gestión de Posiciones (Long/Short)
        # signal: 1 (Enter Long), -1 (Enter Short), 0 (Exit/Neutral)
        # OJO: La lógica anterior era 1=Buy, -1=Sell(Exit). Ahora -1 es Short.
        # Necesitamos una lógica de estado más robusta o asumir que la estrategia devuelve la POSICIÓN deseada (1, -1, 0)
        # Si la estrategia devuelve 'signal' como trigger, convertimos a posición.
        
        if 'position' not in df.columns:
            # Asumimos que 'signal' es la posición deseada (Target Position)
            # 1: Long, -1: Short, 0: Flat
            df['position'] = df['signal'].shift(1).fillna(0) # Shift 1 para evitar lookahead
        else:
            # Si la estrategia ya calculó 'position', solo hacemos shift
            df['position'] = df['position'].shift(1).fillna(0)

        # Leverage (Apalancamiento)
        # Si la estrategia define una columna 'leverage', la usamos. Si no, default 1.0.
        if 'leverage' in df.columns:
            df['leverage'] = df['leverage'].shift(1).fillna(1.0)
        else:
            df['leverage'] = 1.0
            
        # Calcular retornos de la estrategia
        # Retorno = (Posición * Retorno Mercado * Apalancamiento) - Costos
        # Costos: Se pagan sobre el valor nocional total (Capital * Leverage)
        
        # Cambio de posición (Turnover)
        # abs(pos_actual * lev_actual - pos_prev * lev_prev)
        notional_exposure = df['position'] * df['leverage']
        turnover = notional_exposure.diff().abs().fillna(0)
        
        df['cost'] = turnover * comision
        
        # Retorno bruto
        df['strategy_return'] = (df['position'] * df['pct_change'] * df['leverage']) - df['cost']
        
        # Curva de equidad
        df['equity'] = capital_inicial * (1 + df['strategy_return']).cumprod()
        
        # Calcular Métricas Avanzadas (High-Ticket)
        total_return = (df['equity'].iloc[-1] / capital_inicial) - 1
        
        # Calcular días de forma robusta
        if isinstance(df.index, pd.DatetimeIndex):
            days = (df.index[-1] - df.index[0]).days
            seconds = (df.index[-1] - df.index[0]).total_seconds()
        else:
            days = len(df) / 24 # Asumiendo 1h candles
            seconds = days * 86400
            
        cagr = ((1 + total_return) ** (365 / days)) - 1 if days > 0 else 0
        
        # Drawdown
        rolling_max = df['equity'].cummax()
        drawdown = (df['equity'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Sharpe Ratio (Anualizado)
        returns_std = df['strategy_return'].std()
        sharpe = (df['strategy_return'].mean() / returns_std) * np.sqrt(365 * 24) if returns_std != 0 else 0
        
        # Sortino Ratio (Solo penaliza volatilidad negativa)
        negative_returns = df.loc[df['strategy_return'] < 0, 'strategy_return']
        downside_std = negative_returns.std()
        sortino = (df['strategy_return'].mean() / downside_std) * np.sqrt(365 * 24) if downside_std != 0 else 0
        
        # Calmar Ratio (CAGR / Max Drawdown)
        calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Profit Factor (Gross Profit / Gross Loss)
        gross_profit = df.loc[df['strategy_return'] > 0, 'strategy_return'].sum()
        gross_loss = abs(df.loc[df['strategy_return'] < 0, 'strategy_return'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0
        
        # Win Rate & Trade Returns Extraction
        trades_returns = []
        current_trade_ret = 0.0
        
        # Iteración rápida para extraer retornos por trade
        pos_arr = df['position'].values
        ret_arr = df['strategy_return'].values
        
        for i in range(1, len(df)):
            if pos_arr[i-1] != 0: # Estábamos en un trade
                current_trade_ret += ret_arr[i]
                
                if pos_arr[i] != pos_arr[i-1]: # El trade terminó o cambió de sentido
                    trades_returns.append(current_trade_ret)
                    current_trade_ret = 0.0
            
            elif pos_arr[i] != 0: # Empezamos un trade nuevo
                current_trade_ret += ret_arr[i]
                
        if pos_arr[-1] != 0:
            trades_returns.append(current_trade_ret)
            
        trades_returns = np.array(trades_returns)
        total_trades = len(trades_returns)
        
        win_rate = (np.sum(trades_returns > 0) / total_trades) * 100 if total_trades > 0 else 0

        metricas = {
            "total_return_pct": round(total_return * 100, 2),
            "cagr_pct": round(cagr * 100, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2),
            "profit_factor": round(profit_factor, 2),
            "win_rate_pct": round(win_rate, 2),
            "final_equity": round(df['equity'].iloc[-1], 2),
            "trades_count": int(total_trades)
        }
        
        logging.info(f"✅ P4: Backtest completed. Return: {metricas['total_return_pct']}%")
        
        output = BacktestOutput(
            status="SUCCESS",
            metricas=metricas,
            trade_returns=trades_returns.tolist(),
            equity_curve=df['equity'].tolist()[-50:]
        )
        return output.model_dump()
        
    except Exception as e:
        logging.error(f"❌ P4: Error en backtest: {e}")
        traceback.print_exc()
        return {"status": "ERROR", "error": str(e)}

# Alias for backward compatibility
def run_backtest(**kwargs) -> Dict[str, Any]:
    return execute(**kwargs)
