import os
import time
import logging
from enum import Enum
from typing import List, Dict, Optional, Any

import requests
import pandas as pd
import numpy as np

# --- Configuración del Logging ---
# Configura un logger para mostrar información detallada sobre las operaciones del bot.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Tipos y Enumeraciones para Claridad y Seguridad ---

class SenalTrading(Enum):
    """Enumeración para las señales de trading generadas por el análisis."""
    COMPRAR = "COMPRAR"
    VENDER = "VENDER"
    MANTENER = "MANTENER"

class Posicion(Enum):
    """Enumeración para el estado de la posición actual del bot."""
    NINGUNA = "NINGUNA"
    LONG = "LONG"  # Posición de compra

class SniperBot:
    """
    Una clase que representa un bot de trading simulado (SniperBot).
    
    Este bot utiliza una estrategia de cruce de medias móviles para identificar
    tendencias y ejecuta órdenes simuladas con gestión de riesgo (stop-loss).
    """

    def __init__(
        self,
        simbolo: str,
        periodo_corto: int = 12,
        periodo_largo: int = 26,
        porcentaje_stop_loss: float = 0.05,
        intervalo_datos_dias: int = 30
    ):
        """
        Inicializa el SniperBot.

        Args:
            simbolo (str): El símbolo del activo a operar (ej. 'BTC-USD').
            periodo_corto (int): Periodo para la media móvil simple (SMA) corta.
            periodo_largo (int): Periodo para la media móvil simple (SMA) larga.
            porcentaje_stop_loss (float): Porcentaje de pérdida máxima antes de vender (ej. 0.05 para 5%).
            intervalo_datos_dias (int): Número de días de datos históricos a obtener.
        """
        if not (0 < porcentaje_stop_loss < 1):
            raise ValueError("El porcentaje_stop_loss debe estar entre 0 y 1.")
            
        self.simbolo = simbolo
        self.periodo_corto = periodo_corto
        self.periodo_largo = periodo_largo
        self.porcentaje_stop_loss = porcentaje_stop_loss
        self.intervalo_datos_dias = intervalo_datos_dias
        
        # Mapeo de símbolos a IDs de CoinGecko para la API
        self.mapa_simbolos_coingecko: Dict[str, str] = {
            "BTC-USD": "bitcoin",
            "ETH-USD": "ethereum",
            "SOL-USD": "solana"
        }
        if simbolo not in self.mapa_simbolos_coingecko:
            raise ValueError(f"Símbolo '{simbolo}' no soportado. Soportados: {list(self.mapa_simbolos_coingecko.keys())}")
        
        # Estado del bot
        self.posicion: Posicion = Posicion.NINGUNA
        self.precio_entrada: float = 0.0
        self.historial_ordenes: List[Dict[str, Any]] = []
        
        logging.info(f"SniperBot inicializado para {self.simbolo} con SMA({self.periodo_corto}, {self.periodo_largo}) y Stop Loss del {self.porcentaje_stop_loss:.2%}.")

    def _obtener_datos_historicos(self) -> Optional[pd.DataFrame]:
        """
        Método privado para obtener datos históricos de precios desde la API de CoinGecko.
        
        Returns:
            Optional[pd.DataFrame]: Un DataFrame de pandas con 'timestamp' y 'price',
                                    o None si ocurre un error.
        """
        coingecko_id = self.mapa_simbolos_coingecko[self.simbolo]
        url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": str(self.intervalo_datos_dias),
            "interval": "daily"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # Lanza una excepción para códigos de error HTTP
            data = response.json()
            
            if 'prices' not in data or not data['prices']:
                logging.warning("La respuesta de la API no contiene datos de precios.")
                return None

            df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df

        except requests.exceptions.RequestException as e:
            logging.error(f"Error al conectar con la API de CoinGecko: {e}")
            return None
        except (KeyError, ValueError) as e:
            logging.error(f"Error al procesar los datos de la API: {e}")
            return None

    def analizar_tendencia(self, datos_historicos: pd.DataFrame) -> SenalTrading:
        """
        Analiza la tendencia del mercado usando un cruce de medias móviles simples (SMA).

        Un "cruce dorado" (SMA corta > SMA larga) es una señal de compra.
        Un "cruce de la muerte" (SMA corta < SMA larga) es una señal de venta.

        Args:
            datos_historicos (pd.DataFrame): DataFrame con los precios históricos.

        Returns:
            SenalTrading: La señal de trading generada (COMPRAR, VENDER, MANTENER).
        """
        if len(datos_historicos) < self.periodo_largo:
            logging.warning("No hay suficientes datos históricos para calcular las medias móviles.")
            return SenalTrading.MANTENER

        # Calcular SMAs
        datos_historicos['sma_corta'] = datos_historicos['price'].rolling(window=self.periodo_corto).mean()
        datos_historicos['sma_larga'] = datos_historicos['price'].rolling(window=self.periodo_largo).mean()
        
        # Obtener los últimos valores calculados
        ultima_sma_corta = datos_historicos['sma_corta'].iloc[-1]
        ultima_sma_larga = datos_historicos['sma_larga'].iloc[-1]
        
        # Obtener los valores previos para detectar el cruce
        penultima_

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
