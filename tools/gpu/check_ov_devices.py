import openvino as ov
core = ov.Core()
print("Available devices:")
for device in core.available_devices:
    name = core.get_property(device, "FULL_DEVICE_NAME")
    print(f"- {device}: {name}")
