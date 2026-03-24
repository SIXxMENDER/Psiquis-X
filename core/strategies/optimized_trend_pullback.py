import pandas as pd
import numpy as np
import pandas_ta as ta

# --- OPTIMIZED PARAMETERS ---
REGIME_SMA_PERIOD = 174
PULLBACK_SMA_PERIOD = 24
ADX_PERIOD = 16
ADX_ENTRY_THRESHOLD = 22
RSI_PERIOD = 11
RSI_BULLISH_ZONE = 63
RSI_BEARISH_ZONE = 42
ATR_PERIOD_RISK = 29
ATR_SL_MULTIPLIER = 1.88462
ATR_TP_MULTIPLIER = 2.78991
LEVERAGE_MAX = 1.8146
LONG_FUNDING_THRESHOLD = 0.00019
SHORT_FUNDING_THRESHOLD = -5e-05

import pandas as pd
import numpy as np
import pandas_ta as ta

# --- PARAMETERS ARE INJECTED BY OPTIMIZER ---
# REGIME_SMA_PERIOD
# PULLBACK_SMA_PERIOD
# ADX_PERIOD
# ADX_ENTRY_THRESHOLD
# RSI_PERIOD
# RSI_BULLISH_ZONE
# RSI_BEARISH_ZONE
# ATR_PERIOD_RISK
# ATR_SL_MULTIPLIER
# ATR_TP_MULTIPLIER
# LEVERAGE_MIN
# LEVERAGE_MAX
# LEVERAGE_ATR_LOOKBACK
# LONG_FUNDING_THRESHOLD
# SHORT_FUNDING_THRESHOLD

