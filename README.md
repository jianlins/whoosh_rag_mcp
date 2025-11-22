# Whoosh RAG MCP - Documentation Search Server

A Model Context Protocol (MCP) server that provides full-text search capabilities for documentation using Whoosh. This allows AI assistants like Cline and GitHub Copilot to search and retrieve relevant documentation.

## Rationale

Large language models (LLMs) are often trained on outdated code and documentation, which can lead to suggestions that use deprecated functions or patterns. This MCP server uses Whoosh for fast, precise, and explainable full-text search over your latest documentation, helping AI assistants and users find up-to-date, authoritative answers. This improves coding correctness and reliability, especially in technical environments. Whoosh is lightweight, CPU-friendly, and requires no embeddings or GPUs. For best results, include synonyms in your queries to broaden coverage.

## Features

- **Full-text search** through markdown (.md, .mdx) and reStructuredText (.rst) documentation
- **Section-based indexing** for granular search results
- **Stemming analyzer** for better search matches
- **Multiple search modes**: snippets, full content, or by section

## Tools Provided

The MCP server exposes the following tools to AI assistants:

1. **`search_documentation`** - Search indexed documentation with full-text search
2. **`build_documentation_index`** - Build/rebuild the search index from documentation files
3. **`update_documentation_index`** - Update the existing index (currently performs full rebuild)
4. **`get_index_info`** - Get information about the current index status

## Installation

### 1. Install from PyPI

The easiest way to install the package is from PyPI:

```bash
pip install whoosh-rag-mcp
```

Alternatively, you can install directly from GitHub:

```bash
pip install git+https://github.com/jianlins/whoosh_rag_mcp.git
```

Or for development (editable install):

```bash
git clone https://github.com/jianlins/whoosh_rag_mcp.git
cd whoosh_rag_mcp
pip install -e .
```

### 2. Configure Environment Variables

The server uses environment variables to locate documentation:

- `DOCS_ROOT` - Path to your documentation directory (default: `./references`)
- `INDEX_DIR` - Path to store the Whoosh index (default: `./whoosh_index`)

### 3. Configure MCP Server

Choose the appropriate configuration method based on your AI assistant:

#### Option A: For Cline (VS Code Extension)

Add the server configuration to your Cline MCP settings file:

**Windows**: `%APPDATA%\Code - Insiders\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

**macOS**: `~/Library/Application Support/Code - Insiders/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

