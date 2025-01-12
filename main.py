import os
import requests
from pyrogram import Client, filters
from playwright.sync_api import sync_playwright

# Telegram Bot Config
API_ID = "22469064"
API_HASH = "c05481978a217fdb11fa6774b15cba32"
BOT_TOKEN = "7942169109:AAHQeVhqf0hdM34qiyMVpAeSxjpKeZCfRMk"

# Terabox Session Cookies (if login is required)
TERABOX_COOKIES = {
    "cookie_name1": "PANWEB=1; csrfToken=tl2pqlIpZs-nq51FEEph_DW8; lang=en; TSID=3g9dXlXOottLSsQspciI9TLgJ3xdVY2m; __bid_n=18ea84278b11d086d64207; _ga=none; ndus=Yq7EMC3teHuiP-N36C2DBOIumBe6Fxt1NCf6es6w; browserid==H5Q7WeEh7u4Dhru6_RM96NUURbH7uwuPeAMiIjm4UCmk9ckdC2IS6TI04w0=; ndut_fmt=0783FEEEE10AA527370BA9BD3BFD896272C84225A1E2DFFBE420CE1B1BC7D99A; _ga_06ZNKL8C2E=none",
}

# Channel where files are stored
CHANNEL_ID = "-1002170811388"

app = Client("terabox_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def extract_download_link_playwright(terabox_url):
    """
    Extract direct download link from a Terabox shared link using Playwright.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Launch the browser in headless mode
        page = browser.new_page()

        # Go to the Terabox URL
        page.goto(terabox_url)

        # Wait for the page to load completely
        page.wait_for_selector(".download-button", timeout=30000)

        # Extract the download link
        download_button = page.query_selector(".download-button")
        if download_button:
            download_link = download_button.get_attribute("href")
            browser.close()
            return download_link
        browser.close()
        return None

def download_file(file_url, save_path):
    """
    Download the file from the direct download link.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
    }

    with requests.get(file_url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return save_path

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Welcome to the Terabox Downloader Bot! Send me a Terabox link to get started.")

@app.on_message(filters.text & ~filters.command([]))
async def handle_link(client, message):
    terabox_url = message.text.strip()

    await message.reply_text("Processing your link... Please wait.")

    # Step 1: Extract download link using Playwright
    direct_link = extract_download_link_playwright(terabox_url)
    if not direct_link:
        await message.reply_text("Failed to extract the download link. Please check your URL or try again.")
        return

    # Step 2: Download the file
    file_name = direct_link.split("/")[-1]
    save_path = os.path.join("downloads", file_name)
    os.makedirs("downloads", exist_ok=True)

    try:
        download_file(direct_link, save_path)
    except Exception as e:
        await message.reply_text(f"Failed to download the file: {str(e)}")
        return

    # Step 3: Send file to the user and channel
    try:
        # Send file to the user
        await client.send_document(
            chat_id=message.chat.id,
            document=save_path,
            caption=f"Here is your file: {file_name}",
        )

        # Send file to the channel
        await client.send_document(
            chat_id=CHANNEL_ID,
            document=save_path,
            caption=f"File stored from user {message.from_user.mention}: {file_name}",
        )
    except Exception as e:
        await message.reply_text(f"Failed to send the file: {str(e)}")
    finally:
        # Clean up the downloaded file
        if os.path.exists(save_path):
            os.remove(save_path)

if __name__ == "__main__":
    print("Bot is running...")
    app.run()