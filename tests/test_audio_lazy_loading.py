import sys
import pytest
import importlib
from unittest.mock import patch, MagicMock

def test_audio_module_import_does_not_load_transformers():
    # Clear transformers and optimum from sys.modules if they were already loaded
    # Use a set to avoid 'dict changed size during iteration' if any other thread is active (though unlikely here)
    for mod in list(sys.modules.keys()):
        if mod.startswith('transformers') or mod.startswith('optimum'):
            del sys.modules[mod]
            
    # Import the module
    import handlers.audio
    importlib.reload(handlers.audio)
    
    # Assert heavy modules are NOT in sys.modules
    assert 'transformers' not in sys.modules
    assert 'optimum.intel.openvino' not in sys.modules

def test_whisper_pipeline_lazy_loading():
    # Clear cache
    import handlers.audio
    importlib.reload(handlers.audio)
    handlers.audio._whisper_pipe = None
    
    # Mock the modules
    mock_transformers = MagicMock()
    mock_optimum = MagicMock()
    
    with patch.dict('sys.modules', {
        'transformers': mock_transformers,
        'optimum.intel.openvino': mock_optimum
    }):
        # Setup mocks
        mock_transformers.AutoProcessor.from_pretrained.return_value = MagicMock()
        mock_optimum.OVModelForSpeechSeq2Seq.from_pretrained.return_value = MagicMock()
        mock_transformers.pipeline.return_value = MagicMock()
        
        # Initially None
        assert handlers.audio._whisper_model is None
        
        # Load
        model, processor, pipe = handlers.audio._get_whisper_components()
        
        # Verify it's loaded and cached
        assert model is not None
        assert handlers.audio._whisper_model is not None
        
        # Call again
        handlers.audio._get_whisper_components()
