# Design Doc: Lazy Loading for Heavy Modules (Audio Transcription)

## Status
Proposed: 2026-03-31
Approved: 2026-03-31

## Context
The current implementation of `handlers/audio.py` performs heavy imports (`transformers`, `optimum.intel.openvino`) and initializes a Whisper transcription model (via OpenVINO) at the module level. This significantly increases the bot's initial startup time and memory footprint, even if the audio transcription feature is never used.

## Goals
- Reduce the bot's initial startup time by deferring heavy imports and model initialization.
- Load the Whisper model only when the first audio or voice message is received.
- Provide clear feedback to the user during the initial (one-time) model loading process.

## Architecture & Design

### Lazy Loading Strategy
We will use a **Singleton Loader Pattern** within `handlers/audio.py`.

1. **Move Imports**: Heavy imports will be moved from the module level into a local helper function.
2. **Global Cache**: A private global variable `_whisper_pipe` will store the loaded pipeline.
3. **Loader Function**: `_get_whisper_pipeline()` will handle the one-time initialization.

```python
_whisper_pipe = None

def _get_whisper_pipeline():
    global _whisper_pipe
    if _whisper_pipe is None:
        # 1. Perform heavy imports locally
        from transformers import AutoProcessor, pipeline
        from optimum.intel.openvino import OVModelForSpeechSeq2Seq
        
        # 2. Initialize model and processor
        # (Include GPU/CPU fallback logic here)
        
        # 3. Create pipeline
        _whisper_pipe = pipeline(...)
        
    return _whisper_pipe
```

### Handler Integration
The `handle_audio_message` handler will be updated:
1. When an audio/voice message arrives, it will first check if `_whisper_pipe` is `None`.
2. If `None`, it will send a "Loading transcription model, please wait..." message to the user.
3. It will then call `_get_whisper_pipeline()` (wrapped in `asyncio.to_thread` if needed, though initialization is synchronous).
4. Once loaded, it proceeds with transcription.
5. The "Loading..." message is updated or deleted after transcription starts or fails.

## Error Handling
- If `_get_whisper_pipeline()` fails, the error will be caught, logged, and reported to the user.
- `_whisper_pipe` will remain `None`, allowing for a retry on the next audio message.

## Testing Strategy
1. **Unit Test**: Verify that `handlers/audio.py` can be imported without triggering heavy dependencies (mocking the heavy modules).
2. **Integration Test**: Mock the `_get_whisper_pipeline()` function to ensure the handler correctly manages the "Loading..." message state.
3. **Manual Verification**: Run the bot and observe the startup time compared to the current version. Verify the model loads only on the first audio message.

## Success Criteria
- Bot startup time (from execution to polling start) is reduced by at least 50% (estimated based on model loading time).
- Audio transcription remains fully functional after the initial load.
- No heavy transcription-related modules are present in `sys.modules` until the first audio message is processed.
