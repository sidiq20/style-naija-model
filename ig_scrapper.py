import instaloader
import os 
import pandas as pd 
from datetime import datetime 


# config
hashtags = ["asoebi", "naijafashion", "naijastyles", "senatorwears"]
output_dir = "scraped/ig"
post_limit = 50 

os.makedirs(output_dir, exist_ok=True)

L = instaloader.Instaloader(download_comments=False, save_metadata=False, download_video_thumbnails=False)

csv_data = []

for tag in hashtags:
    #loggers to trouble shoot
    print(f" scrapping {tag}")
    
    tag_dir = os.path.join(output_dir, tag)
    os.makedirs(tag_dir, exist_ok=True)
    
    hashtags = instaloader.Hashtag.from_name(L.context, tag)
    
    count = 0
    for post in hashtags.get_posts():
        if count >= post_limit:
            break
        
        try:
            post_date = post.date.strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{tag}_{post_date}_{post.shortcode}.jpg"
            filepath = os.path.join(tag_dir, filename)
            
            L.download_pic(filepath, post.url, post.date)
            
            caption = post.caption or ""
            with open(filepath.replace(".jpg", ".txt"), "w", encoding="utf-8") as f:
                f.write(caption)
                
            csv_data.append({
                "filename": filename,
                "hashtag": tag,
                "caption": caption,
                'post_url': f"https://www.instagram.com/p/{post.shortcode}/",
                "timestamp": post.date,
                "owner": post.owner_username
            })
            
            count += 1 
            
        except Exception as e:
            print(f" Error: {e}")
            continue
        
df = pd.DataFrame(csv_data)
csv_data = os.path.join(output_dir, "instagram_scraped_data.csv")
df.to_csv(csv_data, index=False, encoding="utf-8")

print(f"\n✅ Done. Scraped {len(df)} posts.")
print(f" Images saved to: {output_dir}")
print(f" metadata csv: {csv_data}")