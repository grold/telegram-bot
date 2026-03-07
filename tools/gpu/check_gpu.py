import openvino as ov
core = ov.Core()
try:
    core.get_property("GPU", "FULL_DEVICE_NAME")
    print("GPU property check passed.")
except Exception as e:
    print(f"GPU check failed: {e}")

try:
    print("Trying to load a dummy model to GPU...")
    # This might be slow but will show the error
    # Actually, just querying the device should be enough
except:
    pass
