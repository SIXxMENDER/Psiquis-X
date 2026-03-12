import os
import asyncio
import random
import requests
from playwright.async_api import async_playwright, Page
from typing import Dict, Any, List
from core.S_SERIES.cortex import cortex
from core.S_SERIES.mission_control import mission_manager

async def _check_url_alive(url: str) -> bool:
    """Pre-flight check to avoid navigating to dead/hallucinated URLs."""
    try:
        res = requests.head(url, timeout=5, allow_redirects=True)
        return res.status_code < 400
    except:
        return False

async def _vision_click_fallback(page: Page, goal: str) -> bool:
    """Uses Cortex Vision to find coordinates and click when CSS selectors fail."""
    screenshot_path = "data/last_web_error.png"
    await page.screenshot(path=screenshot_path)
    
    prompt = (
        f"Actúa como un Navegador Humano. En la imagen adjunta, necesito encontrar el elemento para: {goal}.\n"
        "Responde ÚNICAMENTE con las coordenadas en formato JSON: {\"x\": 123, \"y\": 456}. "
        "Si no está visible, responde {\"error\": \"not_found\"}."
    )
    
    res_str = await cortex.ask_vision(prompt, screenshot_path)
    res = cortex.extract_json(res_str, None)
    
    if "x" in res and "y" in res:
        print(f"[VISION] Clicking at {res['x']}, {res['y']} for {goal}...")
        await page.mouse.click(res["x"], res["y"])
        return True
    return False

