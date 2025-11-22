const vscode = require('vscode');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const util = require('util');
const execPromise = util.promisify(exec);

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('Whoosh RAG MCP extension is now active!');

    // Register commands
    let buildIndexCmd = vscode.commands.registerCommand('whoosh-rag.buildIndex', buildIndex);
    let searchDocsCmd = vscode.commands.registerCommand('whoosh-rag.searchDocs', searchDocs);
    let updateIndexCmd = vscode.commands.registerCommand('whoosh-rag.updateIndex', updateIndex);
    let configureCmd = vscode.commands.registerCommand('whoosh-rag.configureSettings', configureSettings);

    context.subscriptions.push(buildIndexCmd, searchDocsCmd, updateIndexCmd, configureCmd);
}

/**
 * Get the Python command from configuration
 */
function getPythonCommand() {
    const config = vscode.workspace.getConfiguration('whooshRag');
    const pythonPath = config.get('pythonPath', 'python').trim();
    return pythonPath;
}

/**
 * Get the references path from configuration or use default
 */
function getReferencesPath() {
    const config = vscode.workspace.getConfiguration('whooshRag');
    const configuredPath = config.get('referencesPath', '').trim();
    
    if (configuredPath) {
        // Use configured path (can be absolute or relative)
        if (path.isAbsolute(configuredPath)) {
            return configuredPath;
        } else {
            // Relative to workspace
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (workspaceFolder) {
                return path.join(workspaceFolder.uri.fsPath, configuredPath);
            }
        }
    }
    
    // Default to references folder in workspace root
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (workspaceFolder) {
        return path.join(workspaceFolder.uri.fsPath, 'references');
    }
    
    return null;
}

/**
 * Get the index path from configuration or use default
 */
function getIndexPath() {
    const config = vscode.workspace.getConfiguration('whooshRag');
    const configuredPath = config.get('indexPath', '').trim();
    
    if (configuredPath) {
        // Use configured path (can be absolute or relative)
        if (path.isAbsolute(configuredPath)) {
            return configuredPath;
        } else {
            // Relative to workspace
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (workspaceFolder) {
                return path.join(workspaceFolder.uri.fsPath, configuredPath);
            }
        }
    }
    
    // Default to whoosh_index folder in workspace root
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (workspaceFolder) {
        return path.join(workspaceFolder.uri.fsPath, 'whoosh_index');
    }
    
    return null;
}

/**
 * Get the path to the Python script
 */
function getScriptPath() {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (workspaceFolder) {
        return path.join(workspaceFolder.uri.fsPath, 'src', 'whoosh_rag_mcp', 'doc_retriever.py');
    }
    return null;
}

/**
 * Execute Python script with given arguments
 */
async function executePythonScript(args, outputChannel) {
    const pythonCmd = getPythonCommand();
    const scriptPath = getScriptPath();
    const referencesPath = getReferencesPath();
    const indexPath = getIndexPath();

    if (!scriptPath) {
        throw new Error('Could not determine script path. Make sure you have a workspace folder open.');
    }

    if (!referencesPath) {
        throw new Error('Could not determine references path. Please configure it in settings.');
    }

    // Set environment variables for the script
    const env = { ...process.env };
    env.DOCS_ROOT = referencesPath;
    if (indexPath) {
        env.INDEX_DIR = indexPath;
    }

    const command = `${pythonCmd} "${scriptPath}" ${args}`;
    
    outputChannel.appendLine(`Executing: ${command}`);
    outputChannel.appendLine(`References Path: ${referencesPath}`);
    outputChannel.appendLine(`Index Path: ${indexPath || '(default)'}`);
    outputChannel.appendLine('---');

    try {
        const { stdout, stderr } = await execPromise(command, { 
            env,
            cwd: path.dirname(scriptPath),
            maxBuffer: 10 * 1024 * 1024 // 10MB buffer for large outputs
        });
        
        if (stdout) {
            outputChannel.appendLine(stdout);
        }
        if (stderr) {
            outputChannel.appendLine('STDERR:');
            outputChannel.appendLine(stderr);
        }
        
        return { stdout, stderr };
    } catch (error) {
        outputChannel.appendLine(`Error: ${error.message}`);
        if (error.stdout) outputChannel.appendLine(error.stdout);
        if (error.stderr) outputChannel.appendLine(error.stderr);
        throw error;
    }
}