def robust_rename_ta_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renombra columnas generadas por pandas_ta de forma robusta usando startswith.
    Adaptado para SMAs, ADX, ATR y RSI.
    """
    cols_to_rename = {}
    
    # Access injected globals
    regime_sma = int(globals().get('REGIME_SMA_PERIOD', 200))
    pullback_sma = int(globals().get('PULLBACK_SMA_PERIOD', 20))
    adx_per = int(globals().get('ADX_PERIOD', 14))
    atr_per = int(globals().get('ATR_PERIOD_RISK', 14))
    rsi_per = int(globals().get('RSI_PERIOD', 14))
    
    for col in df.columns:
        # SMA Lenta (Régimen)
        if col.startswith(f'SMA_{regime_sma}'):
            cols_to_rename[col] = 'sma_slow'
        # SMA Rápida (Pullback)
        elif col.startswith(f'SMA_{pullback_sma}'):
            cols_to_rename[col] = 'sma_fast'
        # ADX
        elif col.startswith(f'ADX_{adx_per}'):
            cols_to_rename[col] = 'adx'
        # ATR para Riesgo
        elif col.startswith(f'ATRr_{atr_per}'):
            cols_to_rename[col] = 'atr'
        # RSI
        elif col.startswith(f'RSI_{rsi_per}'):
            cols_to_rename[col] = 'rsi'

    df.rename(columns=cols_to_rename, inplace=True)
    return df

def generar_senales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera señales para la estrategia "Trend-Pullback with Dynamic Risk & Funding".
    """
    # Access injected globals
    regime_sma = int(globals().get('REGIME_SMA_PERIOD', 200))
    pullback_sma = int(globals().get('PULLBACK_SMA_PERIOD', 20))
    adx_per = int(globals().get('ADX_PERIOD', 14))
    atr_per = int(globals().get('ATR_PERIOD_RISK', 14))
    rsi_per = int(globals().get('RSI_PERIOD', 14))

    # --- 2. Cálculo de TODOS los Indicadores Necesarios ---
    df.ta.sma(length=regime_sma, append=True)
    df.ta.sma(length=pullback_sma, append=True)
    df.ta.adx(length=adx_per, append=True)
    df.ta.atr(length=atr_per, append=True)
    df.ta.rsi(length=rsi_per, append=True)
    
    df = robust_rename_ta_columns(df)
    
    # Manejo de NaNs iniciales
    df.dropna(inplace=True)
    # Guardamos el índice original y lo reseteamos para el bucle
    original_index = df.index
    df.reset_index(drop=True, inplace=True)

    # --- 3. Lógica de Apalancamiento Dinámico (Invertido a Volatilidad) ---
    # Access injected globals
    atr_lookback = int(globals().get('LEVERAGE_ATR_LOOKBACK', 50))
    lev_max = float(globals().get('LEVERAGE_MAX', 1.5))
    lev_min = float(globals().get('LEVERAGE_MIN', 1.0))
    
    atr_rolling_min = df['atr'].rolling(window=atr_lookback).min()
    atr_rolling_max = df['atr'].rolling(window=atr_lookback).max()
    atr_normalized = (df['atr'] - atr_rolling_min) / (atr_rolling_max - atr_rolling_min)
    atr_normalized = atr_normalized.clip(0, 1).fillna(0.5)
    df['leverage'] = lev_max - (atr_normalized * (lev_max - lev_min))
    
    # --- 4. Generación Vectorizada de Condiciones de Entrada ---
    
    # Condición 1: Filtro de Régimen Macro
    is_bullish_regime = df['close'] > df['sma_slow']
    is_bearish_regime = df['close'] < df['sma_slow']

    # Condición 2: Señal de Entrada (Pullback a la SMA rápida)
    price_pullback_to_support = df['low'] <= df['sma_fast']
    price_pullback_to_resistance = df['high'] >= df['sma_fast']

    # Access injected globals for logic
    adx_thresh = float(globals().get('ADX_ENTRY_THRESHOLD', 25))
    rsi_bull = float(globals().get('RSI_BULLISH_ZONE', 55))
    rsi_bear = float(globals().get('RSI_BEARISH_ZONE', 45))
    fund_long = float(globals().get('LONG_FUNDING_THRESHOLD', 0.0001))
    fund_short = float(globals().get('SHORT_FUNDING_THRESHOLD', -0.0001))
    sl_mult = float(globals().get('ATR_SL_MULTIPLIER', 2.0))
    tp_mult = float(globals().get('ATR_TP_MULTIPLIER', 3.0))

    # Condición 3: Filtro de Fortaleza de Tendencia
    trend_is_strong = df['adx'] > adx_thresh

    # Condición 4: Filtro de Confirmación de Momentum
    rsi_confirms_bullish = df['rsi'] > rsi_bull
    rsi_confirms_bearish = df['rsi'] < rsi_bear

    # Condición 5: Filtro de Funding Rate
    funding_favorable_long = df['funding_rate'] <= fund_long
    funding_favorable_short = df['funding_rate'] >= fund_short

    # Combinamos condiciones para obtener "candidatos" de entrada de alta probabilidad
    long_entry_candidate = (
        is_bullish_regime & 
        price_pullback_to_support & 
        trend_is_strong & 
        rsi_confirms_bullish &
        funding_favorable_long
    )
    short_entry_candidate = (
        is_bearish_regime & 
        price_pullback_to_resistance & 
        trend_is_strong &
        rsi_confirms_bearish &
        funding_favorable_short
    )

    # --- 5. Simulación de Posiciones con Gestión de Riesgo (Bucle de Estado) ---
    signals = np.zeros(len(df), dtype=int)
    stop_losses = np.full(len(df), np.nan)
    take_profits = np.full(len(df), np.nan)
    
    position = 0  # 0: neutral, 1: long, -1: short
    current_sl = 0.0
    current_tp = 0.0

    for i in range(1, len(df)): # Empezamos en 1 para poder mirar la vela anterior si es necesario
        # --- Lógica de SALIDA de Posición (Prioridad 1: proteger capital) ---
        if position == 1:  # En posición LARGA
            # Salida 1: SL o TP alcanzados
            if df['low'].iloc[i] <= current_sl or df['high'].iloc[i] >= current_tp:
                position = 0
            # Salida 2: El régimen de mercado ha cambiado (CRÍTICO)
            elif not is_bullish_regime.iloc[i]:
                position = 0
        
        elif position == -1:  # En posición CORTA
            # Salida 1: SL o TP alcanzados
            if df['high'].iloc[i] >= current_sl or df['low'].iloc[i] <= current_tp:
                position = 0
            # Salida 2: El régimen de mercado ha cambiado (CRÍTICO)
            elif not is_bearish_regime.iloc[i]:
                position = 0

        # --- Lógica de ENTRADA a Posición (Prioridad 2) ---
        # Solo podemos entrar si estamos neutrales y en la vela anterior no estábamos en una posición
        if position == 0 and signals[i-1] == 0:
            atr_value = df['atr'].iloc[i]
            if pd.isna(atr_value) or atr_value == 0: continue

            if long_entry_candidate.iloc[i]:
                signals[i] = 1
                position = 1
                # Usamos el precio de cierre como entrada teórica
                entry_price = df['close'].iloc[i] 
                current_sl = entry_price - (atr_value * sl_mult)
                current_tp = entry_price + (atr_value * tp_mult)
                stop_losses[i] = current_sl
                take_profits[i] = current_tp
                
            elif short_entry_candidate.iloc[i]:
                signals[i] = -1
                position = -1
                entry_price = df['close'].iloc[i]
                current_sl = entry_price + (atr_value * sl_mult)
                current_tp = entry_price - (atr_value * tp_mult)
                stop_losses[i] = current_sl
                take_profits[i] = current_tp
    
    df['signal'] = signals
    df['stop_loss'] = stop_losses
    df['take_profit'] = take_profits
    
    # El apalancamiento solo se aplica en la vela de entrada, de lo contrario es 1.0
    df['leverage'] = df['leverage'].where(df['signal'] != 0, 1.0)
    
    # Restaurar el índice de timestamp original
    df.set_index(original_index, inplace=True)
    
    return df
