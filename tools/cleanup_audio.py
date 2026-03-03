import os
import time
import shutil
import logging
from pathlib import Path
from config import AUDIO_FOLDER, AUDIO_CLEANUP_DAYS

logger = logging.getLogger(__name__)

def cleanup_old_audio():
    """
    Deletes files in AUDIO_FOLDER that are older than AUDIO_CLEANUP_DAYS.
    """
    if not AUDIO_FOLDER.exists():
        logger.info(f"Audio folder {AUDIO_FOLDER} does not exist. Skipping cleanup.")
        return

    if AUDIO_CLEANUP_DAYS <= 0:
        logger.info("AUDIO_CLEANUP_DAYS is set to 0 or less. Skipping cleanup.")
        return

    now = time.time()
    cutoff = now - (AUDIO_CLEANUP_DAYS * 86400)
    
    count = 0
    # Walk through the audio directory (which is structured by date folders)
    for date_folder in AUDIO_FOLDER.iterdir():
        if date_folder.is_dir():
            # Check if all files in the folder are older than the cutoff
            # Or if the folder itself is old enough. 
            # Given the structure audio/YYYY-MM-DD/, we can also check the folder modification time.
            folder_mtime = date_folder.stat().st_mtime
            if folder_mtime < cutoff:
                logger.info(f"Removing old audio folder: {date_folder}")
                try:
                    shutil.rmtree(date_folder)
                    count += 1
                except Exception as e:
                    logger.error(f"Error removing folder {date_folder}: {e}")
            else:
                # If the folder is not old enough, check individual files inside
                for file_path in date_folder.iterdir():
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                        logger.info(f"Removing old file: {file_path}")
                        try:
                            file_path.unlink()
                        except Exception as e:
                            logger.error(f"Error removing file {file_path}: {e}")

    logger.info(f"Cleanup finished. Removed {count} old folders/files.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cleanup_old_audio()
