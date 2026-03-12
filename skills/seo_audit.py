import requests
from bs4 import BeautifulSoup
import time

def run_seo_audit(url: str):
    """
    Performs a technical SEO audit on the given URL.
    Returns a Markdown report.
    """
    print(f"🕵️‍♂️ [SKILL: SEO-AUDIT] Analyzing {url}...")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10, headers={"User-Agent": "Psiquis-X/SEO-Bot"})
        load_time = time.time() - start_time
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Meta Tags
        title = soup.title.string if soup.title else "MISSING"
        meta_desc = soup.find("meta", {"name": "description"})
        desc_content = meta_desc["content"] if meta_desc else "MISSING"
        
        # 2. Headings
        h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2s = [h.get_text(strip=True) for h in soup.find_all("h2")]
        
        # 3. Images
        images = soup.find_all("img")
        missing_alt = [img['src'] for img in images if not img.get('alt')]
        
        # 4. Links
        links = soup.find_all("a")
        internal = [l['href'] for l in links if l.get('href') and url in l['href']]
        
        # Score Calculation
        score = 100
        if title == "MISSING": score -= 20
        if desc_content == "MISSING": score -= 20
        if not h1s: score -= 15
        if len(missing_alt) > 0: score -= 10
        if load_time > 2.0: score -= 10
        
        report = f"""
### 🕵️‍♂️ SEO Audit Report: {url}
**Overall Score: {score}/100**

#### ⚡ Performance
- **Load Time:** {load_time:.2f}s (Target: < 2.0s)
- **Status Code:** {response.status_code}

#### 🏷️ Meta Data
- **Title:** `{title}` ({len(title)} chars)
- **Description:** `{desc_content}` ({len(desc_content)} chars)

#### 📑 Content Structure
- **H1 Tags:** {len(h1s)} found. {f"('{h1s[0]}')" if h1s else "❌ MISSING"}
- **H2 Tags:** {len(h2s)} found.

#### 🖼️ Media & Links
- **Images:** {len(images)} total.
- **Missing Alt Text:** {len(missing_alt)} images.
- **Internal Links:** {len(internal)} found.

#### 💡 Recommendations
"""
        if score < 100:
            if not h1s: report += "- 🔴 **Add an H1 tag.** It is crucial for SEO ranking.\n"
            if desc_content == "MISSING": report += "- 🔴 **Add a Meta Description.** It improves click-through rates.\n"
            if len(missing_alt) > 0: report += f"- 🟠 **Fix Alt Text.** {len(missing_alt)} images are missing descriptions.\n"
            if load_time > 2.0: report += "- 🟠 **Optimize Speed.** The site is slower than recommended (2s).\n"
        else:
            report += "- ✅ **Perfect!** No critical issues found.\n"
            
        return report

    except Exception as e:
        return f"❌ [SEO-AUDIT FAILED]: {str(e)}"
