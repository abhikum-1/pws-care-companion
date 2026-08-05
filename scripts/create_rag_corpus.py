# Copyright 2026 Google LLC
# Create Vertex AI RAG Engine Corpus in Serverless Mode for PWS Medical Guidelines

import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-04-d2bb10d8ba5b"
LOCATION = "us-central1"  # Serverless RAG Engine is us-central1
GCS_PATH = "gs://pws-care-companion-media-04d2/"

PARSING_PROMPT = (
    "Extract all clinical recommendations, medical alerts, growth hormone guidance, "
    "nutritional phases, GI algorithms, anesthesia precautions, and caregiver tips "
    "related to Prader-Willi Syndrome (PWS) from this document. Omit headers, footers, "
    "and page numbers. Output clean, factual, self-contained prose."
)


def create_and_populate_corpus():
    """Configures serverless mode, creates a RAG corpus, and imports uploaded PWS PDF guidelines."""
    print(f"Initializing Vertex AI RAG Engine in project: {PROJECT_ID}, location: {LOCATION}...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # 1. Configure serverless mode
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    try:
        rag.update_rag_engine_config(
            rag_engine_config=rag.RagEngineConfig(
                name=cfg,
                rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
            )
        )
        print("✓ RAG engine configured to Serverless mode.")
    except Exception as e:
        print(f"Note on RAG Engine config update: {e}")

    # 2. Create the RAG corpus
    print("Creating RAG corpus 'pws-care-guidelines-corpus'...")
    corpus = rag.create_corpus(
        display_name="pws-care-guidelines-corpus",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    corpus_name = corpus.name
    print(f"🎉 Created RAG Corpus Name: {corpus_name}")

    # 3. Import uploaded PDF documents from GCS
    print(f"Importing and indexing PWS care PDFs from {GCS_PATH}...")
    resp = rag.import_files(
        corpus_name=corpus_name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-2.5-flash",
            custom_parsing_prompt=PARSING_PROMPT,
        ),
    )
    print(f"✓ Successfully imported {getattr(resp, 'imported_rag_files_count', 'all')} PWS medical/care documents into corpus!")
    return corpus_name


if __name__ == "__main__":
    create_and_populate_corpus()