**Linux**: `~/.config/Code - Insiders/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

Add this configuration to the `mcpServers` object:

```json
{
  "mcpServers": {
    "whoosh-rag-docs": {
      "command": "python",
      "args": ["-m", "whoosh_rag_mcp.mcp_server"],
      "env": {
        "DOCS_ROOT": "c:/Users/YourUsername/Projects/whoosh_rag_mcp/references",
        "INDEX_DIR": "c:/Users/YourUsername/Projects/whoosh_rag_mcp/whoosh_index"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Important**: Replace the paths with your actual project directory paths.

#### Option B: For GitHub Copilot Chat (VS Code Extension)

GitHub Copilot uses a different configuration format than Cline. You'll create an `mcp.json` file instead of editing `settings.json`.

**Method 1: Using the Command Palette (Recommended)**

1. Open the Command Palette (`Ctrl+Shift+P` on Windows/Linux or `Cmd+Shift+P` on macOS)

2. Run the command: **MCP: Add Server**

3. When prompted, select **stdio** as the server type

4. Fill in the server details:
   - **Server name**: `whoosh-rag-docs`
   - **Command**: `python` (or full path to Python if not in PATH)
   - **Args**: 
     - Click "Add argument" and enter `-m`
     - Click "Add argument" again and enter `whoosh_rag_mcp.mcp_server`

5. Add environment variables:
   - Click "Add environment variable"
   - **Name**: `DOCS_ROOT`, **Value**: `c:/Users/YourUsername/Projects/whoosh_rag_mcp/references`
   - Click "Add environment variable" again
   - **Name**: `INDEX_DIR`, **Value**: `c:/Users/YourUsername/Projects/whoosh_rag_mcp/whoosh_index`

6. Select where to save: Choose **Global** (for all workspaces) or **Workspace** (current project only)

**Method 2: Manual Configuration**

1. **Create the MCP configuration file**:
   - For **global** (all workspaces): Run **MCP: Open User Configuration** from Command Palette
   - For **workspace** (current project): Create `.vscode/mcp.json` in your project

2. **Add the server configuration**:

```json
{
  "servers": {
    "whoosh-rag-docs": {
      "command": "python",
      "args": ["-m", "whoosh_rag_mcp.mcp_server"],
      "env": {
        "DOCS_ROOT": "c:/Users/YourUsername/Projects/whoosh_rag_mcp/references",
        "INDEX_DIR": "c:/Users/YourUsername/Projects/whoosh_rag_mcp/whoosh_index"
      }
    }
  }
}
```

**Note**: Using `python -m whoosh_rag_mcp.mcp_server` is more portable than specifying the direct file path. Make sure the package is installed or your Python path includes the project directory.

3. **If Python is not in your PATH**, use the full path:
   ```json
   "command": "c:/Users/YourUsername/AppData/Local/Programs/Python/Python311/python.exe"
   ```

4. **Start the MCP server**:
   - Run **MCP: List Servers** from Command Palette
   - Select `whoosh-rag-docs` and click **Start Server**
   - Or enable auto-start: Set `chat.mcp.autostart` to `true` in VS Code settings

5. **Verify the connection**:
   - Open GitHub Copilot Chat
   - Click the **Tools** button in the chat input to see available tools
   - You should see tools from `whoosh-rag-docs` listed

### 4. Build the Index

Before searching, you need to build the index. You can either:

**Option A**: Use Cline to build the index:
- Ask Cline: "Use the build_documentation_index tool to index my documentation"

**Option B**: Build manually from command line:
```bash
python -m whoosh_rag_mcp.doc_retriever --build
```

**Safety Feature**: If an index already exists, you'll be prompted to confirm before overwriting it. This prevents accidental loss of your existing index.

- **CLI Options**:
  - `--build`: Prompts for confirmation if index exists
    ```bash
    python -m whoosh_rag_mcp.doc_retriever --build
    ```
  - `--build-force`: Skips confirmation and rebuilds immediately
    ```bash
    python -m whoosh_rag_mcp.doc_retriever --build-force
    ```
  
- **MCP Tool**: When calling `build_documentation_index`, if an index exists, you must set the `force` parameter to `true`:
  ```json
  {
    "force": true
  }
  ```

## Usage

Once configured, AI assistants can use the tools automatically.

### Using with Cline

Here are some example prompts:

- "Use the search_documentation tool to find information about task retries"
- "Search the documentation for flow decorators"
- "Look up deployment configuration in the docs"
- "Get the index info to see how many documents are indexed"
- "Build the documentation index"

### Using with GitHub Copilot Chat

You can interact with the MCP server in several ways:

**Method 1: Using @participant syntax** (if supported):
```
@whoosh-rag-docs search for information about task retries
```

**Method 2: Direct tool invocation** (recommended):
```
Can you search the documentation for "flow decorators"?
```

**Method 3: Natural language requests**:
```
I need help understanding deployment configuration. Can you search the docs?
```

**Example Copilot Chat interactions**:
- "Search the indexed documentation for examples of error handling"
- "Find information about async/await patterns in the docs"
- "What does the documentation say about configuration options?"
- "Search for 'authentication' in the documentation"

## Project Structure

```
whoosh_rag_mcp/
├── src/
│   └── whoosh_rag_mcp/
│       ├── __init__.py        # Package initialization
│       ├── mcp_server.py      # MCP server implementation
│       └── doc_retriever.py   # Core search and indexing logic
├── references/                # Your documentation files go here
│   ├── dask_docs/
│   ├── prefect_docs/
│   └── setuptools_docs/
├── whoosh_index/              # Search index (auto-generated)
├── pyproject.toml             # Package configuration (setuptools)
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## How It Works

1. The MCP server runs as a subprocess and communicates via stdio
2. AI assistants discover available tools through the MCP protocol
3. When you ask to search documentation, the assistant calls the `search_documentation` tool
4. The server uses Whoosh to perform full-text search on indexed documents
5. Results are returned to the assistant, which can then use them to answer your questions

## Manual Usage (Optional)

You can also use the search functionality directly from the command line:

```bash
# Build the index (will prompt for confirmation if index exists)
python -m whoosh_rag_mcp.doc_retriever --build

# Force rebuild the index (skips confirmation prompt)
python -m whoosh_rag_mcp.doc_retriever --build-force

# Update the index (currently same as --build, will prompt if index exists)
python -m whoosh_rag_mcp.doc_retriever --update

# Search documentation
python -m whoosh_rag_mcp.doc_retriever --query "your search terms" --json

# Search by section
python -m whoosh_rag_mcp.doc_retriever --query "your search terms" --section --json

# Get full content
python -m whoosh_rag_mcp.doc_retriever --query "your search terms" --full --json
```

## Troubleshooting

### Server Not Connecting (Cline)

1. Check that Python is in your PATH
2. Verify the paths in your MCP settings are correct (use absolute paths)
3. Check that dependencies are installed: `pip install -r requirements.txt`
4. Look for error messages in Cline's MCP server logs

### GitHub Copilot Chat Issues

**MCP server not appearing or not starting:**

1. **Verify the configuration file**:
   - GitHub Copilot uses `mcp.json`, NOT `settings.json`
   - Open your MCP configuration: Run **MCP: Open User Configuration** (for global) or check `.vscode/mcp.json` (for workspace)
   - Verify the file exists and contains valid JSON

2. **Check the configuration format**:
   - Must use the `"servers"` key (not `"mcpServers"` like Cline)
   - Configuration must be valid JSON (no trailing commas, proper escaping)
   - Example valid configuration:
     ```json
     {
       "servers": {
         "whoosh-rag-docs": {
           "command": "python",
           "args": ["-m", "whoosh_rag_mcp.mcp_server"],
           "env": {
             "DOCS_ROOT": "c:/path/to/references",
             "INDEX_DIR": "c:/path/to/whoosh_index"
           }
         }
       }
     }
     ```

3. **Start the MCP server**:
   - Run **MCP: List Servers** from Command Palette
   - Find `whoosh-rag-docs` and select **Start Server**
   - Check for any error messages in the output

3. **Verify Python path**:
   - Open terminal: `python --version`
   - If command not found, use full Python path in the `"command"` field
   - Windows: `"c:/Users/YourUsername/AppData/Local/Programs/Python/Python311/python.exe"`
   - macOS/Linux: `"/usr/local/bin/python3"` or `"/usr/bin/python3"`

4. **Check VS Code Output panel**:
   - Open Output panel: `View > Output`
   - Select "GitHub Copilot Chat" from the dropdown
   - Look for MCP-related error messages

5. **Restart VS Code completely**:
   - Close all VS Code windows
   - Reopen VS Code
   - Wait a few seconds for extensions to initialize

6. **Test the MCP server manually**:
   ```bash
   python -m whoosh_rag_mcp.mcp_server
   ```
   - The server should start without errors
   - Press `Ctrl+C` to stop

**Copilot not using the MCP tools:**

1. **Build the index first** (required before searches work):
   ```bash
   python -m whoosh_rag_mcp.doc_retriever --build
   ```

2. **Be explicit in your requests**:
   - Instead of: "Tell me about task retries"
   - Try: "Search the documentation for task retries"
   - Or: "Use the search_documentation tool to find information about task retries"

3. **Check if GitHub Copilot Chat supports MCP**:
   - MCP support in GitHub Copilot Chat is a newer feature
   - Ensure you have the latest version of the GitHub Copilot extension
   - Check extension updates: `Extensions > Search for "GitHub Copilot" > Update if available`

### No Search Results

1. Make sure the index is built: ask Cline to run `get_index_info`
2. If index doesn't exist, build it with `build_documentation_index`
3. Check that `DOCS_ROOT` points to a directory containing .md, .mdx, or .rst files

### Index Build Fails

1. Verify `DOCS_ROOT` directory exists and contains documentation files
2. Check file permissions - ensure the server can read the documentation files
3. Ensure write permissions for `INDEX_DIR`

## License

MIT License - see LICENSE file for details
