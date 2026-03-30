'use client';

import CodeEditor from '@/components/CodeEditor';
import { MarketplaceLayout } from '@/components/layouts/MarketplaceLayout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { API_BASE_URL } from '@/lib/config';
import { logger } from '@/lib/logger';
import {
  ChevronDown,
  ChevronRight,
  Code2,
  File,
  FilePlus,
  Folder,
  FolderOpen,
  FolderPlus,
  GitBranch,
  MessageSquare,
  Search,
  Sparkles,
  Terminal,
  Trash2,
  X,
} from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

type FileNode = {
  id: string;
  name: string;
  type: 'file' | 'folder';
  language?: string;
  content?: string;
  children?: FileNode[];
  expanded?: boolean;
};

type OpenTab = {
  id: string;
  name: string;
  language: string;
  content: string;
  modified: boolean;
};

const DEFAULT_FILES: FileNode[] = [
  {
    id: 'src',
    name: 'src',
    type: 'folder',
    expanded: true,
    children: [
      {
        id: 'src/main.ts',
        name: 'main.ts',
        type: 'file',
        language: 'typescript',
        content: `import { HelixCollective } from '@helix/agents';
import { UCFMetrics } from '@helix/coordination';

// Initialize Helix
const collective = new HelixCollective({
  agents: ['kael', 'lumina', 'vega', 'kavach'],
  coordination_threshold: 5.0,
});

async function main() {
  // Get current UCF metrics
  const metrics = await UCFMetrics.getCurrent();
  logger.info('Coordination Level:', metrics.level);

  // Run multi-agent analysis
  const result = await collective.analyze({
    task: 'Evaluate system harmony',
    data: metrics,
  });

  logger.info('Analysis:', result.summary);
  logger.info('Agents involved:', result.agents.map(a => a.name));
}

main().catch(console.error);
`,
      },
      {
        id: 'src/agents.py',
        name: 'agents.py',
        type: 'file',
        language: 'python',
        content: `"""Helix Agent Configuration"""
from helix_flow.agents import AgentConfig, create_agent

# Configure Kael - The Analytical Mind
kael = create_agent(
    name="Kael",
    role="analyst",
    personality={
        "analytical": 0.95,
        "creative": 0.60,
        "empathetic": 0.70,
    },
    capabilities=["data_analysis", "pattern_recognition", "forecasting"],
)

# Configure Lumina - The Creative Force
lumina = create_agent(
    name="Lumina",
    role="creative",
    personality={
        "analytical": 0.65,
        "creative": 0.98,
        "empathetic": 0.85,
    },
    capabilities=["content_generation", "design", "storytelling"],
)

def run_analysis(data: dict) -> dict:
    """Run collaborative analysis between agents."""
    kael_result = kael.analyze(data)
    lumina_result = lumina.enhance(kael_result)
    return {
        "analysis": kael_result,
        "enhanced": lumina_result,
        "consensus": kael.consensus(lumina_result),
    }
`,
      },
      {
        id: 'src/spiral.json',
        name: 'spiral.json',
        type: 'file',
        language: 'json',
        content: `{
  "name": "Lead Nurture Automation",
  "version": "1.0.0",
  "trigger": {
    "type": "webhook",
    "path": "/api/leads/new"
  },
  "nodes": [
    { "id": "enrich", "type": "data_enrichment", "config": {} },
    { "id": "score", "type": "ai_agent", "agent": "kael", "task": "score_lead" },
    { "id": "route", "type": "condition", "field": "score", "operator": ">=", "value": 80 },
    { "id": "notify_sales", "type": "slack", "channel": "#hot-leads" },
    { "id": "add_sequence", "type": "email_sequence", "template": "nurture_v2" }
  ],
  "connections": [
    { "source": "trigger", "target": "enrich" },
    { "source": "enrich", "target": "score" },
    { "source": "score", "target": "route" },
    { "source": "route", "target": "notify_sales", "condition": "true" },
    { "source": "route", "target": "add_sequence", "condition": "false" }
  ]
}
`,
      },
    ],
  },
  {
    id: 'tests',
    name: 'tests',
    type: 'folder',
    expanded: false,
    children: [
      {
        id: 'tests/test_agents.py',
        name: 'test_agents.py',
        type: 'file',
        language: 'python',
        content: `"""Tests for Helix agents."""
import pytest
from src.agents import kael, lumina, run_analysis
import { logger } from '@/lib/logger';

def test_kael_analysis():
    data = {"metrics": [1, 2, 3, 4, 5]}
    result = kael.analyze(data)
    assert result is not None
    assert "patterns" in result

def test_lumina_enhancement():
    base = {"text": "Hello world"}
    result = lumina.enhance(base)
    assert len(result["text"]) > len(base["text"])

def test_collaborative_analysis():
    data = {"input": "test data"}
    result = run_analysis(data)
    assert "analysis" in result
    assert "enhanced" in result
    assert "consensus" in result
`,
      },
    ],
  },
  {
    id: 'README.md',
    name: 'README.md',
    type: 'file',
    language: 'markdown',
    content: `# Helix Project

A multi-agent AI automation project built on the Helix platform.

## Getting Started

\`\`\`bash
npm install
npm run dev
\`\`\`

## Agents

- **Kael** - Analytical processing and pattern recognition
- **Lumina** - Creative content generation
- **Vega** - Technical engineering and optimization
- **Kavach** - Security and ethical review
`,
  },
];

