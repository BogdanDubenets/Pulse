import os
import logging
from api.utils.storage import AVATAR_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diagnose_photos")

def diagnose():
    logger.info(f"AVATAR_DIR: {AVATAR_DIR}")
    logger.info(f"Exists: {os.path.exists(AVATAR_DIR)}")
    
    if os.path.exists(AVATAR_DIR):
        files = os.listdir(AVATAR_DIR)
        logger.info(f"Total files: {len(files)}")
        if files:
            logger.info(f"Sample files: {files[:5]}")
    else:
        logger.error("AVATAR_DIR DOES NOT EXIST!")

if __name__ == "__main__":
    diagnose()
