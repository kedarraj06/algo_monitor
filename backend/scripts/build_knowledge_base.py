"""
build_knowledge_base.py
-----------------------
Loads all markdown files from the knowledge_base/ directory,
chunks them intelligently (respecting section boundaries),
generates sentence-transformer embeddings, and upserts them
into a ChromaDB vector store at model/vectorstore/.

Run from the project root:
    python scripts/build_knowledge_base.py
"""

import os
import re
import sys
import hashlib
from pathlib import Path

# ---------------------------------------------------------------------------
# Path configuration (resolved relative to this script's location)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
VECTORSTORE_DIR = PROJECT_ROOT / "model" / "vectorstore"

# Chunking parameters (in characters, not tokens — conservative for ~300-400 token chunks)
CHUNK_SIZE = 1500        # ~375 tokens at 4 chars/token average
CHUNK_OVERLAP = 300      # ~75 tokens overlap
MIN_CHUNK_SIZE = 200     # Discard chunks smaller than this

# ChromaDB collection name
COLLECTION_NAME = "algoshield_knowledge"

# Embedding model (local, no API key required)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def check_dependencies() -> bool:
    """Verify required packages are installed before proceeding."""
    missing = []
    try:
        import chromadb  # noqa
    except ImportError:
        missing.append("chromadb")
    try:
        from sentence_transformers import SentenceTransformer  # noqa
    except ImportError:
        missing.append("sentence-transformers")

    if missing:
        print(f"[ERROR] Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    return True


def load_markdown_files(kb_dir: Path) -> list[dict]:
    """
    Load all .md files from the knowledge base directory.
    Returns a list of {source, content} dicts.
    """
    documents = []
    md_files = list(kb_dir.glob("*.md"))

    if not md_files:
        print(f"[WARN] No markdown files found in {kb_dir}")
        return documents

    for md_file in sorted(md_files):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            print(f"[SKIP] {md_file.name} is empty")
            continue
        documents.append({
            "source": md_file.name,
            "content": content
        })
        print(f"[LOAD] {md_file.name} — {len(content):,} chars")

    return documents


def split_into_sections(content: str) -> list[str]:
    """
    Split content on section boundaries (## or --- separators)
    to avoid mid-rule chunking. Returns a list of section strings.
    """
    # Split on level-2 headings or horizontal rules, keeping the delimiter
    section_pattern = re.compile(r'(?=^## )', re.MULTILINE)
    sections = section_pattern.split(content)

    # Also handle --- separators within each section
    refined = []
    for section in sections:
        if "---" in section:
            subsections = re.split(r'\n---+\n', section)
            refined.extend(subsections)
        else:
            refined.append(section)

    return [s.strip() for s in refined if s.strip()]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Chunk a piece of text into overlapping windows.
    Prefers splitting at paragraph or sentence boundaries.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            # Last chunk — take everything remaining
            chunks.append(text[start:].strip())
            break

        # Try to find a good split point: double newline (paragraph), then single newline, then period
        for delimiter in ["\n\n", "\n", ". "]:
            split_pos = text.rfind(delimiter, start + chunk_size // 2, end)
            if split_pos != -1:
                end = split_pos + len(delimiter)
                break

        chunk = text[start:end].strip()
        if len(chunk) >= MIN_CHUNK_SIZE:
            chunks.append(chunk)

        # Move forward with overlap
        start = end - overlap
        if start <= 0:
            start = end  # Safety: prevent infinite loop

    return chunks


def process_documents(documents: list[dict]) -> tuple[list[str], list[dict], list[str]]:
    """
    Process all documents into chunks with metadata.
    Returns (texts, metadatas, ids).
    """
    all_texts = []
    all_metadatas = []
    all_ids = []

    for doc in documents:
        source = doc["source"]
        content = doc["content"]

        # First split into logical sections to avoid splitting mid-rule
        sections = split_into_sections(content)

        for section_idx, section in enumerate(sections):
            # Then chunk each section if it's too long
            chunks = chunk_text(section)

            for chunk_idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                # Generate a deterministic ID based on content hash
                content_hash = hashlib.md5(chunk.encode()).hexdigest()[:12]
                chunk_id = f"{source}_{section_idx}_{chunk_idx}_{content_hash}"

                # Extract section title for metadata
                title_match = re.match(r'^#+\s+(.+)', chunk)
                section_title = title_match.group(1) if title_match else "General"

                all_texts.append(chunk)
                all_metadatas.append({
                    "source": source,
                    "section": section_title,
                    "section_index": section_idx,
                    "chunk_index": chunk_idx,
                    "char_count": len(chunk)
                })
                all_ids.append(chunk_id)

    return all_texts, all_metadatas, all_ids


def build_vectorstore(texts: list[str], metadatas: list[dict], ids: list[str]) -> None:
    """
    Embed texts and upsert into ChromaDB.
    Uses SentenceTransformer for local embedding generation.
    """
    import chromadb
    from chromadb.utils import embedding_functions

    print(f"\n[EMBED] Loading embedding model: {EMBEDDING_MODEL}")
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    # Create vectorstore directory
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[DB] Connecting to ChromaDB at: {VECTORSTORE_DIR}")
    client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))

    # Delete existing collection to rebuild fresh
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"[DB] Deleted existing collection '{COLLECTION_NAME}' for fresh rebuild")
    except Exception:
        pass  # Collection doesn't exist yet

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=sentence_transformer_ef,
        metadata={"hnsw:space": "cosine"}
    )

    # Batch upsert (ChromaDB handles batching internally)
    print(f"[UPSERT] Inserting {len(texts)} chunks into '{COLLECTION_NAME}'...")
    BATCH_SIZE = 50
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_meta = metadatas[i:i + BATCH_SIZE]
        batch_ids = ids[i:i + BATCH_SIZE]
        collection.upsert(
            documents=batch_texts,
            metadatas=batch_meta,
            ids=batch_ids
        )
        print(f"  Batch {i // BATCH_SIZE + 1}: {len(batch_texts)} chunks inserted")

    print(f"\n[DONE] Knowledge base built successfully!")
    print(f"  Total chunks: {collection.count()}")
    print(f"  Vectorstore location: {VECTORSTORE_DIR}")


def main():
    print("=" * 60)
    print("  AlgoShieldAI — Knowledge Base Builder")
    print("=" * 60)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check knowledge base directory
    if not KNOWLEDGE_BASE_DIR.exists():
        print(f"[ERROR] Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        sys.exit(1)

    # Load documents
    print(f"\n[STEP 1] Loading markdown files from: {KNOWLEDGE_BASE_DIR}")
    documents = load_markdown_files(KNOWLEDGE_BASE_DIR)

    if not documents:
        print("[ERROR] No documents loaded. Aborting.")
        sys.exit(1)

    print(f"\n  Loaded {len(documents)} document(s)")

    # Process into chunks
    print(f"\n[STEP 2] Chunking documents (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    texts, metadatas, ids = process_documents(documents)
    print(f"  Generated {len(texts)} chunks total")

    # Build vectorstore
    print(f"\n[STEP 3] Building ChromaDB vectorstore...")
    build_vectorstore(texts, metadatas, ids)


if __name__ == "__main__":
    main()
