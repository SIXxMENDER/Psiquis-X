
# --- STRATEGY LOGIC ---
def generar_senales(df: pd.DataFrame) -> pd.DataFrame:
    # Helper to safely rename latest columns
    def rename_latest(df, prefix_map):
        # This assumes the indicators were just added and are at the end, 
        # or we scan all columns. Scanning all is safer.
        # But better: we know what we just added.
        pass

    # 1. Indicators
    
    # EMA
    cols_before = set(df.columns)
    df.ta.ema(length=int(EMA_TREND), append=True)
    new_cols = set(df.columns) - cols_before
    for col in new_cols:
        df.rename(columns={col: 'ema_trend'}, inplace=True)

    # BBANDS
    cols_before = set(df.columns)
    df.ta.bbands(length=int(BB_LENGTH), std=float(BB_STD), append=True)
    new_cols = set(df.columns) - cols_before
    for col in new_cols:
        if col.startswith('BBL'): df.rename(columns={col: 'bb_lower'}, inplace=True)
        elif col.startswith('BBM'): df.rename(columns={col: 'bb_middle'}, inplace=True)
        elif col.startswith('BBU'): df.rename(columns={col: 'bb_upper'}, inplace=True)

    # RSI
    cols_before = set(df.columns)
    df.ta.rsi(length=int(RSI_LENGTH), append=True)
    new_cols = set(df.columns) - cols_before
    for col in new_cols:
        df.rename(columns={col: 'rsi'}, inplace=True)

    # ATR
    cols_before = set(df.columns)
    df.ta.atr(length=int(ATR_LENGTH), append=True)
    new_cols = set(df.columns) - cols_before
    for col in new_cols:
        df.rename(columns={col: 'atr'}, inplace=True)

    # 2. Logic
    df['signal'] = 0
    df['leverage'] = 1.0
    
    # Ensure columns exist (fallback)
    if 'bb_lower' not in df.columns: return df
    
    # Vectorized Conditions
    long_cond = (
        (df['close'] < df['bb_lower']) & 
        (df['rsi'] < RSI_OS) & 
        (df['close'] > df['ema_trend']) &
        (df['funding_rate'] < FUNDING_THRESHOLD)
    )
    
    short_cond = (
        (df['close'] > df['bb_upper']) & 
        (df['rsi'] > RSI_OB) & 
        (df['close'] < df['ema_trend']) &
        (df['funding_rate'] > -FUNDING_THRESHOLD)
    )
    
    df.loc[long_cond, 'signal'] = 1
    df.loc[short_cond, 'signal'] = -1
    
    # 3. Dynamic Leverage
    mean_atr = df['atr'].rolling(100).mean()
    low_vol = df['atr'] < mean_atr
    df.loc[low_vol, 'leverage'] = 1.5
    df.loc[~low_vol, 'leverage'] = 1.0
    
    return df
