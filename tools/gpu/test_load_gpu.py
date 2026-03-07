from transformers import AutoProcessor
from optimum.intel.openvino import OVModelForSpeechSeq2Seq
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_ID = "OpenVINO/whisper-base-int8-ov"
try:
    print(f"Loading Whisper model {MODEL_ID} on Intel GPU...")
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = OVModelForSpeechSeq2Seq.from_pretrained(MODEL_ID, device="GPU")
    print("Model loaded successfully on Intel GPU!")
except Exception as e:
    print(f"FAILED to load on Intel GPU: {e}")
    # Try to load on CPU as a comparison
    try:
        model = OVModelForSpeechSeq2Seq.from_pretrained(MODEL_ID, device="CPU")
        print("Model loaded successfully on CPU.")
    except Exception as e2:
        print(f"FAILED to load on CPU too: {e2}")
