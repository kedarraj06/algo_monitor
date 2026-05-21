"""
rag_pipeline.py
---------------
RAG (Retrieval-Augmented Generation) pipeline for AlgoShieldAI.

Responsibilities:
  1. Load the ChromaDB vectorstore (built by build_knowledge_base.py)
  2. Retrieve the top-k most relevant knowledge base chunks for a given query
  3. Optionally pass context + query to a local SLM (Phi-3-mini via llama-cpp)
  4. Return retrieved context and SLM response

The pipeline degrades gracefully:
  - If ChromaDB is not built yet -> returns empty context
  - If SLM is not downloaded -> skips SLM, returns context-only
  - Timeouts are enforced to prevent hanging
"""

import os
import logging
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent

VECTORSTORE_DIR = Path(
    os.getenv("VECTORSTORE_DIR", str(_BACKEND_DIR / "model" / "vectorstore"))
)
SLM_MODEL_DIR = Path(os.getenv("SLM_MODEL_DIR", str(_BACKEND_DIR / "model" / "slm")))
HF_MODEL_REPO = "microsoft/Phi-3-mini-4k-instruct-gguf"
HF_MODEL_FILE = "Phi-3-mini-4k-instruct-q4.gguf"
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "algoshield_knowledge")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

TOP_K = int(os.getenv("RAG_TOP_K", "4"))
SLM_MAX_TOKENS = int(os.getenv("SLM_MAX_TOKENS", "250"))
SLM_TIMEOUT = int(os.getenv("SLM_TIMEOUT_SEC", "30"))

# ---------------------------------------------------------------------------
# Lazy-loaded singletons
# ---------------------------------------------------------------------------
_chroma_collection = None
_slm_model = None
_chroma_available = None
_slm_available = None


def _init_chroma() -> bool:
    """Initialize ChromaDB collection lazily. Returns True if available."""
    global _chroma_collection, _chroma_available

    if _chroma_available is not None:
        return _chroma_available

    try:
        import chromadb
        from chromadb.utils import embedding_functions

        if not VECTORSTORE_DIR.exists():
            logger.warning(
                f"[RAG] Vectorstore not found at {VECTORSTORE_DIR}. "
                "Run: python scripts/build_knowledge_base.py"
            )
            _chroma_available = False
            return False

        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))
        collections = [c.name for c in client.list_collections()]

        if COLLECTION_NAME not in collections:
            logger.warning(
                f"[RAG] Collection '{COLLECTION_NAME}' not found. "
                "Run: python scripts/build_knowledge_base.py"
            )
            _chroma_available = False
            return False

        _chroma_collection = client.get_collection(
            name=COLLECTION_NAME, embedding_function=embedding_fn
        )
        logger.info(
            f"[RAG] ChromaDB ready -- {_chroma_collection.count()} chunks loaded"
        )
        _chroma_available = True
        return True

    except ImportError:
        logger.warning(
            "[RAG] chromadb or sentence-transformers not installed. RAG disabled."
        )
        _chroma_available = False
        return False
    except Exception as e:
        logger.error(f"[RAG] ChromaDB init failed: {e}")
        _chroma_available = False
        return False


def _download_model_from_huggingface() -> Optional[Path]:
    """Download Phi-3 model from HuggingFace if not already cached."""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        logger.warning(
            "[SLM] huggingface-hub not installed. Run: pip install huggingface-hub"
        )
        return None

    SLM_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    local_path = SLM_MODEL_DIR / HF_MODEL_FILE

    if local_path.exists():
        logger.info(f"[SLM] Model already exists at {local_path}")
        return local_path

    try:
        logger.info(f"[SLM] Downloading {HF_MODEL_REPO} from HuggingFace...")
        downloaded_path = hf_hub_download(
            repo_id=HF_MODEL_REPO,
            filename=HF_MODEL_FILE,
            local_dir=str(SLM_MODEL_DIR),
            local_dir_use_symlinks=False,
        )
        logger.info(f"[SLM] Downloaded model to {downloaded_path}")
        return Path(downloaded_path)
    except Exception as e:
        logger.error(f"[SLM] Download failed: {e}")
        return None


