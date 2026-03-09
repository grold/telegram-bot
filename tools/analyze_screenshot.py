import asyncio
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

async def analyze_screenshot(file_path: str):
    """
    Calls the Gemini CLI to analyze a screenshot.
    Mimics the behavior of generate_docs.sh but for images.
    """
    if not Path(file_path).exists():
        logger.error(f"File not found: {file_path}")
        return None

    logger.info(f"Analyzing screenshot {file_path}...")
    
    # Prompt for Gemini
    prompt = f"Analyze this camera snapshot and describe any activity or notable objects. @{file_path}"
    
    command = [
        "gemini",
        "-m", "gemini-2.5-flash",
        "-p", prompt
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            result = stdout.decode().strip()
            return result
        else:
            error_msg = stderr.decode().strip()
            logger.error(f"Gemini CLI error: {error_msg}")
            return None
    except Exception as e:
        logger.error(f"Exception during Gemini CLI execution: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_screenshot.py <image_path>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    result = asyncio.run(analyze_screenshot(image_path))
    if result:
        print(result)
    else:
        sys.exit(1)
