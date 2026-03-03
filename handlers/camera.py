import logging
import httpx
import os
import asyncio
import requests
import urllib3
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile
from onvif import ONVIFCamera
from config import CAMERA_IP, CAMERA_PORT, CAMERA_USER, CAMERA_PASSWORD

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
        # Format: rtsp://user:pass@ip:port/path
        if rtsp_uri.startswith("rtsp://") and "@" not in rtsp_uri:
            rtsp_uri = rtsp_uri.replace("rtsp://", f"rtsp://{CAMERA_USER}:{CAMERA_PASSWORD}@")

        logger.info(f"Attempting RTSP frame capture from: {rtsp_uri.split('@')[-1]}") # Log without credentials
        
        # ffmpeg command to capture 1 frame
        command = [
            "ffmpeg",
            "-y", # Overwrite output
            "-rtsp_transport", "tcp", # Use TCP for better reliability
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

@router.message(Command("camera"))
async def cmd_camera(message: types.Message, command: CommandObject):
    """Handles the /camera screenshot command."""
    args = command.args.strip().lower() if command.args else None
    
    if args == "screenshot":
        processing_msg = await message.answer("📸 Connecting to camera and capturing screenshot...")
        
        try:
            # 1. Get URIs from ONVIF
            snapshot_uri, rtsp_uri = await get_camera_snapshot()
            
            image_content = None
            
            # 2. Try Snapshot URI first if available
            if snapshot_uri:
                logger.info(f"Attempting snapshot from URI: {snapshot_uri}")
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
                    logger.info(f"Snapshot URI success: {len(image_content)} bytes")

            # 3. Fallback to RTSP if Snapshot failed
            if not image_content and rtsp_uri:
                logger.info("Snapshot URI failed or unavailable. Falling back to RTSP capture...")
                image_content = await capture_rtsp_frame(rtsp_uri)
                if image_content:
                    logger.info(f"RTSP capture success: {len(image_content)} bytes")

            # 4. Send the result
            if image_content:
                photo = BufferedInputFile(image_content, filename="screenshot.jpg")
                await message.answer_photo(photo, caption=f"🖼️ Camera Snapshot from {CAMERA_IP}")
                await processing_msg.delete()
            else:
                await message.answer("❌ Failed to capture image from both Snapshot URI and RTSP stream. The camera might be busy or credentials might be incorrect for the stream.")
                    
        except Exception as e:
            logger.error(f"Error in cmd_camera: {e}")
            await message.answer(f"❌ Error capturing screenshot: {str(e)}")
    else:
        await message.answer("Usage: <code>/camera screenshot</code>")