def _init_slm() -> bool:
    """Initialize the Phi-3-mini SLM lazily. Returns True if available."""
    global _slm_model, _slm_available

    if _slm_available is not None:
        return _slm_available

    model_path = _download_model_from_huggingface()
    if not model_path or not model_path.exists():
        logger.info(
            "[SLM] Model not available. Will attempt download on first request."
        )
        _slm_available = False
        return False

    try:
        from llama_cpp import Llama

        logger.info(f"[SLM] Loading Phi-3-mini from {model_path}...")
        _slm_model = Llama(
            model_path=str(model_path), n_ctx=2048, n_threads=4, verbose=False
        )
        logger.info("[SLM] Phi-3-mini loaded successfully")
        _slm_available = True
        return True

    except ImportError:
        logger.info(
            "[SLM] llama-cpp-python not installed. Run: pip install llama-cpp-python"
        )
        _slm_available = False
        return False
    except Exception as e:
        logger.error(f"[SLM] Failed to load model: {e}")
        _slm_available = False
        return False

    gguf_files = list(SLM_MODEL_DIR.glob("*.gguf"))
    if not gguf_files:
        logger.info(f"[SLM] No .gguf files in {SLM_MODEL_DIR}. SLM disabled.")
        _slm_available = False
        return False

    model_path = gguf_files[0]

    try:
        from llama_cpp import Llama

        logger.info(f"[SLM] Loading Phi-3-mini from {model_path}...")
        _slm_model = Llama(
            model_path=str(model_path), n_ctx=2048, n_threads=4, verbose=False
        )
        logger.info("[SLM] Phi-3-mini loaded successfully")
        _slm_available = True
        return True

    except ImportError:
        logger.info("[SLM] llama-cpp-python not installed. SLM disabled.")
        _slm_available = False
        return False
    except Exception as e:
        logger.error(f"[SLM] Failed to load model: {e}")
        _slm_available = False
        return False


def retrieve_context(query: str, top_k: int = TOP_K) -> list:
    """
    Retrieve top-k relevant knowledge base chunks for the given query.

    Returns:
        List of dicts: {text, source, section, score}
        Empty list if ChromaDB is unavailable.
    """
    if not _init_chroma():
        return []

    try:
        count = _chroma_collection.count()
        if count == 0:
            return []

        results = _chroma_collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            similarity = max(0.0, 1.0 - float(dist))
            retrieved.append(
                {
                    "text": doc,
                    "source": meta.get("source", "unknown"),
                    "section": meta.get("section", ""),
                    "score": round(similarity, 4),
                }
            )

        if retrieved:
            logger.debug(
                f"[RAG] Retrieved {len(retrieved)} chunks (top score: {retrieved[0]['score']:.3f})"
            )
        return retrieved

    except Exception as e:
        logger.error(f"[RAG] Retrieval failed: {e}")
        return []


def run_slm(query: str, context_chunks: list) -> Optional[Dict[str, str]]:
    """
    Run the Phi-3-mini SLM to generate a suggestion given query + context.

    Returns:
        Dict with keys: issue, explanation, fix.
        Returns None if SLM is unavailable or JSON parsing fails.
    """
    if not _init_slm():
        return None

    # Build concise context string (cap total length for SLM)
    context_parts = []
    total_chars = 0
    max_context_chars = 1500

    for chunk in context_chunks:
        text = chunk["text"]
        if total_chars + len(text) > max_context_chars:
            remaining = max_context_chars - total_chars
            if remaining > 100:
                context_parts.append(text[:remaining] + "...")
            break
        context_parts.append(text)
        total_chars += len(text)

    context_str = (
        "\n\n---\n\n".join(context_parts)
        if context_parts
        else "No relevant context found."
    )

    # Phi-3 instruct format for strict JSON
    system_part = (
        "<|system|>\nYou are a smart contract security expert specializing in Algorand TEAL. "
        "Provide concise, actionable fix recommendations based ONLY on the provided context. "
        "You MUST respond with valid JSON ONLY. No markdown blocks, no other text. "
        'Format: {"issue": "...", "explanation": "...", "fix": "..."}\n<|end|>\n'
    )
    user_part = f"<|user|>\nContext:\n{context_str}\n\nQuery:\n{query}\n<|end|>\n"
    assist_part = "<|assistant|>\n{"

    prompt = system_part + user_part + assist_part

    try:
        logger.info("[SLM] Generating response...")
        response = _slm_model(
            prompt,
            max_tokens=SLM_MAX_TOKENS,
            stop=["<|end|>", "<|user|>"],
            temperature=0.2,
        )
        output_text = "{" + response["choices"][0]["text"].strip()

        # Safe JSON parse with fallback regex trap
        try:
            parsed = json.loads(output_text)
            return parsed
        except json.JSONDecodeError:
            # Fallback: regex search for keys if it broke format
            match_issue = re.search(r'"issue"\s*:\s*"([^"]+)"', output_text)
            match_exp = re.search(r'"explanation"\s*:\s*"([^"]+)"', output_text)
            match_fix = re.search(r'"fix"\s*:\s*"([^"]+)"', output_text)
            if match_issue and match_exp:
                return {
                    "issue": match_issue.group(1),
                    "explanation": match_exp.group(1),
                    "fix": match_fix.group(1)
                    if match_fix
                    else "Review context for fix.",
                }
            logger.warning(f"[SLM] Failed to parse valid JSON from: {output_text}")
            return None

    except Exception as e:
        logger.error(f"[SLM] Inference failed: {e}")
        return None
