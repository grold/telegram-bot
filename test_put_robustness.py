import torch
import numpy as np

def put_robust(value):
    if isinstance(value, torch.Tensor):
        if value.ndim == 0:
            new_tokens = [value.item()]
        elif value.ndim == 1:
            new_tokens = value.tolist()
        else:
            new_tokens = value[0].tolist()
    elif isinstance(value, int):
        new_tokens = [value]
    else:
        try:
            new_tokens = [int(value)]
        except:
            return []
    return new_tokens

# Test cases
print("Int:", put_robust(5))
print("0-D Tensor:", put_robust(torch.tensor(5)))
print("1-D Tensor:", put_robust(torch.tensor([5, 6])))
print("2-D Tensor:", put_robust(torch.tensor([[5, 6]])))
