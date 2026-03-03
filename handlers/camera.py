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
    """Connects to the ONVIF camera and retrieves a snapshot URI."""
    try:
        # Note: onvif-zeep is synchronous in its connection/calls
        def connect_and_get_uri():
            cam = ONVIFCamera(CAMERA_IP, CAMERA_PORT, CAMERA_USER, CAMERA_PASSWORD)
            media = cam.create_media_service()
            profiles = media.GetProfiles()
            if not profiles:
                raise Exception("No media profiles found on camera.")
            
            token = profiles[0].token
            obj = media.create_type('GetSnapshotUri')
            obj.ProfileToken = token
            res = media.GetSnapshotUri(obj)
            return res.Uri

        # Run synchronous ONVIF calls in a thread
        return await asyncio.to_thread(connect_and_get_uri)
    except Exception as e:
        logger.error(f"Failed to get camera snapshot URI: {e}")
        raise

@router.message(Command("camera"))
async def cmd_camera(message: types.Message, command: CommandObject):
    """Handles the /camera screenshot command."""
    args = command.args.strip().lower() if command.args else None
    
    if args == "screenshot":
        processing_msg = await message.answer("📸 Connecting to camera and capturing screenshot...")
        
        try:
            # 1. Get Snapshot URI
            snapshot_uri = await get_camera_snapshot()
            logger.info(f"Retrieved snapshot URI: {snapshot_uri}")
            
            # 2. Download the image
            # Many cameras use Digest authentication for the snapshot URL.
            # requests handles this much more robustly than httpx.
            def download_image():
                # Try Digest Auth first
                try:
                    response = requests.get(
                        snapshot_uri, 
                        auth=HTTPDigestAuth(CAMERA_USER, CAMERA_PASSWORD), 
                        timeout=15.0,
                        verify=False
                    )
                    
                    # If 401, try Basic Auth
                    if response.status_code == 401:
                        response = requests.get(
                            snapshot_uri, 
                            auth=HTTPBasicAuth(CAMERA_USER, CAMERA_PASSWORD), 
                            timeout=15.0,
                            verify=False
                        )
                    
                    # If still not 200, try without auth
                    if response.status_code != 200:
                        response = requests.get(snapshot_uri, timeout=15.0, verify=False)
                        
                    return response
                except Exception as e:
                    logger.error(f"Download thread error: {e}")
                    raise

            # Run synchronous requests in a thread to avoid blocking the event loop
            response = await asyncio.to_thread(download_image)
            
            if response.status_code == 200:
                if not response.content:
                    await message.answer("❌ Camera returned an empty image. Snapshot failed.")
                    return

                logger.info(f"Successfully downloaded snapshot: {len(response.content)} bytes")
                # 3. Send the image
                photo = BufferedInputFile(response.content, filename="screenshot.jpg")
                await message.answer_photo(photo, caption=f"🖼️ Camera Snapshot from {CAMERA_IP}")
                await processing_msg.delete()
            else:
                await message.answer(f"❌ Failed to download snapshot. Status: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error in cmd_camera: {e}")
            await message.answer(f"❌ Error capturing screenshot: {str(e)}")
    else:
        await message.answer("Usage: <code>/camera screenshot</code>")