const LANGUAGE_MAP: Record<string, string> = {
  ts: 'typescript',
  tsx: 'typescript',
  js: 'javascript',
  jsx: 'javascript',
  py: 'python',
  go: 'go',
  rs: 'rust',
  java: 'java',
  cpp: 'cpp',
  html: 'html',
  css: 'css',
  json: 'json',
  md: 'markdown',
};

function getLanguageFromFilename(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() || '';
  return LANGUAGE_MAP[ext] || 'plaintext';
}

function FileTreeItem({
  node,
  depth,
  onFileClick,
  onToggleFolder,
}: {
  node: FileNode;
  depth: number;
  onFileClick: (node: FileNode) => void;
  onToggleFolder: (id: string) => void;
}) {
  const isFolder = node.type === 'folder';
  const paddingLeft = depth * 16 + 8;

  return (
    <>
      <div
        className="flex items-center gap-1 py-1 px-2 hover:bg-accent/50 cursor-pointer text-sm rounded-sm transition-colors"
        style={{ paddingLeft }}
        onClick={() => (isFolder ? onToggleFolder(node.id) : onFileClick(node))}
      >
        {isFolder ? (
          <>
            {node.expanded ? (
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
            )}
            {node.expanded ? (
              <FolderOpen className="h-4 w-4 text-yellow-400 shrink-0" />
            ) : (
              <Folder className="h-4 w-4 text-yellow-400 shrink-0" />
            )}
          </>
        ) : (
          <>
            <span className="w-3.5 shrink-0" />
            <File className="h-4 w-4 text-blue-400 shrink-0" />
          </>
        )}
        <span className="truncate text-foreground/80">{node.name}</span>
      </div>
      {isFolder &&
        node.expanded &&
        node.children?.map((child) => (
          <FileTreeItem
            key={child.id}
            node={child}
            depth={depth + 1}
            onFileClick={onFileClick}
            onToggleFolder={onToggleFolder}
          />
        ))}
    </>
  );
}

