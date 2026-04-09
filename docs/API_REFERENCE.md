# Helix Web OS - API Reference

Complete API documentation for the browser-based AI service platform.

## Table of Contents

1. [Browser AI Service](#browser-ai-service)
2. [File System](#file-system)
3. [Terminal Executor](#terminal-executor)
4. [Workflow Engine](#workflow-engine)
5. [Monitoring & Health](#monitoring--health)
6. [Error Handling](#error-handling)
7. [Examples](#examples)

---

## Browser AI Service

The core service for running AI agents and executing tasks in the browser.

### Initialization

```python
from helix_web_os import BrowserAIService

service = BrowserAIService(
    service_id="service_001",
    api_key="your_api_key",
    api_url="http://localhost:8000",
    timeout=30
)

await service.initialize()
```

### Methods

#### `execute_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]`

Execute a complete workflow with multiple steps.

**Parameters:**
- `workflow` (Dict): Workflow configuration with steps and metadata

**Returns:**
- `Dict` with `status`, `workflow_id`, `results`

**Example:**
```python
workflow = {
    "workflow_id": "wf_001",
    "name": "Data Processing",
    "steps": [
        {
            "step_id": "step_001",
            "type": "ai_execution",
            "payload": {"prompt": "Analyze this data"}
        }
    ],
    "timeout": 300
}

result = await service.execute_workflow(workflow)
print(result["status"])  # "success"
```

#### `execute_task(task: Dict[str, Any]) -> Dict[str, Any]`

Execute a single task with AI.

**Parameters:**
- `task` (Dict): Task configuration with type and payload

**Returns:**
- `Dict` with `status`, `task_id`, `output`

**Example:**
```python
task = {
    "task_id": "task_001",
    "type": "ai_execution",
    "payload": {
        "prompt": "What is the capital of France?",
        "model": "gpt-4",
        "temperature": 0.7
    },
    "timeout": 30
}

result = await service.execute_task(task)
print(result["output"])  # "The capital of France is Paris."
```

#### `get_status() -> Dict[str, Any]`

Get current service status.

**Returns:**
- `Dict` with `status`, `uptime`, `active_tasks`

**Example:**
```python
status = await service.get_status()
print(status["status"])  # "active"
```

#### `shutdown() -> bool`

Shutdown the service gracefully.

**Returns:**
- `bool`: True if successful

**Example:**
```python
await service.shutdown()
```

---

## File System

Access and manage files in the browser environment.

### Initialization

```python
from helix_web_os import FileSystem

fs = FileSystem(
    root_path="/home/user",
    max_file_size=10485760  # 10MB
)

await fs.initialize()
```

### Methods

#### `read_file(path: str) -> str`

Read file contents.

**Parameters:**
- `path` (str): File path

**Returns:**
- `str`: File contents

**Example:**
```python
content = await fs.read_file("data.txt")
print(content)
```

#### `write_file(path: str, content: str) -> bool`

Write content to file.

**Parameters:**
- `path` (str): File path
- `content` (str): Content to write

**Returns:**
- `bool`: True if successful

**Example:**
```python
await fs.write_file("output.txt", "Hello, World!")
```

#### `delete_file(path: str) -> bool`

Delete a file.

**Parameters:**
- `path` (str): File path

**Returns:**
- `bool`: True if successful

**Example:**
```python
await fs.delete_file("temp.txt")
```

#### `list_files(path: str) -> List[str]`

List files in directory.

**Parameters:**
- `path` (str): Directory path

**Returns:**
- `List[str]`: File names

**Example:**
```python
files = await fs.list_files("/home/user")
for file in files:
    print(file)
```

#### `get_file_info(path: str) -> Dict[str, Any]`

Get file metadata.

**Parameters:**
- `path` (str): File path

**Returns:**
- `Dict` with `size`, `type`, `created`, `modified`

**Example:**
```python
info = await fs.get_file_info("data.txt")
print(f"Size: {info['size']} bytes")
```

#### `create_directory(path: str) -> bool`

Create a directory.

**Parameters:**
- `path` (str): Directory path

**Returns:**
- `bool`: True if successful

**Example:**
```python
await fs.create_directory("/home/user/projects")
```

#### `delete_directory(path: str) -> bool`

Delete a directory.

**Parameters:**
- `path` (str): Directory path

**Returns:**
- `bool`: True if successful

**Example:**
```python
await fs.delete_directory("/home/user/old_projects")
```

---

## Terminal Executor

Execute commands and scripts in the browser terminal.

### Initialization

```python
from helix_web_os import TerminalExecutor

executor = TerminalExecutor(
    shell="/bin/bash",
    timeout=60,
    max_output_size=1048576  # 1MB
)

await executor.initialize()
```

### Methods

#### `execute_command(command: str) -> Dict[str, Any]`

Execute a shell command.

**Parameters:**
- `command` (str): Command to execute

**Returns:**
- `Dict` with `status`, `output`, `exit_code`

**Example:**
```python
result = await executor.execute_command("ls -la")
print(result["output"])
print(f"Exit code: {result['exit_code']}")
```

#### `execute_script(script_path: str) -> Dict[str, Any]`

Execute a script file.

**Parameters:**
- `script_path` (str): Path to script

**Returns:**
- `Dict` with `status`, `output`

**Example:**
```python
result = await executor.execute_script("setup.sh")
print(result["output"])
```

#### `get_status() -> Dict[str, Any]`

Get executor status.

**Returns:**
- `Dict` with `status`, `shell`, `uptime`

**Example:**
```python
status = await executor.get_status()
print(status["shell"])  # "/bin/bash"
```

---

## Workflow Engine

Create and manage complex workflows with multiple steps.

### Initialization

```python
from helix_web_os import WorkflowEngine

engine = WorkflowEngine(
    max_workflows=100,
    timeout=300
)

await engine.initialize()
```

### Methods

#### `create_workflow(config: Dict[str, Any]) -> Dict[str, Any]`

Create a new workflow.

**Parameters:**
- `config` (Dict): Workflow configuration

**Returns:**
- `Dict` with `workflow_id`, `status`

**Example:**
```python
config = {
    "name": "Data Pipeline",
    "steps": [
        {"step_id": "step_1", "type": "ai_execution"},
        {"step_id": "step_2", "type": "file_operation"}
    ]
}

result = await engine.create_workflow(config)
print(result["workflow_id"])
```

#### `execute_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]`

Execute a workflow.

**Parameters:**
- `workflow` (Dict): Workflow configuration

**Returns:**
- `Dict` with `status`, `results`

**Example:**
```python
result = await engine.execute_workflow(workflow)
print(result["status"])  # "success"
```

#### `get_workflow_status(workflow_id: str) -> Dict[str, Any]`

Get workflow status.

**Parameters:**
- `workflow_id` (str): Workflow ID

**Returns:**
- `Dict` with `status`, `progress`, `current_step`

**Example:**
```python
status = await engine.get_workflow_status("wf_001")
print(f"Progress: {status['progress']}%")
```

#### `cancel_workflow(workflow_id: str) -> bool`

Cancel a running workflow.

**Parameters:**
- `workflow_id` (str): Workflow ID

**Returns:**
- `bool`: True if successful

**Example:**
```python
await engine.cancel_workflow("wf_001")
```

#### `list_workflows() -> List[Dict[str, Any]]`

List all workflows.

**Returns:**
- `List[Dict]`: Workflow list

**Example:**
```python
workflows = await engine.list_workflows()
for wf in workflows:
    print(f"{wf['workflow_id']}: {wf['name']}")
```

---

## Monitoring & Health

Monitor service health and collect metrics.

### Health Monitoring

```python
from helix_web_os import HealthMonitor

monitor = HealthMonitor()

# Check service health
health = await monitor.check_service_health()
print(health["status"])  # "healthy"

# Get health report
report = await monitor.get_health_report()
```

### Metrics Collection

```python
from helix_web_os import MetricsCollector

collector = MetricsCollector()

# Record metric
collector.record_metric("latency", 15.5)
collector.record_metric("throughput", 100)

# Get metrics
metrics = collector.get_metrics()
print(metrics)
```

---

## Error Handling

Handle errors gracefully with custom exceptions.

### Exception Types

```python
from helix_web_os.exceptions import (
    HelixWebOSException,
    ServiceInitializationError,
    FileSystemError,
    TerminalExecutionError,
    WorkflowExecutionError,
    TimeoutError,
    ValidationError
)
```

### Error Handling Example

```python
try:
    result = await service.execute_task(task)
except ValidationError as e:
    print(f"Validation failed: {e}")
except TimeoutError as e:
    print(f"Task timed out: {e}")
except HelixWebOSException as e:
    print(f"Error: {e}")
```

---

## Examples

### Complete Workflow Example

```python
import asyncio
from helix_web_os import (
    BrowserAIService,
    FileSystem,
    TerminalExecutor,
    WorkflowEngine
)

async def main():
    # Initialize services
    service = BrowserAIService()
    fs = FileSystem()
    executor = TerminalExecutor()
    engine = WorkflowEngine()
    
    await service.initialize()
    await fs.initialize()
    await executor.initialize()
    await engine.initialize()
    
    # Create workflow
    workflow = {
        "workflow_id": "wf_001",
        "name": "Complete Pipeline",
        "steps": [
            {
                "step_id": "step_1",
                "type": "ai_execution",
                "payload": {"prompt": "Analyze data"}
            },
            {
                "step_id": "step_2",
                "type": "file_operation",
                "payload": {"operation": "write", "file": "results.txt"}
            },
            {
                "step_id": "step_3",
                "type": "terminal_execution",
                "payload": {"command": "echo 'Pipeline complete'"}
            }
        ]
    }
    
    # Execute workflow
    result = await engine.execute_workflow(workflow)
    print(f"Workflow result: {result['status']}")
    
    # Shutdown
    await service.shutdown()

asyncio.run(main())
```

### File Processing Example

```python
async def process_files():
    fs = FileSystem()
    await fs.initialize()
    
    # List files
    files = await fs.list_files("/home/user/data")
    
    # Process each file
    for file in files:
        content = await fs.read_file(f"/home/user/data/{file}")
        processed = content.upper()
        await fs.write_file(f"/home/user/output/{file}", processed)
```

### Task Execution Example

```python
async def execute_tasks():
    service = BrowserAIService()
    await service.initialize()
    
    tasks = [
        {"task_id": f"task_{i}", "payload": {"prompt": f"Task {i}"}}
        for i in range(10)
    ]
    
    results = []
    for task in tasks:
        result = await service.execute_task(task)
        results.append(result)
    
    return results
```

---

## Configuration

### Environment Variables

```bash
# Service Configuration
HELIX_API_KEY=your_api_key
HELIX_API_URL=http://localhost:8000
HELIX_TIMEOUT=30

# File System Configuration
HELIX_ROOT_PATH=/home/user
HELIX_MAX_FILE_SIZE=10485760

# Terminal Configuration
HELIX_SHELL=/bin/bash
HELIX_TERMINAL_TIMEOUT=60

# Workflow Configuration
HELIX_MAX_WORKFLOWS=100
HELIX_WORKFLOW_TIMEOUT=300
```

---

## Best Practices

1. **Always initialize services** before use
2. **Use try-except blocks** for error handling
3. **Set appropriate timeouts** for long-running tasks
4. **Monitor health regularly** in production
5. **Log important events** for debugging
6. **Clean up resources** with shutdown()
7. **Use async/await** for non-blocking operations
8. **Validate input** before execution

---

**Last Updated**: 2024-04-07  
**Version**: 1.0.0
