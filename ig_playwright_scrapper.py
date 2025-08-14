import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ====== CONFIG ======
hashtags = ["asoebi", "naijafashion", "naijastyles", "senatorwears"]
limit = 50
output_dir = "scraped/ig_playwright"
session_path = "ig_session"  # Folder to store login session
scroll_pause = 2
# ====================

os.makedirs(output_dir, exist_ok=True)
results = []

with sync_playwright() as p:
    if os.path.exists(session_path):
        print("🔄 Loading saved Instagram session...")
    else:
        print("🆕 No saved session. You must log in manually once...")

    context = p.chromium.launch_persistent_context(
        session_path,
        headless=False,
        slow_mo=50
    )
    page = context.new_page()

    page.goto("https://www.instagram.com/", timeout=60000)
    if "login" in page.url:
        print("🔑 Please log in to Instagram in the opened browser.")
        input("➡️ Press Enter here after logging in...")

    for tag in hashtags:
        print(f"\n🔍 Scraping #{tag}...")
        tag_dir = os.path.join(output_dir, tag)
        os.makedirs(tag_dir, exist_ok=True)

        try:
            page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=60000)

            # Try to close cookie popup
            try:
                page.locator("text=Only allow essential cookies").click(timeout=3000)
                print("✅ Cookie popup dismissed.")
            except:
                pass

            # Scroll to collect post links
            post_urls = set()
            while len(post_urls) < limit:
                for href in page.locator("a").evaluate_all("els => els.map(el => el.getAttribute('href'))"):
                    if href and href.startswith("/p/"):
                        post_urls.add("https://www.instagram.com" + href)
                    if len(post_urls) >= limit:
                        break
                page.mouse.wheel(0, 3000)
                time.sleep(scroll_pause)

            print(f"✅ Found {len(post_urls)} post links.")

            count = 0
            for url in list(post_urls)[:limit]:
                try:
                    print(f"📄 Visiting: {url}")
                    page.goto(url, timeout=60000)
                    page.wait_for_timeout(2000)  # Let JS load

                    # Handle lazy-load: scroll a bit
                    page.mouse.wheel(0, 1000)
                    page.wait_for_timeout(1000)

                    media_selector = (
                        "article img[srcset], article img[src], "
                        "article video[src], "
                        "ul li video[src], ul li img[src]"
                    )

                    try:
                        page.wait_for_selector(media_selector, timeout=20000)
                    except PlaywrightTimeout:
                        print("   🔄 Media not found, retrying after reload...")
                        page.reload(timeout=30000)
                        try:
                            page.wait_for_selector(media_selector, timeout=15000)
                        except PlaywrightTimeout:
                            print(f"❌ Skipping {url} — no media found after retry.")
                            continue

                    # Collect all visible media in the post
                    media_elements = page.locator(media_selector)
                    media_urls = media_elements.evaluate_all(
                        "els => els.map(el => el.getAttribute('src'))"
                    )

                    if not media_urls:
                        print(f"⚠️ No media found for {url}")
                        continue

                    caption_el = page.query_selector("article h1, article div[role='button']")
                    caption = caption_el.inner_text() if caption_el else ""

                    for media_url in media_urls:
                        if not media_url:
                            continue

                        ext = "mp4" if ".mp4" in media_url else "jpg"
                        filename = f"{tag}_{count}.{ext}"
                        filepath = os.path.join(tag_dir, filename)

                        media_data = page.evaluate("""(url) => {
                            return fetch(url)
                            .then(res => res.arrayBuffer())
                            .then(buf => Array.from(new Uint8Array(buf)));
                        }""", media_url)

                        with open(filepath, "wb") as f:
                            f.write(bytearray(media_data))

                        results.append({
                            "filename": filename,
                            "hashtag": tag,
                            "caption": caption,
                            "post_url": url,
                            "media_url": media_url,
                            "type": "video" if ext == "mp4" else "image"
                        })

                        print(f"✅ Saved {filename}")
                        count += 1

                except KeyboardInterrupt:
                    print("\n🛑 Stopping due to keyboard interrupt...")
                    break
                except Exception as e:
                    print(f"❌ Error scraping {url}: {e}")
                    continue

        except Exception as e:
            print(f"❌ Failed to load tag #{tag}: {e}")
            continue

    context.close()

# Save CSV metadata
df = pd.DataFrame(results)
csv_path = os.path.join(output_dir, "instagram_scraped_data.csv")
df.to_csv(csv_path, index=False, encoding="utf-8")

print(f"\n🎯 Done. Scraped {len(df)} posts.")
print(f"📂 Images saved to: {output_dir}")
print(f"📝 Metadata saved to: {csv_path}")
