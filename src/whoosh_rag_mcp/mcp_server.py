#!/usr/bin/env python3
"""
Whoosh RAG Documentation Search MCP Server

This MCP server exposes documentation search functionality using Whoosh full-text search.
It provides tools for searching indexed documentation and managing the search index.
"""

import asyncio
import json
import os
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import the existing documentation retrieval functions
from whoosh_rag_mcp.doc_retriever import (
    build_index as _build_index,
    search as _search,
    update_index as _update_index,
    INDEX_DIR,
    DOCS_ROOT
)

# Create MCP server instance
app = Server("whoosh-rag-docs")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for documentation search."""
    return [
        Tool(
            name="search_documentation",
            description=(
                "Search through indexed documentation using full-text search, you should try also query with synonyms."
                "Returns relevant documentation snippets or full sections matching the query. "
                "Use this when you need to find information in the documentation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string (e.g., 'flow decorator', 'task retries', 'deployment configuration')"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "section_mode": {
                        "type": "boolean",
                        "description": "If true, search and return results by section (based on ## headings). If false, return document snippets.",
                        "default": False
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="build_documentation_index",
            description=(
                "Build or rebuild the Whoosh search index from documentation files. "
                "This indexes all markdown (.md, .mdx) and reStructuredText (.rst) files "
                "in the documentation root directory. Run this when setting up for the first time "
                "or when you want to completely rebuild the index. "
                "If an index already exists, you must set 'force' to true to overwrite it."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "Set to true to overwrite existing index without confirmation. Required if index already exists.",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="update_documentation_index",
            description=(
                "Update the existing documentation index. Currently performs a full rebuild. "
                "Use this after documentation files have been added, modified, or removed."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_index_info",
            description=(
                "Get information about the current documentation index, including "
                "the documentation root path, index directory path, and whether the index exists."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for documentation search operations."""
    
    try:
        if name == "search_documentation":
            query = arguments.get("query")
            if not query:
                return [TextContent(
                    type="text",
                    text="Error: 'query' parameter is required"
                )]
            
            limit = arguments.get("limit", 5)
            section_mode = arguments.get("section_mode", False)
            
            # Check if index exists
            from whoosh import index
            if not index.exists_in(INDEX_DIR):
                return [TextContent(
                    type="text",
                    text=(
                        "Error: Documentation index not found. "
                        "Please run 'build_documentation_index' tool first to create the index."
                    )
                )]
            
            # Perform search
            results = _search(query, topk=limit, section=section_mode)
            
            if not results:
                return [TextContent(
                    type="text",
                    text=f"No results found for query: '{query}'"
                )]
            
            # Format results
            output_lines = [f"Search Results for: '{query}'", "=" * 60, ""]
            
            for idx, result in enumerate(results, 1):
                if section_mode:
                    path, section_idx, section_title, content = result
                    output_lines.extend([
                        f"Result {idx}:",
                        f"File: {path}",
                        f"Section: {section_title}" if section_title else f"Section Index: {section_idx}",
                        "",
                        content,
                        "",
                        "-" * 60,
                        ""
                    ])
                else:
                    path, section_idx, snippet = result
                    output_lines.extend([
                        f"Result {idx}:",
                        f"File: {path}",
                        f"Section Index: {section_idx}",
                        "",
                        f"Snippet: {snippet}",
                        "",
                        "-" * 60,
                        ""
                    ])
            
            return [TextContent(
                type="text",
                text="\n".join(output_lines)
            )]
        
        elif name == "build_documentation_index":
            # Check if index exists and force flag
            from whoosh import index
            index_exists = index.exists_in(INDEX_DIR)
            force = arguments.get("force", False)
            
            if index_exists and not force:
                return [TextContent(
                    type="text",
                    text=(
                        f"Warning: An index already exists at: {INDEX_DIR}\n\n"
                        "To overwrite the existing index, please call this tool again with "
                        "'force' parameter set to true:\n"
                        '{"force": true}\n\n'
                        "This safety check prevents accidental loss of your existing index."
                    )
                )]
            
            old_stdout = sys.stdout
            try:
                # Redirect stdout to capture build output
                from io import StringIO
                sys.stdout = captured_output = StringIO()
                
                _build_index(force=True)  # Pass force=True since we've already checked
                
                sys.stdout = old_stdout
                output = captured_output.getvalue()
                
                return [TextContent(
                    type="text",
                    text=f"Successfully built documentation index.\n\n{output}"
                )]
            except Exception as e:
                sys.stdout = old_stdout
                return [TextContent(
                    type="text",
                    text=f"Error building index: {str(e)}"
                )]
        
        elif name == "update_documentation_index":
            old_stdout = sys.stdout
            try:
                # Redirect stdout to capture update output
                from io import StringIO
                sys.stdout = captured_output = StringIO()
                
                _update_index()
                
                sys.stdout = old_stdout
                output = captured_output.getvalue()
                
                return [TextContent(
                    type="text",
                    text=f"Successfully updated documentation index.\n\n{output}"
                )]
            except Exception as e:
                sys.stdout = old_stdout
                return [TextContent(
                    type="text",
                    text=f"Error updating index: {str(e)}"
                )]
        
        elif name == "get_index_info":
            from whoosh import index
            index_exists = index.exists_in(INDEX_DIR)
            
            info_lines = [
                "Documentation Index Information:",
                "=" * 60,
                f"Documentation Root: {DOCS_ROOT}",
                f"Index Directory: {INDEX_DIR}",
                f"Index Exists: {'Yes' if index_exists else 'No'}",
                ""
            ]
            
            if not os.path.exists(DOCS_ROOT):
                info_lines.append(f"⚠️  Warning: Documentation root directory does not exist: {DOCS_ROOT}")
            else:
                # Count documentation files
                doc_count = 0
                for root, _, files in os.walk(DOCS_ROOT):
                    doc_count += sum(1 for f in files if f.endswith((".md", ".mdx", ".rst")))
                info_lines.append(f"Documentation Files Found: {doc_count}")
            
            if not index_exists:
                info_lines.append("\n⚠️  Index not built yet. Run 'build_documentation_index' to create it.")
            
            return [TextContent(
                type="text",
                text="\n".join(info_lines)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing tool '{name}': {str(e)}"
        )]

def main():
    """Run the MCP server using stdio transport."""
    asyncio.run(async_main())

async def async_main():
    """Async entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    main()
