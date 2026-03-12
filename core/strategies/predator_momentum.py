import pandas as pd
import pandas_ta as ta

def generar_senales(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Estrategia Predator Momentum v5.0 (Ported from MQL5)
    
    Parámetros por defecto (se pueden sobreescribir con 'params'):
    - EMA_Trend_Period: 200
    - EMA_Pullback_Period: 50
    - EMA_Trigger_Period: 3
    - ADX_Period: 14
    - ADX_Threshold: 18
    - ATR_Period: 14
    - ATR_SL_Multiplier: 2.0
    - ATR_TS_Multiplier: 2.5
    """
    if params is None:
        params = {}
        
    # 1. Extraer parámetros
    ema_trend_p = params.get("EMA_Trend_Period", 200)
    ema_pullback_p = params.get("EMA_Pullback_Period", 50)
    ema_trigger_p = params.get("EMA_Trigger_Period", 3)
    adx_p = params.get("ADX_Period", 14)
    adx_thresh = params.get("ADX_Threshold", 18)
    atr_p = params.get("ATR_Period", 14)
    
    # 2. Calcular Indicadores
    # Asegurar que el índice es datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    df['ema_trend'] = ta.ema(df['close'], length=ema_trend_p)
    df['ema_pullback'] = ta.ema(df['close'], length=ema_pullback_p)
    df['ema_trigger'] = ta.ema(df['close'], length=ema_trigger_p)
    
    # ADX retorna 3 columnas: ADX_14, DMP_14, DMN_14. Tomamos la primera.
    adx_df = ta.adx(df['high'], df['low'], df['close'], length=adx_p)
    if adx_df is not None and not adx_df.empty:
        df['adx'] = adx_df.iloc[:, 0] # La columna ADX suele ser la primera
    else:
        df['adx'] = 0
        
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=atr_p)
    
    # 3. Lógica de Trading (Vectorizada)
    
    # Inicializar señales
    df['signal'] = 0
    
    # Condiciones
    # A. Tendencia: Precio > EMA 200
    trend_ok = df['close'] > df['ema_trend']
    
    # B. Fuerza: ADX > Umbral
    strength_ok = df['adx'] > adx_thresh
    
    # C. Pullback (Acecho): Low <= EMA 50
    # En MQL5 esto es stateful ("pullback_confirmed"). 
    # En vectorizado, marcamos las velas donde ocurre el toque.
    touched_pullback = df['low'] <= df['ema_pullback']
    
    # Para simular el estado "pullback_confirmed", podemos propagar el evento hacia adelante
    # hasta que ocurra un cruce o se rompa la tendencia.
    # Simplificación vectorizada: Buscamos cruces que ocurran DESPUÉS de un toque reciente (ej. últimas 5 velas)
    # O mejor: Definimos la señal de entrada exacta.
    
    # D. Gatillo: EMA 3 cruza ARRIBA de EMA 50
    # Cruce alcista: (EMA3_prev < EMA50_prev) AND (EMA3_curr > EMA50_curr)
    cross_up = (df['ema_trigger'].shift(1) < df['ema_pullback'].shift(1)) & \
               (df['ema_trigger'] > df['ema_pullback'])
               
    # E. Combinación:
    # Entrada = CrossUp AND TrendOK AND StrengthOK AND (Recientemente tocó Pullback??)
    # La lógica original de MQL5 es muy específica con el estado.
    # Vamos a aproximarla: Si hay CrossUp Y TrendOK Y StrengthOK, entramos.
    # El "pullback_confirmed" de MQL5 se activa cuando Low <= EMA50 y se desactiva al entrar.
    # Dado que el cruce EMA3 > EMA50 implica que el precio estaba abajo y subió, 
    # el pullback está implícito en la naturaleza del cruce de recuperación.
    
    entry_signal = cross_up & trend_ok & strength_ok
    
    # Asignar señal de compra (1)
    df.loc[entry_signal, 'signal'] = 1
    
    # Salidas (Trailing Stop)
    # En un backtest vectorizado simple (P4 actual), no simulamos trailing stop tick-a-tick.
    # P4 cierra la posición cuando la señal cambia o se invierte.
    # Para simular salidas, necesitaríamos un motor de eventos (loop).
    # Por ahora, P4 asume que mantenemos la posición hasta la siguiente señal contraria o fin.
    # Vamos a dejarlo así para la optimización de ENTRADAS, que es lo crítico.
    
    # Si quisiéramos ser más precisos con P4, deberíamos generar señal de VENTA (-1) cuando toca el SL.
    # Pero eso requiere iterar.
    
    return df