/**
 * Build the documentation index
 */
async function buildIndex() {
    const outputChannel = vscode.window.createOutputChannel('Whoosh RAG MCP - Build Index');
    outputChannel.show();

    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Building documentation index...",
            cancellable: false
        }, async (progress) => {
            await executePythonScript('--build', outputChannel);
        });

        vscode.window.showInformationMessage('Documentation index built successfully!');
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to build index: ${error.message}`);
    }
}

/**
 * Update the documentation index
 */
async function updateIndex() {
    const outputChannel = vscode.window.createOutputChannel('Whoosh RAG MCP - Update Index');
    outputChannel.show();

    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Updating documentation index...",
            cancellable: false
        }, async (progress) => {
            await executePythonScript('--update', outputChannel);
        });

        vscode.window.showInformationMessage('Documentation index updated successfully!');
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to update index: ${error.message}`);
    }
}

/**
 * Search the documentation
 */
async function searchDocs() {
    const query = await vscode.window.showInputBox({
        prompt: 'Enter search query',
        placeHolder: 'e.g., flow decorator, task retries, deployment'
    });

    if (!query) {
        return;
    }

    const options = await vscode.window.showQuickPick([
        { label: 'Snippet', description: 'Show snippets only', value: 'snippet' },
        { label: 'Full Content', description: 'Show full document content', value: 'full' },
        { label: 'By Section', description: 'Show results by section', value: 'section' }
    ], {
        placeHolder: 'Select output format'
    });

    if (!options) {
        return;
    }

    const outputChannel = vscode.window.createOutputChannel('Whoosh RAG MCP - Search Results');
    outputChannel.clear();
    outputChannel.show();

    try {
        let args = `--query "${query}" --json`;
        
        if (options.value === 'full') {
            args += ' --full';
        } else if (options.value === 'section') {
            args += ' --section';
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Searching documentation...",
            cancellable: false
        }, async (progress) => {
            const { stdout } = await executePythonScript(args, outputChannel);
            
            try {
                const results = JSON.parse(stdout);
                outputChannel.clear();
                outputChannel.appendLine(`Search Results for: "${query}"`);
                outputChannel.appendLine('='.repeat(60));
                outputChannel.appendLine('');
                
                if (results.length === 0) {
                    outputChannel.appendLine('No results found.');
                } else {
                    results.forEach((result, index) => {
                        outputChannel.appendLine(`Result ${index + 1}:`);
                        outputChannel.appendLine(`File: ${result.path}`);
                        
                        if (result.section_title) {
                            outputChannel.appendLine(`Section: ${result.section_title}`);
                        }
                        if (result.section_idx !== undefined) {
                            outputChannel.appendLine(`Section Index: ${result.section_idx}`);
                        }
                        
                        outputChannel.appendLine('');
                        
                        if (result.content) {
                            outputChannel.appendLine(result.content);
                        } else if (result.snippet) {
                            outputChannel.appendLine(result.snippet);
                        }
                        
                        outputChannel.appendLine('');
                        outputChannel.appendLine('-'.repeat(60));
                        outputChannel.appendLine('');
                    });
                }
            } catch (parseError) {
                outputChannel.appendLine('Raw output:');
                outputChannel.appendLine(stdout);
            }
        });

    } catch (error) {
        vscode.window.showErrorMessage(`Search failed: ${error.message}`);
    }
}

/**
 * Open settings to configure the extension
 */
async function configureSettings() {
    await vscode.commands.executeCommand('workbench.action.openSettings', 'whooshRag');
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