export default function CodeEditorPage() {
  const [files, setFiles] = useState<FileNode[]>(DEFAULT_FILES);
  const [openTabs, setOpenTabs] = useState<OpenTab[]>([
    {
      id: 'src/main.ts',
      name: 'main.ts',
      language: 'typescript',
      content: DEFAULT_FILES[0].children![0].content!,
      modified: false,
    },
  ]);
  const [activeTabId, setActiveTabId] = useState<string>('src/main.ts');
  const [terminalOutput, setTerminalOutput] = useState<string[]>([
    '$ helix init',
    'Helix initialized',
    'Agents loaded: kael, lumina, vega, kavach',
    'UCF Level: 7.2 (operational)',
    '$ _',
  ]);
  const [showTerminal, setShowTerminal] = useState(true);
  const [aiSuggestion, setAiSuggestion] = useState<string | null>(null);
  const [showAiPanel, setShowAiPanel] = useState(false);

  const activeTab = openTabs.find((t) => t.id === activeTabId);

  const handleFileClick = (node: FileNode) => {
    if (node.type !== 'file') return;

    const existing = openTabs.find((t) => t.id === node.id);
    if (existing) {
      setActiveTabId(node.id);
      return;
    }

    const newTab: OpenTab = {
      id: node.id,
      name: node.name,
      language: node.language || getLanguageFromFilename(node.name),
      content: node.content || '',
      modified: false,
    };

    setOpenTabs([...openTabs, newTab]);
    setActiveTabId(node.id);
  };

  const handleCloseTab = (tabId: string) => {
    const newTabs = openTabs.filter((t) => t.id !== tabId);
    setOpenTabs(newTabs);
    if (activeTabId === tabId) {
      setActiveTabId(newTabs.length > 0 ? newTabs[newTabs.length - 1].id : '');
    }
  };

  const handleToggleFolder = (folderId: string) => {
    const toggleInTree = (nodes: FileNode[]): FileNode[] =>
      nodes.map((n) => {
        if (n.id === folderId) return { ...n, expanded: !n.expanded };
        if (n.children) return { ...n, children: toggleInTree(n.children) };
        return n;
      });
    setFiles(toggleInTree(files));
  };

  const handleSave = (code: string) => {
    setOpenTabs(
      openTabs.map((t) => (t.id === activeTabId ? { ...t, content: code, modified: false } : t))
    );
    setTerminalOutput([...terminalOutput, `$ saved ${activeTab?.name}`, 'File saved successfully']);
  };

  const handleRun = async (code: string) => {
    const lang = activeTab?.language || 'unknown';
    setTerminalOutput((prev) => [
      ...prev,
      `$ helix run ${activeTab?.name} --lang ${lang}`,
      'Executing...',
    ]);
    setShowTerminal(true);

    try {
      const res = await fetch(
        `${API_BASE_URL}/api/web-os/terminal/execute?command=${encodeURIComponent(
          `run ${activeTab?.name}`
        )}`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (res.ok) {
        const result = await res.json();
        setTerminalOutput((prev) =>
          [
            ...prev,
            result.output || 'No output',
            result.error ? `Error: ${result.error}` : '',
            `Exit code: ${result.exit_code}`,
            '$ _',
          ].filter(Boolean)
        );
      } else {
        const errText = await res.text().catch(() => 'Unknown error');
        setTerminalOutput((prev) => [
          ...prev,
          `Error: execution failed (${res.status}) — ${errText}`,
          '$ _',
        ]);
      }
    } catch (err) {
      logger.warn('Terminal execute endpoint unavailable:', err);
      setTerminalOutput((prev) => [
        ...prev,
        'Error: backend unavailable — check your connection and try again',
        '$ _',
      ]);
    }
  };

  const handleAiAssist = async () => {
    setShowAiPanel(true);
    setAiSuggestion('Analyzing your code...');

    try {
      const res = await fetch('/api/copilot/message', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `Review this code and suggest improvements:\n\n${(
            activeTab?.content || ''
          ).slice(0, 2000)}`,
          agent: 'kael',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        const reply = data.response || data.message || data.content;
        if (reply) {
          setAiSuggestion(reply);
          return;
        }
      }
    } catch (error) {
      logger.warn('Code editor AI suggestion API unavailable:', error);
    }

    setAiSuggestion('AI assistant is currently unavailable. Please try again later.');
  };

  return (
    <MarketplaceLayout>
      <div className="min-h-screen bg-gradient-to-b from-background via-indigo-950/30 to-background">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-6">
            <Link
              href="/marketplace/web-os"
              className="text-ucf-harmony hover:text-ucf-harmony/80 mb-4 inline-block"
            >
              &larr; Back to Web OS
            </Link>
            <div className="flex items-center justify-between">
              <div>
                <h1 className="font-heading text-4xl font-bold mb-2 text-foreground">
                  Code Editor AI
                </h1>
                <p className="text-muted-foreground">
                  Intelligent code editor with AI suggestions and Helix agent integration
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <GitBranch className="h-4 w-4 mr-2" />
                  main
                </Button>
                <Button variant="outline" size="sm" onClick={handleAiAssist}>
                  <Sparkles className="h-4 w-4 mr-2" />
                  AI Assist
                </Button>
                <Button variant="outline" size="sm" onClick={() => setShowTerminal(!showTerminal)}>
                  <Terminal className="h-4 w-4 mr-2" />
                  Terminal
                </Button>
              </div>
            </div>
          </div>

          {/* Main Editor Layout */}
          <div
            className="flex gap-0 rounded-lg overflow-hidden border border-border"
            style={{ height: 'calc(100vh - 220px)' }}
          >
            {/* File Explorer Sidebar */}
            <div className="w-64 bg-card/80 border-r border-border flex flex-col shrink-0">
              <div className="p-3 border-b border-border flex items-center justify-between">
                <span className="text-sm font-medium text-foreground/80">Explorer</span>
                <div className="flex gap-1">
                  <button className="p-1 hover:bg-accent rounded" title="New File">
                    <FilePlus className="h-3.5 w-3.5 text-muted-foreground" />
                  </button>
                  <button className="p-1 hover:bg-accent rounded" title="New Folder">
                    <FolderPlus className="h-3.5 w-3.5 text-muted-foreground" />
                  </button>
                </div>
              </div>
              <div className="flex-1 overflow-auto py-1">
                {files.map((node) => (
                  <FileTreeItem
                    key={node.id}
                    node={node}
                    depth={0}
                    onFileClick={handleFileClick}
                    onToggleFolder={handleToggleFolder}
                  />
                ))}
              </div>
            </div>

            {/* Editor Area */}
            <div className="flex-1 flex flex-col min-w-0">
              {/* Tabs */}
              <div className="flex bg-card/60 border-b border-border overflow-x-auto">
                {openTabs.map((tab) => (
                  <div
                    key={tab.id}
                    className={`flex items-center gap-2 px-4 py-2 text-sm cursor-pointer border-r border-border shrink-0 transition-colors ${
                      tab.id === activeTabId
                        ? 'bg-background text-foreground border-b-2 border-b-cyan-400'
                        : 'text-muted-foreground hover:bg-accent/30'
                    }`}
                    onClick={() => setActiveTabId(tab.id)}
                  >
                    <Code2 className="h-3.5 w-3.5" />
                    <span>{tab.name}</span>
                    {tab.modified && <span className="w-2 h-2 rounded-full bg-yellow-400" />}
                    <button
                      className="ml-1 p-0.5 hover:bg-accent rounded"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCloseTab(tab.id);
                      }}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Monaco Editor */}
              <div className={`flex-1 ${showTerminal ? '' : ''}`}>
                {activeTab ? (
                  <CodeEditor
                    key={activeTab.id}
                    defaultLanguage={activeTab.language}
                    defaultCode={activeTab.content}
                    onSave={handleSave}
                    onRun={handleRun}
                  />
                ) : (
                  <div className="h-full flex items-center justify-center text-muted-foreground">
                    <div className="text-center">
                      <Code2 className="h-16 w-16 mx-auto mb-4 opacity-20" />
                      <p>Select a file to start editing</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Terminal Panel */}
              {showTerminal && (
                <div className="h-40 border-t border-border bg-black/90 flex flex-col">
                  <div className="flex items-center justify-between px-3 py-1 bg-card/30 border-b border-border">
                    <span className="text-xs text-muted-foreground flex items-center gap-2">
                      <Terminal className="h-3 w-3" />
                      Terminal
                    </span>
                    <div className="flex gap-1">
                      <button
                        className="p-0.5 hover:bg-accent rounded"
                        onClick={() => setTerminalOutput(['$ _'])}
                        title="Clear"
                      >
                        <Trash2 className="h-3 w-3 text-muted-foreground" />
                      </button>
                      <button
                        className="p-0.5 hover:bg-accent rounded"
                        onClick={() => setShowTerminal(false)}
                      >
                        <X className="h-3 w-3 text-muted-foreground" />
                      </button>
                    </div>
                  </div>
                  <div className="flex-1 overflow-auto p-3 font-mono text-xs">
                    {terminalOutput.map((line, i) => (
                      <div key={i} className="text-green-400">
                        {line}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* AI Assistant Panel */}
            {showAiPanel && (
              <div className="w-80 bg-card/80 border-l border-border flex flex-col shrink-0">
                <div className="p-3 border-b border-border flex items-center justify-between">
                  <span className="text-sm font-medium flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-purple-400" />
                    AI Assistant
                  </span>
                  <button
                    className="p-1 hover:bg-accent rounded"
                    onClick={() => setShowAiPanel(false)}
                  >
                    <X className="h-3.5 w-3.5 text-muted-foreground" />
                  </button>
                </div>
                <div className="flex-1 overflow-auto p-4">
                  {aiSuggestion && (
                    <Card className="p-4 bg-purple-500/10 border-purple-500/30">
                      <div className="flex items-start gap-2 mb-3">
                        <Sparkles className="h-4 w-4 text-purple-400 mt-0.5 shrink-0" />
                        <p className="text-sm font-medium text-purple-200">Lumina suggests:</p>
                      </div>
                      <p className="text-sm text-foreground/80 whitespace-pre-wrap">
                        {aiSuggestion}
                      </p>
                      <div className="flex gap-2 mt-4">
                        <Button size="sm" className="bg-purple-600 hover:bg-purple-700">
                          Apply All
                        </Button>
                        <Button size="sm" variant="outline">
                          Dismiss
                        </Button>
                      </div>
                    </Card>
                  )}

                  <div className="mt-4 space-y-3">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start"
                      onClick={handleAiAssist}
                    >
                      <MessageSquare className="h-4 w-4 mr-2" />
                      Explain this code
                    </Button>
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <Search className="h-4 w-4 mr-2" />
                      Find bugs
                    </Button>
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <Sparkles className="h-4 w-4 mr-2" />
                      Optimize code
                    </Button>
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <Code2 className="h-4 w-4 mr-2" />
                      Generate tests
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </MarketplaceLayout>
  );
}
