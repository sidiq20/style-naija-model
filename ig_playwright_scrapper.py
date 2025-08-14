import os
import time
import pandas as pd
import requests
from playwright.sync_api import sync_playwright

hashtags = ["asoebi", "naijafashion", "naijastyles", "senatorwears"]
limit = 50
output_dir = "scraped/ig_playwright"

os.makedirs(output_dir, exist_ok=True)
results = []

with sync_playwright() as p:
    context = None
    session_path = "ig_session"

    if os.path.exists(session_path):
        print(" Loading saved Instagram session...")
        context = p.chromium.launch_persistent_context(session_path, headless=False, slow_mo=50)
    else:
        print(" No saved session. Logging in required...")
        context = p.chromium.launch_persistent_context(session_path, headless=False, slow_mo=50)

    page = context.new_page()

    for tag in hashtags:
        print(f"🔍 Scraping #{tag}")
        tag_dir = os.path.join(output_dir, tag)
        os.makedirs(tag_dir, exist_ok=True)

        try:
            page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=60000)
            print("Page loaded")
            
            try:
                page.locator("text=Only allow essential cookies").click(timeout=3000)
                print("Dismissed cokkie popup")
            except:
                pass

            print(" Page loaded or redirected")
            if "login" in page.url:
                print(" Instagram redirected to login page. You must log in.")
                input(" Log in manually in the browser, then press Enter...")

        except Exception as e:
            print(f"Failed to loas tag page for {tag}: {e}")
            continue 

        post_urls = set()


        
        page.wait_for_timeout(5000)
        time.sleep(5)


        while len(post_urls) < limit:
            page.mouse.wheel(0, 3000)
            time.sleep(2)

            anchors = page.query_selector_all("a")
            for a in anchors:
                href = a.get_attribute("href")
                if href and href.startswith("/p/"):
                    post_urls.add("https://www.instagram.com" + href)
                if len(post_urls) >= limit:
                    break

        print(f"Found {len(post_urls)} post links for #{tag}")

        count = 0
        for url in list(post_urls)[:limit]:
            try:
                page.goto(url, timeout=30000)
                time.sleep(3)

                img = page.query_selector("article img[srcset]")
                if not img:
                    continue

                img_url = img.get_attribute("src")
                caption = img.get_attribute("alt") or ""

                filename = f"{tag}_{count}.jpg"
                filepath = os.path.join(tag_dir, filename)

                img_data = requests.get(img_url).content
                with open(filepath, "wb") as f:
                    f.write(img_data)

                results.append({
                    "filename": filename,
                    "hashtag": tag,
                    "caption": caption,
                    "post_url": url,
                    "image_url": img_url
                })

                count += 1
                print(f" Downloaded {filename}")
            except Exception as e:
                print(f" Failed to process {url}: {e}")
                continue

    context.close()

df = pd.DataFrame(results)
csv_path = os.path.join(output_dir, "instagram_scraped_data.csv")
df.to_csv(csv_path, index=False, encoding="utf-8")

print(f"\n Done. Scraped {len(df)} posts.")
print(f" Images saved to: {output_dir}")
print(f" Metadata saved to: {csv_path}")
