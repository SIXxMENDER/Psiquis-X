# config/settings.py
"""Configuration module for the Psiquis-X project.

Defines paths and constants used by the Cortex router and benchmark scripts.
All values can be overridden by environment variables.
"""
import os

# Base directory of the project (directory containing this file's parent)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Path to the Chroma vector store database
DB_PATH = os.getenv(
    "DB_PATH",
    os.path.join(BASE_DIR, "data", "chroma_db")
)

# Name of the collection inside the Chroma DB
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "psiquis_core")

# Google Cloud project identifier (used by Vertex AI)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project")

# Region for Vertex AI – the user explicitly wants the global endpoint
GCP_REGION = os.getenv("GCP_REGION", "global")
