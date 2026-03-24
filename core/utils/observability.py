import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from phoenix.trace.opentelemetry import TracerProvider as PhoenixTracerProvider

def setup_phoenix():
    """
    Configura Arize Phoenix para observabilidad profunda (OpenInference).
    Permite visualizar trazas, costos y alucinaciones de forma agnóstica.
    """
    print("📡 [OBSERVABILITY] Inicializando Arize Phoenix (OpenTelemetry)...")
    
    # En local, Phoenix suele correr en el puerto 6006
    # Si no hay colector, Phoenix puede actuar como uno.
    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        # Configuración básica si no existe
        trace.set_tracer_provider(PhoenixTracerProvider())
    
    tracer = trace.get_tracer("psiquis-x-motor")
    return tracer

# Inicialización temprana si se desea
# setup_phoenix()
