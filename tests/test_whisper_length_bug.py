import pytest
import torch
from unittest.mock import MagicMock

def test_whisper_generation_length_constraint():
    # Simulate the error reported by the user
    # decoder_input_ids length + max_new_tokens > max_target_positions (448)
    
    max_target_positions = 448
    decoder_input_ids_len = 4
    max_new_tokens = 448
    
    # This is what triggered the error
    combined_len = decoder_input_ids_len + max_new_tokens
    assert combined_len > max_target_positions, "Should exceed limit"
    
    # Fix hypothesis: reduce max_new_tokens
    safe_max_new_tokens = 440
    assert (decoder_input_ids_len + safe_max_new_tokens) <= max_target_positions
