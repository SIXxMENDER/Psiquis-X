import pandas as pd
import numpy as np
import pandas_ta as ta

# --- PARAMETERS ARE INJECTED BY OPTIMIZER ---
# ADX_PERIOD
# ADX_REGIME_THRESHOLD
# TREND_EMA_PERIOD
# RANGE_RSI_PERIOD
# RANGE_RSI_OB
# RANGE_RSI_OS
# RANGE_BB_LENGTH
# RANGE_BB_STD
# TREND_SL_ATR
# TREND_TP_ATR
# RANGE_SL_ATR
# RANGE_TP_ATR

def robust_rename_ta_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_to_rename = {}
    
    # Access injected globals
    adx_per = int(globals().get('ADX_PERIOD', 14))
    trend_ema = int(globals().get('TREND_EMA_PERIOD', 50))
    rsi_per = int(globals().get('RANGE_RSI_PERIOD', 14))
    bb_len = int(globals().get('RANGE_BB_LENGTH', 20))
    bb_std = float(globals().get('RANGE_BB_STD', 2.0))
    atr_per = 14 # Fixed for risk calc
    
    for col in df.columns:
        if col.startswith(f'ADX_{adx_per}'): cols_to_rename[col] = 'adx'
        elif col.startswith(f'EMA_{trend_ema}'): cols_to_rename[col] = 'ema_trend'
        elif col.startswith(f'RSI_{rsi_per}'): cols_to_rename[col] = 'rsi'
        elif col.startswith(f'ATRr_{atr_per}'): cols_to_rename[col] = 'atr'
        elif col.startswith(f'BBL_{bb_len}'): cols_to_rename[col] = 'bb_lower'
        elif col.startswith(f'BBU_{bb_len}'): cols_to_rename[col] = 'bb_upper'
        
    df.rename(columns=cols_to_rename, inplace=True)
    return df

def generar_senales(df: pd.DataFrame) -> pd.DataFrame:
    # Globals
    adx_per = int(globals().get('ADX_PERIOD', 14))
    adx_thresh = float(globals().get('ADX_REGIME_THRESHOLD', 25))
    trend_ema = int(globals().get('TREND_EMA_PERIOD', 50))
    rsi_per = int(globals().get('RANGE_RSI_PERIOD', 14))
    rsi_ob = float(globals().get('RANGE_RSI_OB', 70))
    rsi_os = float(globals().get('RANGE_RSI_OS', 30))
    bb_len = int(globals().get('RANGE_BB_LENGTH', 20))
    bb_std = float(globals().get('RANGE_BB_STD', 2.0))
    
    trend_sl = float(globals().get('TREND_SL_ATR', 2.0))
    trend_tp = float(globals().get('TREND_TP_ATR', 4.0))
    range_sl = float(globals().get('RANGE_SL_ATR', 1.5))
    range_tp = float(globals().get('RANGE_TP_ATR', 2.0))

    # 1. Calculate Indicators
    df.ta.adx(length=adx_per, append=True)
    df.ta.ema(length=trend_ema, append=True)
    df.ta.rsi(length=rsi_per, append=True)
    df.ta.bbands(length=bb_len, std=bb_std, append=True)
    df.ta.atr(length=14, append=True)
    
    df = robust_rename_ta_columns(df)
    df.dropna(inplace=True)
    
    original_index = df.index
    df.reset_index(drop=True, inplace=True)
    
    # 2. State Loop
    signals = np.zeros(len(df), dtype=int)
    stop_losses = np.full(len(df), np.nan)
    take_profits = np.full(len(df), np.nan)
    regime_arr = np.zeros(len(df), dtype=int) # 1=Trend, 0=Range
    
    position = 0
    current_sl = 0.0
    current_tp = 0.0
    
    for i in range(1, len(df)):
        atr = df['atr'].iloc[i]
        close = df['close'].iloc[i]
        high = df['high'].iloc[i]
        low = df['low'].iloc[i]
        
        # Determine Regime
        is_trend_regime = df['adx'].iloc[i] > adx_thresh
        regime_arr[i] = 1 if is_trend_regime else 0
        
        # --- EXIT LOGIC ---
        if position == 1:
            if low <= current_sl or high >= current_tp:
                position = 0
        elif position == -1:
            if high >= current_sl or low <= current_tp:
                position = 0
                
        # --- ENTRY LOGIC ---
        if position == 0:
            if is_trend_regime:
                # TREND MODE: Breakout / Trend Following
                # Long: Close > EMA
                if close > df['ema_trend'].iloc[i]:
                    signals[i] = 1
                    position = 1
                    current_sl = close - (atr * trend_sl)
                    current_tp = close + (atr * trend_tp)
                    stop_losses[i] = current_sl
                    take_profits[i] = current_tp
                # Short: Close < EMA
                elif close < df['ema_trend'].iloc[i]:
                    signals[i] = -1
                    position = -1
                    current_sl = close + (atr * trend_sl)
                    current_tp = close - (atr * trend_tp)
                    stop_losses[i] = current_sl
                    take_profits[i] = current_tp
                    
            else:
                # RANGE MODE: Mean Reversion
                # Long: RSI < OS & Close < BB Lower
                if df['rsi'].iloc[i] < rsi_os and close < df['bb_lower'].iloc[i]:
                    signals[i] = 1
                    position = 1
                    current_sl = close - (atr * range_sl)
                    current_tp = close + (atr * range_tp)
                    stop_losses[i] = current_sl
                    take_profits[i] = current_tp
                # Short: RSI > OB & Close > BB Upper
                elif df['rsi'].iloc[i] > rsi_ob and close > df['bb_upper'].iloc[i]:
                    signals[i] = -1
                    position = -1
                    current_sl = close + (atr * range_sl)
                    current_tp = close - (atr * range_tp)
                    stop_losses[i] = current_sl
                    take_profits[i] = current_tp

    df['signal'] = signals
    df['stop_loss'] = stop_losses
    df['take_profit'] = take_profits
    df['regime'] = regime_arr
    df['leverage'] = 1.0 # Keep simple for now
    
    df.set_index(original_index, inplace=True)
    return df
