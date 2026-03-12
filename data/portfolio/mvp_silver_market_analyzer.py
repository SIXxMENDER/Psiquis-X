# -*- coding: utf-8 -*-
"""
Script de nivel profesional (Silver Tier) para conectar a Binance,
descargar datos OHLCV de BTC/USDT y calcular los indicadores RSI y MACD.

Este script es autónomo y está listo para ser ejecutado.

Dependencias externas:
- ccxt: para interactuar con la API de Binance.
- pandas: para la manipulación y análisis de datos.
- pandas-ta: para el cálculo de indicadores técnicos.

Para instalar las dependencias, ejecuta en tu terminal:
pip install ccxt pandas pandas-ta
"""

# --- Imports Requeridos ---
import sys
import ccxt
import pandas as pd
import pandas_ta as ta  # Librería especializada en indicadores técnicos

# --- Constantes de Configuración ---
# Puedes modificar estos valores para analizar otros pares o timeframes.
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1h'  # Timeframe (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
DATA_LIMIT = 200  # Número de velas a descargar (suficiente para RSI(14) y MACD)


def fetch_ohlcv(symbol: str, timeframe: str, limit: int) -> list | None:
    """
    Conecta a Binance usando ccxt y descarga los datos OHLCV (Open, High, Low, Close, Volume).

    Args:
        symbol (str): El par de trading (ej. 'BTC/USDT').
        timeframe (str): El intervalo de tiempo de las velas (ej. '1h').
        limit (int): El número de velas a descargar.

    Returns:
        list | None: Una lista de listas con los datos OHLCV, o None si ocurre un error.
    """
    print(f"[*] Conectando a Binance para descargar {limit} velas de {symbol} en timeframe {timeframe}...")
    try:
        # Inicializa el exchange (no se necesitan claves de API para datos públicos)
        exchange = ccxt.binance()

        # Comprobación de que el exchange soporta la funcionalidad requerida
        if not exchange.has['fetchOHLCV']:
            print(f"[!] Error: El exchange {exchange.id} no soporta la descarga de datos OHLCV.", file=sys.stderr)
            return None

        # Descarga los datos OHLCV
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        
        if not ohlcv:
            print(f"[!] No se recibieron datos para {symbol}. Verifica el símbolo y el timeframe.", file=sys.stderr)
            return None

        print("[+] Datos OHLCV descargados exitosamente.")
        return ohlcv

    except ccxt.NetworkError as e:
        print(f"[!] Error de red al conectar con Binance: {e}", file=sys.stderr)
        return None
    except ccxt.ExchangeError as e:
        print(f"[!] Error del exchange Binance (verifica el símbolo): {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[!] Ocurrió un error inesperado al descargar datos: {e}", file

# Auto-generated self-test
if __name__ == "__main__":
    try:
        resultado = ejecutar_paso()
        assert resultado.get('status') == 'SUCCESS', "El agente debe retornar status=SUCCESS"
        print("✅ Self-test passed")
        print(f"   Resultado: {resultado}")
    except Exception as e:
        print(f"❌ Self-test failed: {e}")
        import sys
        sys.exit(1)
