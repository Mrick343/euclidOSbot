import asyncio
import requests
import json
import os
from aiogram import Bot, Dispatcher, types

# ------------------- CONFIG -------------------
TOKEN = "7254378450:AAEHF0DGXgAJjyj4z2-AHjlPdy0W33ESYjw"
CHANNEL_ID = "@your_channel_here"
BANNER_URL = "https://raw.githubusercontent.com/euclid-Devices/vendor_euclidOTA/16/assets/banner.png"
GITHUB_API_BUILDS = "https://api.github.com/repos/euclid-Devices/vendor_euclidOTA/contents/builds/16"
LOCAL_RECORD = "latest_builds.json"

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# ------------------- HELPERS -------------------
def fetch_json(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_all_json_urls():
    urls = []
    try:
        resp = requests.get(GITHUB_API_BUILDS, timeout=15)
        resp.raise_for_status()
        files = resp.json()
        for f in files:
            if f["name"].endswith(".json"):
                urls.append(f["download_url"])
    except Exception as e:
        print("Error fetching builds folder:", e)
    return urls

def format_build_message(device_name, data, include_banner=True):
    msg_parts = []
    if include_banner:
        msg_parts.append(f"<a href='{BANNER_URL}'>​</a>")  # invisible clickable banner

    msg_parts.append(f"<b>Latest EuclidOS build for {device_name}</b>\n\n")

    download_link = data.get("download", "#")
    flash_link = data.get("flashing", "#")
    changelog_link = data.get("changelogs", "#")
    maintainer = data.get("maintainer", "UNKNOWN")
    
    msg_parts.append(f"▪️ <b>Download:</b> <a href='{download_link}'>Link</a>\n")
    msg_parts.append(f"▪️ <b>Flashing Steps:</b> <a href='{flash_link}'>Link</a>\n")
    msg_parts.append(f"▪️ <b>Changelogs:</b> <a href='{changelog_link}'>Link</a>\n")
    msg_parts.append(f"▪️ <b>By:</b> {maintainer}\n")

    codename = data.get("device", "").strip()
    if codename.startswith("#"):
        codename = codename[1:]
    msg_parts.append(f"#A16 #{codename} #EuclidOS")

    return "\n".join(msg_parts)

# ------------------- LOAD LOCAL RECORD -------------------
if os.path.exists(LOCAL_RECORD):
    with open(LOCAL_RECORD, "r") as f:
        latest_builds = json.load(f)
else:
    latest_builds = {}

# ------------------- AUTO POST LOOP -------------------
async def auto_post_loop():
    while True:
        json_urls = get_all_json_urls()
        for url in json_urls:
            device_name = url.split("/")[-1].replace(".json", "")
            data = fetch_json(url)
            if not data or "response" not in data or len(data["response"]) == 0:
                continue

            latest = data["response"][-1]
            timestamp = latest.get("timestamp", 0)

            # Check if we already posted this build
            if latest_builds.get(device_name, 0) < timestamp:
                msg = format_build_message(device_name, latest, include_banner=True)
                await bot.send_message(CHANNEL_ID, msg, disable_web_page_preview=False)
                latest_builds[device_name] = timestamp

                # Update local record
                with open(LOCAL_RECORD, "w") as f:
                    json.dump(latest_builds, f)

        await asyncio.sleep(300)  # Check every 5 minutes

# ------------------- START BOT -------------------
async def main():
    asyncio.create_task(auto_post_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())