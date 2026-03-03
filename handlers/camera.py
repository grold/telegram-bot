import logging
import httpx
import os
import asyncio
import requests
import urllib3
from datetime import datetime
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, FSInputFile
from onvif import ONVIFCamera
from config import CAMERA_IP, CAMERA_PORT, CAMERA_USER, CAMERA_PASSWORD, SCREENSHOTS_DIR, MAX_VIDEO_DURATION

# Disable insecure request warnings for self-signed camera certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)
router = Router()

async def get_camera_snapshot():
    """Connects to the ONVIF camera and retrieves snapshot or RTSP URIs."""
    try:
        def connect_and_get_uris():
            cam = ONVIFCamera(CAMERA_IP, CAMERA_PORT, CAMERA_USER, CAMERA_PASSWORD)
            media = cam.create_media_service()
            profiles = media.GetProfiles()
            if not profiles:
                raise Exception("No media profiles found on camera.")
            
            token = profiles[0].token
            
            # 1. Try to get Snapshot URI
            snapshot_uri = None
            try:
                obj = media.create_type('GetSnapshotUri')
                obj.ProfileToken = token
                res = media.GetSnapshotUri(obj)
                snapshot_uri = res.Uri
            except Exception as e:
                logger.warning(f"Could not get Snapshot URI: {e}")

            # 2. Try to get RTSP Stream URI as fallback
            rtsp_uri = None
            try:
                obj = media.create_type('GetStreamUri')
                obj.ProfileToken = token
                obj.StreamSetup = {
                    'Stream': 'RTP-Unicast',
                    'Transport': {'Protocol': 'RTSP'}
                }
                res = media.GetStreamUri(obj)
                rtsp_uri = res.Uri
            except Exception as e:
                logger.warning(f"Could not get Stream URI: {e}")

            return snapshot_uri, rtsp_uri

        return await asyncio.to_thread(connect_and_get_uris)
    except Exception as e:
        logger.error(f"Failed to get camera URIs: {e}")
        raise

