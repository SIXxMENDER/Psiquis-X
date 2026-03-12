import logging
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page, Browser

class Hunter:
    """
    El Cazador (v2 - Universal): Módulo de Navegación Web Generalista.
    Habilidad: Navegar, Renderizar JS, Extraer DOM, Capturar Pantalla.
    Filosofía: Herramienta agnóstica. No contiene lógica de negocio.
    """
    def __init__(self, headless: bool = True):
        self.logger = logging.getLogger("Hunter")
        self.headless = headless
        
    def _get_browser_context(self, p):
        """Configura un navegador indetectable (evasión básica de bots)."""
        browser = p.chromium.launch(headless=self.headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale="es-MX"
        )
        return browser, context

    def browse(self, url: str, action_script: Optional[str] = None) -> Dict[str, Any]:
        """
        Navega a una URL y devuelve el contenido.
        
        Args:
            url (str): Destino.
            action_script (str, optional): JavaScript a ejecutar en la página antes de extraer.
            
        Returns:
            Dict: {url, title, content (text), html, screenshot_path}
        """
        self.logger.info(f"🏹 Hunting URL: {url}")
        
        with sync_playwright() as p:
            browser, context = self._get_browser_context(p)
            page = context.new_page()
            
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Ejecutar script custom si existe (para scroll, clicks, etc)
                if action_script:
                    self.logger.info("⚡ Ejecutando script inyectado...")
                    page.evaluate(action_script)
                
                # Extracción Genérica
                title = page.title()
                content = page.inner_text("body") # Texto limpio
                html = page.content() # HTML crudo para parsing complejo
                
                # Screenshot de evidencia
                screenshot_path = "hunter_snapshot.png"
                page.screenshot(path=screenshot_path)
                
                return {
                    "status": "SUCCESS",
                    "url": url,
                    "title": title,
                    "content_snippet": content[:500] + "...",
                    "full_text": content,
                    "html": html,
                    "screenshot": screenshot_path
                }
                
            except Exception as e:
                self.logger.error(f"❌ Hunt failed: {e}")
                return {
                    "status": "ERROR",
                    "error": str(e),
                    "url": url
                }
            finally:
                browser.close()

    def search_google(self, query: str) -> str:
        """Helper rápido para buscar algo en Google y devolver el primer resultado."""
        # TODO: Implementar usando browse() sobre google.com
        pass

# Singleton para uso directo
hunter = Hunter()
