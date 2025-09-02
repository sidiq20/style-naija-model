from playwright.sync_api import sync_playwright 
import os 
import time 
import requests                 
import pandas as pd
from PIL import Image
from io import BytesIO

query = "nigeria fashion wedding"
limit = 50
output_dir = "scraped/pinterest" 

os.makedirs(output_dir, exist_ok=True)
results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=50)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )
    
    print(f"🔍 Searching Pinterest for: {query}")
    page.goto(
        f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}", 
        timeout=60000,
        wait_until="domcontentloaded"
    )
    
    image_url = set()
    while len(image_url) < limit:
        page.mouse.wheel(0, 3000)
        time.sleep(2)
        images = page.query_selector_all("img")
        
        for img in images:
            src = img.get_attribute("src")
            alt = img.get_attribute("alt")
            # Filter out small placeholders (like 60x60, 236x, etc.)
            if src and "236x" not in src and "60x60" not in src:
                image_url.add((src, alt or ""))
            if len(image_url) >= limit * 2:  # collect extra, since we'll filter later
                break 
            
    browser.close()
    
    print(f" Found {len(image_url)} raw images")
    
    valid_images = []
    for i, (img_url, desc) in enumerate(image_url):
        try:
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()

            # Check file size (must be ≥120 KB)
            if len(response.content) < 120 * 1024:
                continue  

            # Check resolution
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            if width < 1000 or height < 1920:
                continue  

            # Save only valid images
            filename = f"pinterest_{i}.jpg"
            with open(os.path.join(output_dir, filename), "wb") as f:
                f.write(response.content)
            
            valid_images.append({
                "filename": filename,
                "description": desc,
                "source": img_url,
                "width": width,
                "height": height,
                "size_kb": round(len(response.content) / 1024, 2)
            })
        except Exception as e:
            print(f"⚠️ Error downloading {img_url}: {e}")

# Save metadata
df = pd.DataFrame(valid_images)
df.to_csv(os.path.join(output_dir, "pinterest_scraped_data.csv"), index=False)
print(f"✅ Done. {len(valid_images)} valid images saved.")
