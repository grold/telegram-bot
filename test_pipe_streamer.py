import torch
import numpy as np
import time
from transformers import pipeline, AutoProcessor
from transformers.generation import BaseStreamer
from optimum.intel.openvino import OVModelForSpeechSeq2Seq

class SimpleStreamer(BaseStreamer):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.tokens = []
    def put(self, value):
        if isinstance(value, torch.Tensor):
            if value.ndim > 1:
                token = value[0].tolist()
            else:
                token = value.tolist()
        else:
            token = [value] # Handle int
        self.tokens.extend(token)
        text = self.tokenizer.decode(self.tokens, skip_special_tokens=True)
        print(f"STREAM TEXT: {text}")
    def end(self):
        print("STREAM END")

MODEL_ID = "OpenVINO/whisper-base-int8-ov"
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = OVModelForSpeechSeq2Seq.from_pretrained(MODEL_ID, device="CPU")

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    chunk_length_s=30,
    stride_length_s=5,
)

# Create 10 seconds of dummy audio (silent)
dummy_audio = np.zeros(16000 * 10, dtype=np.float32)

streamer = SimpleStreamer(processor.tokenizer)

print("Starting pipe with streamer...")
try:
    result = pipe(dummy_audio, generate_kwargs={"streamer": streamer, "num_beams": 1, "max_new_tokens": 440})
    print("\nResult length:", len(result['text']))
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
