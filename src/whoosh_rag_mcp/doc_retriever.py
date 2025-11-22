import os
import re
import sys
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, NUMERIC
from whoosh.qparser import MultifieldParser
from whoosh.analysis import StemmingAnalyzer
from whoosh import writing

# Get configuration from environment variables
DOCS_ROOT = os.environ.get('DOCS_ROOT', os.path.join(os.path.dirname(__file__), "../../references"))
INDEX_DIR = os.environ.get('INDEX_DIR', os.path.join(os.path.dirname(__file__), "../../whoosh_index"))

def iter_doc_files():
    """Iterate through all markdown documentation files."""
    if not os.path.exists(DOCS_ROOT):
        print(f"Warning: Documentation root not found: {DOCS_ROOT}", file=sys.stderr)
        return
    
    for root, _, files in os.walk(DOCS_ROOT):
        for f in files:
            if f.endswith((".md", ".mdx", ".rst")):
                yield os.path.join(root, f)

def extract_title_and_sections(text: str):
    """Extract title and sections from markdown text."""
    lines = text.splitlines()
    title = ""
    sections = []
    buf = []
    sec_title = ""
    
    for line in lines:
        if line.startswith("# "):
            if not title:
                title = line.lstrip("#").strip()
            buf.append(line)
            continue
        if line.startswith("##"):
            if buf:
                sections.append((sec_title, "\n".join(buf).strip()))
                buf = []
            sec_title = line.lstrip("#").strip()
        buf.append(line)
    
    if buf:
        sections.append((sec_title, "\n".join(buf).strip()))
    
    return title, sections

def build_index(force=False):
    """Build the Whoosh search index.
    
    Args:
        force: If True, skip confirmation prompt when overwriting existing index.
    """
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR)
    
    schema = Schema(
        path=ID(stored=True),
        title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        section_title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        section_idx=NUMERIC(stored=True)
    )
    
    if index.exists_in(INDEX_DIR):
        if not force:
            # Prompt user for confirmation
            print(f"Warning: An index already exists at: {INDEX_DIR}")
            response = input("Do you want to overwrite the existing index? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Index rebuild cancelled.")
                return
        
        print("Clearing existing index...")
        ix = index.open_dir(INDEX_DIR)
        writer = ix.writer()
        writer.commit(mergetype=writing.CLEAR)
        writer = ix.writer()
    else:
        ix = index.create_in(INDEX_DIR, schema)
        writer = ix.writer()
    
    file_count = 0
    section_count = 0
    
    for path in iter_doc_files():
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Failed to read {path}: {e}", file=sys.stderr)
            continue
        
        title, sections = extract_title_and_sections(content)
        
        for i, (sec_title, sec_content) in enumerate(sections):
            writer.add_document(
                path=path,
                title=title,
                section_title=sec_title,
                content=sec_content,
                section_idx=i
            )
            section_count += 1
        
        file_count += 1
    
    writer.commit()
    print(f"Whoosh index build complete. Indexed {file_count} files with {section_count} sections.")

def search(query: str, topk=5, section=False):
    """Search the documentation index."""
    if not index.exists_in(INDEX_DIR):
        print("Index not found, please build it first.", file=sys.stderr)
        return []
    
    ix = index.open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        if section:
            parser = MultifieldParser(["section_title", "content"], schema=ix.schema)
        else:
            parser = MultifieldParser(["title", "content"], schema=ix.schema)
        
        q = parser.parse(query)
        results = searcher.search(q, limit=topk)
        hits = []
        
        for hit in results:
            if section:
                hits.append((hit["path"], hit["section_idx"], hit["section_title"], hit["content"]))
            else:
                hits.append((hit["path"], hit["section_idx"], hit["content"][:200]))
        
        return hits

def update_index():
    """Update the index (currently rebuilds it)."""
    build_index()

import json

def print_results(results, full=False, section=False, as_json=False):
    """Print search results in various formats."""
    if as_json:
        out = []
        if section:
            for path, i, sec_title, sec_content in results:
                out.append({
                    "path": path,
                    "section_idx": i,
                    "section_title": sec_title,
                    "content": sec_content
                })
        else:
            for path, i, snippet in results:
                if full:
                    try:
                        with open(path, encoding="utf-8") as f:
                            doc_txt = f.read()
                    except Exception:
                        doc_txt = "[Failed to read full content]"
                    out.append({
                        "path": path,
                        "content": doc_txt
                    })
                else:
                    out.append({
                        "path": path,
                        "section_idx": i,
                        "snippet": snippet
                    })
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if section:
            for path, i, sec_title, sec_content in results:
                print(f"File: {path}, Section: {sec_title}\nContent:\n{sec_content}\n{'-'*40}")
        else:
            for path, i, snippet in results:
                if full:
                    try:
                        with open(path, encoding="utf-8") as f:
                            doc_txt = f.read()
                    except Exception:
                        doc_txt = "[Failed to read full content]"
                    print(f"File: {path}\nFull content:\n{doc_txt}\n{'-'*40}")
                else:
                    print(f"File: {path}, Section: {i}\nSnippet: {snippet}\n{'-'*40}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Documentation retrieval tool (Whoosh version)")
    parser.add_argument("--build", action="store_true", help="Build Whoosh index (will prompt if index exists)")
    parser.add_argument("--build-force", action="store_true", help="Force rebuild Whoosh index without confirmation")
    parser.add_argument("--update", action="store_true", help="Incrementally update index (currently same as rebuild)")
    parser.add_argument("--query", type=str, help="Search keyword")
    parser.add_argument("--full", action="store_true", help="Output full content when searching")
    parser.add_argument("--section", action="store_true", help="Output by section (based on ## and above headings)")
    parser.add_argument("--json", action="store_true", help="Output search results in JSON format")
    args = parser.parse_args()

    if args.build or args.build_force:
        build_index(force=args.build_force)
    elif args.update:
        update_index()
    elif args.query:
        results = search(args.query, section=args.section)
        print_results(results, full=args.full, section=args.section, as_json=args.json)
    else:
        parser.print_help()
