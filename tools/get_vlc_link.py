import sys
import os
from pathlib import Path

# Add project root to path so we can import config
sys.path.append(str(Path(__file__).parent.parent))

from onvif import ONVIFCamera
from config import CAMERA_IP, CAMERA_PORT, CAMERA_USER, CAMERA_PASSWORD

def get_vlc_link():
    """
    Connects to the camera via ONVIF, retrieves the RTSP Stream URI,
    and formats it with credentials for VLC.
    """
    print(f"Connecting to camera at {CAMERA_IP}:{CAMERA_PORT}...")
    
    try:
        # Initialize ONVIF client
        cam = ONVIFCamera(CAMERA_IP, CAMERA_PORT, CAMERA_USER, CAMERA_PASSWORD)
        
        # Create media service
        media = cam.create_media_service()
        
        # Get profiles
        profiles = media.GetProfiles()
        if not profiles:
            print("Error: No media profiles found on the camera.")
            return
        
        # Use the first profile (usually the highest resolution)
        token = profiles[0].token
        print(f"Using media profile: {profiles[0].Name} (Token: {token})")
        
        # Get Stream URI
        obj = media.create_type('GetStreamUri')
        obj.ProfileToken = token
        obj.StreamSetup = {
            'Stream': 'RTP-Unicast',
            'Transport': {'Protocol': 'RTSP'}
        }
        res = media.GetStreamUri(obj)
        
        uri = res.Uri
        
        # Inject credentials for VLC (rtsp://user:pass@ip:port/path)
        if uri.startswith("rtsp://") and "@" not in uri:
            vlc_link = uri.replace("rtsp://", f"rtsp://{CAMERA_USER}:{CAMERA_PASSWORD}@")
        else:
            vlc_link = uri
            
        print("\n" + "="*50)
        print("VLC NETWORK STREAM LINK:")
        print("="*50)
        print(vlc_link)
        print("="*50)
        print("\nHow to use:")
        print("1. Open VLC Media Player")
        print("2. Press Ctrl+N (Media -> Open Network Stream)")
        print("3. Paste the link above and click 'Play'")
            
    except Exception as e:
        print(f"\n❌ Error connecting to camera: {e}")
        print("\nTroubleshooting tips:")
        print(f"- Check if the camera IP ({CAMERA_IP}) is correct.")
        print(f"- Verify that port {CAMERA_PORT} is the correct ONVIF port.")
        print("- Ensure the username and password in your .env file are correct.")

if __name__ == "__main__":
    get_vlc_link()