async def ejecutar(**kwargs) -> Dict[str, Any]:
    raw_input = kwargs.get("url") or kwargs.get("platform_url")
    if not raw_input:
        return {"error": "Missing Input", "status": "FAILED"}

    # 1. Determine Mode (Direct URL vs Search Query)
    import re
    url_pattern = re.compile(r'https?://[^\s,"]+')
    found_urls = url_pattern.findall(raw_input)
    
    is_query = not raw_input.strip().startswith("http") and not found_urls
    
    # Define Strategy
    navigation_targets = [] # List of (provider_name, url)
    if is_query:
        print(f"[SCRAPER] Input is a query. Activating RESILIENCE PROTOCOL.")
        q = raw_input.replace(" ", "+")
        navigation_targets = [
            ("DuckDuckGo", f"https://duckduckgo.com/html/?q={q}"),
            ("Google", f"https://www.google.com/search?q={q}&hl=en")
        ]
    else:
        print(f"[SCRAPER] multinavigation Mode: {len(found_urls)} URLs found.")
        for i, url in enumerate(found_urls):
            navigation_targets.append((f"Target_{i+1}", url))

    # 2. Execution Loop
    extracted_data_blocks = []
    import time
    ss_dir = "data/vault/screenshots"
    os.makedirs(ss_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # For Demo: Show the action 
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        for name, url in navigation_targets:
            print(f"[SCRAPER] Navigating to {name}: {url}")
            try:
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # --- GENERAL INTERACTION LAYER (HUMAN-LIKE SCROLLING) ---
                print("[SCRAPER] Initiating human-like scrolling for visualization and lazy-loading...")
                # Wait 2 seconds for initial render
                await asyncio.sleep(2)
                
                # Scroll down 15 times over ~9 seconds smoothly
                for _ in range(15):
                    await page.mouse.wheel(delta_x=0, delta_y=400)
                    await asyncio.sleep(0.6) 
                
                # Wait one final second to let final elements settle
                await asyncio.sleep(1)

                # Extract Content
                title = await page.title()
                content = await page.evaluate("document.body.innerText")
                
                # --- EVIDENCE CAPTURE (Screenshot) ---
                safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
                ss_path = f"{ss_dir}/ss_{int(time.time())}_{safe_name}.png"
                await page.screenshot(path=ss_path)
                print(f"[SCRAPER] Screenshot saved: {ss_path}")

                # Check for CAPTCHA
                if "captcha" in content.lower() or "robot" in content.lower():
                    await mission_manager.emit_event("thought", f"CAPTCHA on {name}. Requesting HITL...", agent="SCRAPER")
                    approved = await mission_manager.wait_for_approval(f"Solve captcha for {url}", agent="SCRAPER")
                    if approved:
                         content = await page.evaluate("document.body.innerText")
                         await page.screenshot(path=ss_path) # Retake after solve

                extracted_data_blocks.append(f"--- DATA FROM {url} ---\nEvidence: {ss_path}\nTitle: {title}\nContent:\n{content[:8000]}")
                await page.close()
                
            except Exception as e:
                print(f"[SCRAPER] Error on {url}: {e}")

        await browser.close()

    if not extracted_data_blocks:
        return {"status": "FAILED", "diagnostico": "No data extracted."}

    final_content = "\n\n".join(extracted_data_blocks)

    # --- SYNTHESIS & REPORT GENERATION ---
    # Only generate if explicitly requested or default to True (legacy behavior)
    # BUT for specific missions (like DocIntel), we might want to skip this to avoid overwriting.
    should_generate_report = kwargs.get("generate_report", True)
    
    final_report = ""
    filename = ""

    if should_generate_report:
        print(f"[SCRAPER] Synthesizing Final Report from {len(final_content)} chars of data...")
        
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report_prompt = (
            f"IDENTITY: You are a Senior Institutional Market Analyst at Sovereign Intelligence (Agentic Division).\n"
            f"OBJECTIVE: Synthesize a high-precision market intelligence report based on the following real-time data extraction.\n\n"
            f"DATE_OF_REPORT: {current_date}\n\n"
            f"CORE DATA:\n{final_content[:25000]}\n\n"
            "DIRECTIVA DE INTEGRIDAD TEMPORAL:\n"
            "1. Current year is 2026. If extracted data mentions 2024 or older years, treat them as 'Historical context' or 'Legacy data'.\n"
            "2. Do NOT present 2024 data as the current market state. If a prediction is from 2024, call it 'Historical projection'.\n\n"
            "INSTRUCTIONS FOR QUALITY:\n"
            "1. TONE: Professional, objective, and analytical (Institutional Grade). No conversational filler.\n"
            "2. EVIDENCE AUDIT: For every technical level or trend mentioned, cite the corresponding screenshot path from the data (e.g., 'Source: data/vault/screenshots/ss_...').\n"
            "3. CROSS-MARKET CORRELATION: Explicitly connect how movements in SPX (S&P 500) are correlating with Safe Haven assets (Gold/Silver) and Risk assets (BTC).\n"
            "4. CONTRADICTION RESOLUTION: If data shows a price bounce but sentiment is bearish, explain it as a 'Technical correction within a larger trend'.\n"
            "5. IDENTITY DISCLAIMER: End the report with: 'This report was generated autonomously by Psiquis-X Engine. Human intervention: None (HITL-Verified).'\n\n"
            "STRUCTURE:\n"
            "   - I. EXECUTIVE SUMMARY (High-level institutional view).\n"
            "   - II. ASSET DEEP-DIVE (BTC, Gold, Silver, SPX). include Levels and Evidence citations.\n"
            "   - III. CONFLUENCE & CORRELATION ANALYSIS.\n"
            "   - IV. SOVEREIGN VERDICT.\n"
        )
        
        final_report = cortex.ask(report_prompt)
        
        # --- PERSISTENCE ---
        filename = "data/reports/sovereign_intelligence_report.md"
        os.makedirs("data/reports", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_report)
            
        print(f"[MARKETING] ✅ REPORTE FINAL GUARDADO: {filename}")
    else:
        print("[SCRAPER] Skipping automatic report generation (Raw Data Mode).")

    return {
        "status": "SUCCESS",
        "data": final_content, # Return raw content for the caller to process
        "report_generated": should_generate_report,
        "report_path": filename if should_generate_report else None,
        "accion_sugerida": "CONTINUE"
    }
