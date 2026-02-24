import os
import httpx
import logging
from typing import Optional
from config.settings import config

logger = logging.getLogger(__name__)

AVATAR_DIR = os.path.join(os.getcwd(), "static", "avatars")

# Ensure directory exists
os.makedirs(AVATAR_DIR, exist_ok=True)

async def get_or_download_avatar(telegram_id: int) -> Optional[str]:
    """
    Checks if avatar for telegram_id exists locally.
    If not, attempts to download it via Telegram Bot API.
    Returns the path relative to the project root or None.
    """
    file_name = f"{telegram_id}.jpg"
    file_path = os.path.join(AVATAR_DIR, file_name)
    
    # 1. Check if already exists
    if os.path.exists(file_path):
        return file_path
        
    # 2. If not, try to download
    token = config.BOT_TOKEN.get_secret_value()
    async with httpx.AsyncClient() as client:
        try:
            # Normalize ID for getChat
            chat_id = telegram_id
            if chat_id > 0 and chat_id < 10**12:
                chat_id = int(f"-100{chat_id}")
                
            logger.info(f"Downloading photo for {telegram_id} (chat_id: {chat_id})")
            
            # Step A: Get Chat info
            chat_resp = await client.get(f"https://api.telegram.org/bot{token}/getChat?chat_id={chat_id}")
            if chat_resp.status_code != 200:
                logger.error(f"getChat failed for {chat_id}: {chat_resp.text}")
                return None
                
            chat_info = chat_resp.json().get("result", {})
            photo = chat_info.get("photo")
            if not photo:
                logger.warning(f"No photo found for {chat_id}")
                return None
                
            file_id = photo.get("big_file_id") or photo.get("small_file_id")
            
            # Step B: Get File Path
            file_resp = await client.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}")
            if file_resp.status_code != 200:
                logger.error(f"getFile failed for {file_id}")
                return None
                
            t_file_path = file_resp.json().get("result", {}).get("file_path")
            if not t_file_path:
                return None
                
            # Step C: Download actual file
            photo_url = f"https://api.telegram.org/file/bot{token}/{t_file_path}"
            
            async with client.stream("GET", photo_url) as r:
                if r.status_code == 200:
                    with open(file_path, "wb") as f:
                        async for chunk in r.aiter_bytes():
                            f.write(chunk)
                    logger.info(f"Successfully saved avatar for {telegram_id}")
                    return file_path
                else:
                    logger.error(f"Failed to download photo from {photo_url}")
                    
        except Exception as e:
            logger.error(f"Error in get_or_download_avatar for {telegram_id}: {e}")
            
    return None
