import torch

# Check if CUDA is available
if torch.cuda.is_available():
    print(f"CUDA is available! Using {torch.cuda.get_device_name(0)}.")
else:
    print("CUDA is not available. Using CPU.")
