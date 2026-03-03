import logging
import httpx
import os
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile
from onvif import ONVIFCamera
from config import CAMERA_IP, CAMERA_PORT, CAMERA_USER, CAMERA_PASSWORD

logger = logging.getLogger(__name__)
router = Router()

async def get_camera_snapshot():
    """Connects to the ONVIF camera and retrieves a snapshot URI."""
    try:
        # Note: onvif-zeep is synchronous in its connection/calls
        # For a more robust async implementation, we would wrap these in run_in_executor
        # but for a simple bot command, direct usage is usually okay if it doesn't block too long.
        
        # Initialize ONVIF client
        # We assume the wsdl files are available in the package
        cam = ONVIFCamera(CAMERA_IP, CAMERA_PORT, CAMERA_USER, CAMERA_PASSWORD)
        
        # Create media service
        media = cam.create_media_service()
        
        # Get profiles
        profiles = media.GetProfiles()
        if not profiles:
            raise Exception("No media profiles found on camera.")
        
        token = profiles[0].token
        
        # Get Snapshot URI
        # Some cameras might require different versions of GetSnapshotUri depending on ONVIF version
        # but media.GetSnapshotUri is the standard for Media1.
        obj = media.create_type('GetSnapshotUri')
        obj.ProfileToken = token
        res = media.GetSnapshotUri(obj)
        
        return res.Uri
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
            # Many cameras use Digest or Basic auth for the snapshot URL itself
            # We'll try with Basic auth first as it's common for snapshot URIs
            async with httpx.AsyncClient(verify=False) as client:
                # Use common camera auth if the URL doesn't already contain credentials
                auth = httpx.BasicAuth(CAMERA_USER, CAMERA_PASSWORD)
                response = await client.get(snapshot_uri, auth=auth, timeout=10.0)
                
                if response.status_code != 200:
                    # Retry without auth in case it's public or already has tokens
                    response = await client.get(snapshot_uri, timeout=10.0)
                
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
