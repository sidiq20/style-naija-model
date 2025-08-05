import requests
from bs4 import BeautifulSoup 
import pandas as pd
import os

base_url = "https://www.bellanaija.com/category/style/aso-ebi-bella/" 
output_dir = "scraped/blog"
post_limit = 10

os.makedirs(output_dir, exist_ok=True)
result = []

def get_post_links():
    res = requests.get(base_url)
    soup = BeautifulSoup(res.text, "html.parser")
    links = [a["href"] for a in soup.select(".post-title a")]
    return links[:post_limit]

def scrape_post(link):
    res = requests.get(link)
    soup = BeautifulSoup(res.text, "html.perser")
    title = soup.select_one("h1").text.strip()
    imgs = soup.select("img")
    
    for i, img in enumerate(imgs):
        img_url = img.get("src")
        if not img_url or "logo" in img_url:
            continue
        try:
            filename = f"bellanaija_{title[:20].replace(' ', ' ')}_{i}.jpg"
            img_data = requests.get(img_url).content
            with open(os.path.join(output_dir, filename), "wb") as f:
                f.write(img_data)
                
            result.append({
                "filename": filename,
                "post_title": title,
                "post_url": link,
                "image_url": img_url
            })
            
        except Exception as e:
            print(f"Error downloading {img_url} {e}")
            
links = get_post_links()
print(f"founf {len(links)}")

for link in links:
    print(f"scrapping post: {link}")
    scrape_post(link)
    
df = pd.DataFrame(result)
df.to_csv(os.path.join(output_dir, "bellanaija_scraped_data.csv"), index=False)
print("✅ Done. Scraped blog images and saved metadata.")