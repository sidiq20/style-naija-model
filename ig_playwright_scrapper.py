import os
import time
import pandas as pd
import requests
from playwright.sync_api import sync_playwright

hashtags = ["asoebi", "naijafashion", "naijastyles", "senatorwears"]
limit = 50
output_dir = "scraped/ig_playwright"
session_path = "ig_session" # folder to store session

os.makedirs(output_dir, exist_ok=True)
results = []

with sync_playwright() as p:

    if os.path.exists(session_path):
        print(" Loading saved Instagram session...")
    else:
        print(" No saved session. Logging in required...")
    
    context = p.chromium.launch_persistent_context(
        session_path,
        headless=False,
        slow_mo=50
    )
    
    page = context.new_page()

    page.goto("https://www.instagram.com/", timeout=60000)
    if "login" in page.url:
        print("Please log in to instagram in the opened browser. ")
        input("Press enter here after login")
        
    for tag in hashtags:
        print("scrappping {tag}")
        tag_dir = os.path.join(output_dir, tag)
        os.makedirs(tag_dir, exist_ok=True)
        
        try:
            page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=60000)
            
            try:
                page.locator("text=Only allow essential cokkies ").click(timeout=3000)
                print("Cookie popup dismissed")
            except:
                pass 
            
            
            post_urls = set()
            while len(post_urls) < limit:
                anchors = page.query_selector_all("a")
                for a in anchors:
                    href = a.get_attribute("href")
                    if href and href.startswith("/p/"):
                        post_urls.add("https://www.instagram.com" + href)
                    if len(post_urls) >= limit:
                        break 
                page.mouse.wheel(0, 3000)
                time.sleep(2)
                
            print(f"found {len(post_urls)} post links.")
            
            count = 0 
            for url in list(post_urls)[:limit]:
                try:
                    page.goto(url, timeout=30000)
                    page.wait_for_selector("article img[srcset]", timeout=10000)
                    
                    img = page.query_selector("article img[srcset]")
                    if not img:
                        continue
                    
                    img_url = img.get_attribute("src")
                    caption = img.get_attribute("alt") or ""
                    
                    filename = f"{tag}_{count}.jpg"
                    filepath = os.path.join(tag_dir, filename)
                    
                    img_data = page.evaluate("""(url)=> {
                        return fecth(url)
                            .then(res => res.arrayBuffer())
                            .then(buf => array.from(new Unit8Array(buf)));
                    }""", img_url)
                    
                    with open(filepath, "wb") as f:
                        f.write(bytearray(img_data))
                        
                    results.append({
                        "filename": filename,
                        "hastags": tag,
                        "caption": caption,
                        "post_url": url,
                        "image_url": img_url
                    })
                    
                    count += 1
                    print(f"saved {filename}")
                    
                except Exception as e:
                    print(f"error scrapping {url}: {e}")
                    continue
            
        except Exception as e:
            print(f"failed to load tag {tag}: {e}")
            continue
        
    context.close()
    
df = pd.DataFrame(results)
csv_path = os.path.join(output_dir, "instagram_scraped_data.csv")
df.to_csv(csv_path, index=False, encoding="utf-8")
df.to_csv(csv_path, index=False, encoding="utf-8")

print(f"done scraped {len(df)} posts")
print(f"images saved to: {output_dir}")
print(f"Metadat saved to: {csv_path}")