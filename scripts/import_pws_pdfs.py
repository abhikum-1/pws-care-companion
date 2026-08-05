# Copyright 2026 Google LLC
# Import PWS PDF Medical Guidelines into RAG Corpus and test retrieval

import vertexai
from vertexai import rag

PROJECT_ID = "qwiklabs-gcp-04-d2bb10d8ba5b"
LOCATION = "us-central1"
CORPUS_NAME = "projects/872367567135/locations/us-central1/ragCorpora/162349488910893056"
GCS_PATH = "gs://pws-care-companion-media-04d2/"

vertexai.init(project=PROJECT_ID, location=LOCATION)


def import_pdfs():
    """Imports PDF documents from GCS bucket into the RAG corpus."""
    print(f"Importing PDF care guidelines from {GCS_PATH} into corpus {CORPUS_NAME}...")
    resp = rag.import_files(
        corpus_name=CORPUS_NAME,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
    )
    print("✓ Import completed successfully!")
    return resp


if __name__ == "__main__":
    import_pdfs()
