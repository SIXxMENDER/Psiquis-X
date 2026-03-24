import os
import requests

def enviar_notificacion_discord(mensaje: str, webhook_url: str):
    """Sends a notification to Discord."""
    if not webhook_url:
        print("No Discord Webhook URL provided.")
        return
    
    try:
        requests.post(webhook_url, json={"content": mensaje})
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

def enviar_email_sendgrid(asunto: str, contenido: str, destinatarios: list):
    """Sends an email via SendGrid."""
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        print("No SendGrid API Key found.")
        return
    
    # Mock implementation for skeleton
    print(f"Sending email: {asunto} to {destinatarios}")
