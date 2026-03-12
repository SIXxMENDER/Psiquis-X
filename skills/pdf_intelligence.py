import requests
import io
import time
from typing import Optional, Tuple, List
from pypdf import PdfReader

def download_and_extract_text(
    url: str, 
    verify_ssl: bool = True,
    page_range: Optional[Tuple[int, int]] = None,
    specific_pages: Optional[List[int]] = None
) -> str:
    """
    Downloads a PDF from a URL and extracts its text content.
    
    Args:
        url (str): The URL of the PDF file.
        verify_ssl (bool): Whether to verify SSL certificates. Default True.
        page_range (tuple): Optional (start_page, end_page) 1-indexed.
        specific_pages (list): Optional list of specific 1-indexed pages to extract.
        
    Returns:
        str: The extracted text from the PDF.
    """
    print(f"[PDF SKILL] Downloading PDF from: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        if url.startswith("file:///"):
            # Handle local file reading
            local_path = url.replace("file:///", "")
            import urllib.request
            local_path = urllib.request.url2pathname(local_path)
            pdf_file = open(local_path, "rb")
            reader = PdfReader(pdf_file)
        else:
            # Handle web URL downloading
            response = requests.get(url, headers=headers, verify=verify_ssl, timeout=30)
            response.raise_for_status()
            pdf_file = io.BytesIO(response.content)
            reader = PdfReader(pdf_file)
        
        full_text = []
        num_pages = len(reader.pages)
        
        pages_to_extract = []
        if specific_pages:
            pages_to_extract = [p - 1 for p in specific_pages if 1 <= p <= num_pages]
            print(f"[PDF SKILL] Extracting specific pages: {specific_pages} out of {num_pages}...")
        elif page_range:
            start, end = page_range
            start = max(1, start)
            end = min(num_pages, end)
            pages_to_extract = list(range(start - 1, end))
            print(f"[PDF SKILL] Extracting pages {start} to {end} out of {num_pages}...")
        else:
            pages_to_extract = list(range(num_pages))
            print(f"[PDF SKILL] Extracting all {num_pages} pages...")
            
        import os
        filename = os.path.basename(url)
        for i in pages_to_extract:
            text = reader.pages[i].extract_text()
            if text:
                full_text.append(f"\n[SOURCE_FILE: {filename}] [PAGE: {i+1}]\n{text}")
                
        return "\n".join(full_text)

    except Exception as e:
        print(f"[PDF SKILL] Error: {e}")
        return f"ERROR: Could not process PDF. {str(e)}"

if __name__ == "__main__":
    # Test with a dummy PDF if run directly
    test_url = "https://dummy.pdf" # Placeholder
    print("Test Mode: helper function ready.")