async def capture_rtsp_frame(rtsp_uri: str):
    """Uses ffmpeg to capture a single frame from an RTSP stream."""
    try:
        # Inject credentials into RTSP URI if they aren't there
        if rtsp_uri.startswith("rtsp://") and "@" not in rtsp_uri:
            rtsp_uri = rtsp_uri.replace("rtsp://", f"rtsp://{CAMERA_USER}:{CAMERA_PASSWORD}@")

        logger.info(f"Attempting RTSP frame capture from: {rtsp_uri.split('@')[-1]}")
        
        command = [
            "ffmpeg",
            "-y",
            "-rtsp_transport", "tcp",
            "-i", rtsp_uri,
            "-frames:v", "1",
            "-f", "image2pipe",
            "-vcodec", "mjpeg",
            "pipe:1"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0 and stdout:
            return stdout
        else:
            error_msg = stderr.decode().splitlines()[-1] if stderr else "Unknown ffmpeg error"
            logger.error(f"ffmpeg capture failed: {error_msg}")
            return None
    except Exception as e:
        logger.error(f"RTSP capture exception: {e}")
        return None

async def record_rtsp_video(rtsp_uri: str, duration: int, output_path: os.PathLike):
    """Uses ffmpeg to record a video from an RTSP stream for a given duration."""
    try:
        # Inject credentials into RTSP URI if they aren't there
        if rtsp_uri.startswith("rtsp://") and "@" not in rtsp_uri:
            rtsp_uri = rtsp_uri.replace("rtsp://", f"rtsp://{CAMERA_USER}:{CAMERA_PASSWORD}@")

        logger.info(f"Attempting RTSP video record from: {rtsp_uri.split('@')[-1]} for {duration}s")
        
        command = [
            "ffmpeg",
            "-y",
            "-rtsp_transport", "tcp",
            "-timeout", "5000000",  # 5 seconds timeout for RTSP connection
            "-i", rtsp_uri,
            "-t", str(duration),
            "-vcodec", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-pix_fmt", "yuv420p",
            "-an",
            "-movflags", "+faststart",
            str(output_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return True
        else:
            stderr_output = stderr.decode()
            error_msg = stderr_output.splitlines()[-1] if stderr_output else "Unknown ffmpeg error"
            logger.error(f"ffmpeg recording failed with code {process.returncode}. Last error: {error_msg}")
            logger.debug(f"Full ffmpeg stderr: {stderr_output}")
            return False
    except Exception as e:
        logger.error(f"RTSP video record exception: {e}")
        return False

@router.message(Command("camera"))
async def cmd_camera(message: types.Message, command: CommandObject):
    """Handles the /camera screenshot and /camera video [sec] commands."""
    args = command.args.split() if command.args else []
    subcommand = args[0].lower() if args else None
    
    if subcommand == "screenshot":
        processing_msg = await message.answer("📸 Connecting to camera and capturing screenshot...")
        
        try:
            snapshot_uri, rtsp_uri = await get_camera_snapshot()
            image_content = None
            
            # 1. Try Snapshot URI
            if snapshot_uri:
                def download_image():
                    try:
                        response = requests.get(
                            snapshot_uri, 
                            auth=HTTPDigestAuth(CAMERA_USER, CAMERA_PASSWORD), 
                            timeout=10.0,
                            verify=False
                        )
                        if response.status_code == 401:
                            response = requests.get(
                                snapshot_uri, 
                                auth=HTTPBasicAuth(CAMERA_USER, CAMERA_PASSWORD), 
                                timeout=10.0,
                                verify=False
                            )
                        return response if response.status_code == 200 and response.content else None
                    except Exception:
                        return None

                response = await asyncio.to_thread(download_image)
                if response:
                    image_content = response.content

            # 2. Fallback to RTSP
            if not image_content and rtsp_uri:
                logger.info("Falling back to RTSP capture...")
                image_content = await capture_rtsp_frame(rtsp_uri)

            # 3. Save and Send
            if image_content:
                # Ensure directory exists
                SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
                
                # Create timestamped filename
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                filename = f"snapshot_{timestamp}.jpg"
                filepath = SCREENSHOTS_DIR / filename
                
                # Save to disk
                with open(filepath, "wb") as f:
                    f.write(image_content)
                logger.info(f"Saved snapshot to {filepath}")

                # Send to Telegram
                photo = BufferedInputFile(image_content, filename=filename)
                await message.answer_photo(photo, caption=f"🖼️ Camera Snapshot from {CAMERA_IP}\nSaved as: <code>{filename}</code>")
                await processing_msg.delete()
            else:
                await message.answer("❌ Failed to capture image from both Snapshot URI and RTSP stream.")
                    
        except Exception as e:
            logger.error(f"Error in cmd_camera screenshot: {e}")
            await message.answer(f"❌ Error capturing screenshot: {str(e)}")
            
    elif subcommand == "video":
        duration = 5
        if len(args) > 1:
            try:
                duration = int(args[1])
                if duration <= 0:
                    duration = 5
                elif duration > MAX_VIDEO_DURATION:
                    duration = MAX_VIDEO_DURATION
            except ValueError:
                duration = 5

        processing_msg = await message.answer(f"🎥 Connecting to camera and recording {duration}s video...")
        
        try:
            _, rtsp_uri = await get_camera_snapshot()
            
            if rtsp_uri:
                # Ensure directory exists
                SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
                
                # Create timestamped filename
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                filename = f"video_{timestamp}.mp4"
                filepath = SCREENSHOTS_DIR / filename
                
                success = await record_rtsp_video(rtsp_uri, duration, filepath)
                
                if success and filepath.exists() and filepath.stat().st_size > 0:
                    # Send to Telegram
                    video = FSInputFile(filepath)
                    await message.answer_video(video, caption=f"🎥 Camera Video from {CAMERA_IP} ({duration}s)\nSaved as: <code>{filename}</code>")
                    await processing_msg.delete()
                else:
                    await message.answer("❌ Failed to record video from RTSP stream.")
            else:
                await message.answer("❌ No RTSP stream available for video recording.")
                    
        except Exception as e:
            logger.error(f"Error in cmd_camera video: {e}")
            await message.answer(f"❌ Error recording video: {str(e)}")
            
    else:
        await message.answer("Usage:\n<code>/camera screenshot</code>\n<code>/camera video [sec]</code>")
