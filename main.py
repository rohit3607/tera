import os
import requests
from pyrogram import Client, filters
from bs4 import BeautifulSoup

# Telegram Bot Config
API_ID = "your_api_id"
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

# Terabox Session Cookies (if login is required)
TERABOX_COOKIES = {
    "cookie_name1": "cookie_value1",
    "cookie_name2": "cookie_value2",
}

app = Client("terabox_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def extract_download_link(terabox_url):
    """
    Extract direct download link from a Terabox shared link.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
    }

    response = requests.get(terabox_url, headers=headers, cookies=TERABOX_COOKIES)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    download_button = soup.find("a", {"class": "download-button"})
    
    if download_button:
        return download_button["href"]  # Direct download URL
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

@app.on_message(filters.text & ~filters.command)
async def handle_link(client, message):
    terabox_url = message.text.strip()

    await message.reply_text("Processing your link... Please wait.")

    # Step 1: Extract download link
    direct_link = extract_download_link(terabox_url)
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

    # Step 3: Send file to the user
    try:
        await client.send_document(
            chat_id=message.chat.id,
            document=save_path,
            caption=f"Here is your file: {file_name}",
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
