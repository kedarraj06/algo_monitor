#!/usr/bin/env python3
"""
download_models.py
-----------------
Downloads required AI models for AlgoShieldAI.

This script downloads:
1. Phi-3-mini-4k-instruct GGUF model from HuggingFace

Run this script once before using the /suggest endpoint for the first time,
or the model will be downloaded automatically on first use.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "model" / "slm"

HF_MODEL_REPO = "microsoft/Phi-3-mini-4k-instruct-gguf"
HF_MODEL_FILE = "Phi-3-mini-4k-instruct-q4.gguf"


def download_phi3_model():
    """Download Phi-3 model from HuggingFace."""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("[ERROR] huggingface-hub not installed.")
        print("Run: pip install huggingface-hub")
        sys.exit(1)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    output_path = MODEL_DIR / HF_MODEL_FILE

    if output_path.exists():
        print(f"[INFO] Model already exists at {output_path}")
        print(f"Size: {output_path.stat().st_size / (1024 * 1024):.1f} MB")
        return

    print(f"[INFO] Downloading {HF_MODEL_REPO} from HuggingFace...")
    print(f"[INFO] This is ~2.5GB, please wait...")

    try:
        downloaded_path = hf_hub_download(
            repo_id=HF_MODEL_REPO,
            filename=HF_MODEL_FILE,
            local_dir=str(MODEL_DIR),
            local_dir_use_symlinks=False,
        )
        print(f"[SUCCESS] Model downloaded to {downloaded_path}")
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("AlgoShieldAI Model Downloader")
    print("=" * 50)
    print()
    download_phi3_model()
    print()
    print("Done! You can now use the /suggest endpoint.")
