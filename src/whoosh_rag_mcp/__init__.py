"""
Whoosh RAG MCP

A package providing documentation search capabilities using Whoosh full-text search
and MCP (Model Context Protocol) server integration.
"""

from whoosh_rag_mcp.doc_retriever import (
    build_index,
    search,
    update_index,
    DOCS_ROOT,
    INDEX_DIR
)

__version__ = "0.1.0"

__all__ = [
    "build_index",
    "search",
    "update_index",
    "DOCS_ROOT",
    "INDEX_DIR"
]
