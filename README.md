# Helix Web OS

A browser-based AI service platform that brings Helix's powerful AI capabilities directly to the web. Run autonomous agents, manage workflows, and execute complex tasks from your browser.

## Features

- **Browser-Based AI Service** - Run AI agents in the browser
- **File System Integration** - Access and manage files
- **Terminal Executor** - Execute commands and scripts
- **Workflow Management** - Create and manage workflows
- **Real-time Monitoring** - Track agent execution
- **Multi-Agent Support** - Coordinate multiple agents
- **REST API** - Full API for integration

## Components

- `browser_ai_service.py` - Core browser AI service
- `file_system.py` - File system integration
- `terminal_executor.py` - Command execution
- `workflow_engine.py` - Workflow management

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from helix_web_os import BrowserAIService

service = BrowserAIService()
result = await service.execute_workflow(workflow)
```

## Configuration

Set environment variables for:
- `HELIX_API_KEY` - Helix API credentials
- `HELIX_API_URL` - Helix API endpoint

## License

Dual Licensed - Apache 2.0 + Proprietary Commercial

See LICENSE and LICENSING.md for details.
