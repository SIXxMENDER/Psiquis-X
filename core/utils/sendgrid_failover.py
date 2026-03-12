"""
SendGrid Failover - Dead Man's Switch
Sistema de redundancia para alertas cuando Telegram falla.
"""
import os
import logging
from typing import Dict, Any, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

# Configuration
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
EMERGENCY_EMAIL = os.environ.get("EMERGENCY_EMAIL")  # Tu email personal
FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "motor@psiquis-x.com")

# Dead Man's Switch Counter
_telegram_failures = 0
_max_failures = 3
_modo_seguro_activo = False


def incrementar_fallos_telegram() -> int:
    """
    Incrementa el contador de fallos de Telegram.
    
    Returns:
        Número actual de fallos.
    """
    global _telegram_failures
    _telegram_failures += 1
    logging.warning(f"⚠️ Telegram fallo #{_telegram_failures}/{_max_failures}")
    return _telegram_failures


def resetear_contador() -> None:
    """Resetea el contador cuando Telegram vuelve a funcionar."""
    global _telegram_failures
    if _telegram_failures > 0:
        logging.info(f"✅ Telegram recuperado. Resetando contador (era {_telegram_failures})")
        _telegram_failures = 0


def verificar_dead_mans_switch() -> bool:
    """
    Verifica si se debe activar el Dead Man's Switch.
    
    Returns:
        True si se alcanzó el límite de fallos.
    """
    return _telegram_failures >= _max_failures


def activar_modo_seguro() -> None:
    """Activa el Modo Seguro (pausa operaciones de escritura)."""
    global _modo_seguro_activo
    _modo_seguro_activo = True
    logging.critical("🚨 MODO SEGURO ACTIVADO - Pausando operaciones de escritura")


def esta_en_modo_seguro() -> bool:
    """Verifica si el sistema está en Modo Seguro."""
    return _modo_seguro_activo


def enviar_email_emergencia(
    titulo: str,
    cuerpo: str,
    contexto: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Envía un email de emergencia via SendGrid.
    
    Args:
        titulo: Subject del email
        cuerpo: Cuerpo del mensaje
        contexto: Información adicional (logs, estado del sistema)
    
    Returns:
        True si se envió exitosamente.
    """
    if not SENDGRID_API_KEY:
        logging.error("❌ SENDGRID_API_KEY no configurada. No se puede enviar email.")
        return False
    
    if not EMERGENCY_EMAIL:
        logging.error("❌ EMERGENCY_EMAIL no configurada.")
        return False
    
    try:
        # Formatear contexto
        contexto_str = ""
        if contexto:
            contexto_str = "\n\n--- CONTEXTO TÉCNICO ---\n"
            for k, v in contexto.items():
                contexto_str += f"{k}: {v}\n"
        
        # Construir mensaje
        html_content = f"""
        <html>
        <body style="font-family: monospace; background-color: #1a1a1a; color: #00ff00; padding: 20px;">
            <h1 style="color: #ff0000;">🚨 ALERTA CRÍTICA DEL MOTOR</h1>
            <h2>{titulo}</h2>
            <div style="background-color: #000; padding: 15px; border-left: 4px solid #ff0000;">
                <pre>{cuerpo}</pre>
            </div>
            {f'<div style="margin-top: 20px;"><pre>{contexto_str}</pre></div>' if contexto else ''}
            <hr>
            <p style="color: #888;">Automated System Alert - Psiquis-X Framework</p>
        </body>
        </html>
        """
        
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=EMERGENCY_EMAIL,
            subject=f"🚨 MOTOR INCOMUNICADO - {titulo}",
            html_content=html_content
        )
        
        # Enviar
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            logging.info(f"📧 Email de emergencia enviado a {EMERGENCY_EMAIL}")
            return True
        else:
            logging.error(f"❌ SendGrid error: {response.status_code} - {response.body}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Fallo al enviar email de emergencia: {e}")
        # Último recurso: log a Cloud Logging
        logging.critical(f"CRITICAL - Email failover también falló: {titulo} - {cuerpo}")
        return False


def notificar_fallo_telegram(error_details: str) -> None:
    """
    Gestiona un fallo de Telegram y activa el failover si es necesario.
    
    Args:
        error_details: Detalles del error de Telegram
    """
    fallos = incrementar_fallos_telegram()
    
    if verificar_dead_mans_switch():
        logging.critical("💀 Dead Man's Switch ACTIVADO - Telegram ha fallado 3 veces")
        
        # Activar Modo Seguro
        activar_modo_seguro()
        
        # Enviar email de emergencia
        enviar_email_emergencia(
            titulo="Sistema Incomunicado - Telegram Inaccesible",
            cuerpo=f"""
El motor ha perdido comunicación con Telegram después de {fallos} intentos fallidos.

ESTADO DEL SISTEMA:
- Modo Seguro: ACTIVADO
- Operaciones de escritura: PAUSADAS
- Último error: {error_details}

ACCIÓN REQUERIDA:
1. Verificar el estado de Telegram API
2. Revisar el token del bot
3. Reiniciar Sixmender si es necesario
4. Usar Cloud Console para inspeccionar logs

El sistema permanecerá en Modo Seguro hasta que se restablezca la comunicación.
            """,
            contexto={
                "Fallos consecutivos": fallos,
                "Timestamp": str(os.popen('date').read().strip()),
                "Error": error_details
            }
        )
