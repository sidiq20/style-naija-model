from playwright.sync_api import sync_playwright 
import os 
import time 
import pandas as pd 

query = "nigeria fashion wedding"
limit = 50
output_dir = "scraped/pinterest" 

os.makedirs(output_dir, exist_ok=True)
results = []

with sync_playwright as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    
    print(f"🔍 Searching Pinterest for: {query}")
    page.goto(f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}")
    
    image_url = set()
    while len(image_url) < limit:
        page.mouse.whell(0, 3000)
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
            img_data = page.request.get(img_url).body()
            with open(os.path.join(output_dir, filename), "wb") as f:
                f.write(img_data)
                
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