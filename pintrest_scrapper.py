from playwright.sync_api import sync_playwright 
import os 
import time 
import requests                 
import pandas as pd 

query = "nigeria fashion wedding"
limit = 50
output_dir = "scraped/pinterest" 

os.makedirs(output_dir, exist_ok=True)
results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=50)
    page = browser.new_page()
    
    
    print(f"🔍= Searching Pinterest for: {query}")
    page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    page.goto(
        f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}", timeout=60000,
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
            if src and "236x" not in src: 
                image_url.add((src, alt or ""))
            if len(image_url) >= limit:
                break 
            
    browser.close()
    
    print(f" found {len(image_url)} images")
    
    for i, (img_url, desc) in enumerate(image_url):
        try:
            filename = f"pintrest_{i}.jpg"
            response = requests.get(img_url)
            response.raise_for_status()
            with open(os.path.join(output_dir, filename), "wb") as f:
                f.write(response.content)
            
            results.append({
                "filename": filename,
                "description": desc,
                "source": img_url
            })
        except Exception as e:
            print(f"Error downloading image {img_url}: {e}")

            
df = pd.DataFrame(results)
df.to_csv(os.path.join(output_dir, "pintrest_scraped_data.csv"), index=False)
print(" Done.")