# Helix Web OS - Getting Started Guide

Quick start guide for the browser-based AI service platform.

## Installation

### Prerequisites

- Python 3.8+
- pip or conda
- Modern web browser

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/Deathcharge/helix-web-os.git
cd helix-web-os
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
export HELIX_API_KEY=your_api_key
export HELIX_API_URL=http://localhost:8000
```

4. **Verify installation**
```bash
python -c "from helix_web_os import BrowserAIService; print('Installation successful!')"
```

---

## Basic Usage

### 1. Simple Task Execution

Execute a single AI task:

```python
import asyncio
from helix_web_os import BrowserAIService

async def main():
    service = BrowserAIService()
    await service.initialize()
    
    task = {
        "task_id": "task_001",
        "type": "ai_execution",
        "payload": {
            "prompt": "What is the capital of France?",
            "model": "gpt-4"
        }
    }
    
    result = await service.execute_task(task)
    print(f"Result: {result}")
    
    await service.shutdown()

asyncio.run(main())
```

### 2. File Operations

Read and write files:

```python
import asyncio
from helix_web_os import FileSystem

async def main():
    fs = FileSystem()
    await fs.initialize()
    
    # Write file
    await fs.write_file("hello.txt", "Hello, World!")
    
    # Read file
    content = await fs.read_file("hello.txt")
    print(content)
    
    # List files
    files = await fs.list_files(".")
    print(files)

asyncio.run(main())
```

### 3. Terminal Commands

Execute shell commands:

```python
import asyncio
from helix_web_os import TerminalExecutor

async def main():
    executor = TerminalExecutor()
    await executor.initialize()
    
    # Execute command
    result = await executor.execute_command("ls -la")
    print(result["output"])
    
    # Check exit code
    if result["exit_code"] == 0:
        print("Command successful!")

asyncio.run(main())
```

### 4. Workflow Execution

Create and execute workflows:

```python
import asyncio
from helix_web_os import WorkflowEngine

async def main():
    engine = WorkflowEngine()
    await engine.initialize()
    
    workflow = {
        "workflow_id": "wf_001",
        "name": "My First Workflow",
        "steps": [
            {
                "step_id": "step_1",
                "type": "ai_execution",
                "payload": {"prompt": "Step 1"}
            },
            {
                "step_id": "step_2",
                "type": "file_operation",
                "payload": {"operation": "write", "file": "output.txt"}
            }
        ]
    }
    
    result = await engine.execute_workflow(workflow)
    print(f"Status: {result['status']}")

asyncio.run(main())
```

---

## Common Patterns

### Pattern 1: Data Processing Pipeline

Process data through multiple steps:

```python
async def data_pipeline():
    service = BrowserAIService()
    fs = FileSystem()
    
    await service.initialize()
    await fs.initialize()
    
    # Read input data
    data = await fs.read_file("input.txt")
    
    # Process with AI
    task = {
        "payload": {"prompt": f"Process this: {data}"}
    }
    result = await service.execute_task(task)
    
    # Write output
    await fs.write_file("output.txt", result["output"])
```

### Pattern 2: Batch Task Execution

Execute multiple tasks in parallel:

```python
async def batch_execution():
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

### Pattern 3: Conditional Workflow

Workflow with conditional logic:

```python
async def conditional_workflow():
    engine = WorkflowEngine()
    await engine.initialize()
    
    workflow = {
        "workflow_id": "wf_conditional",
        "steps": [
            {
                "step_id": "check",
                "type": "ai_execution",
                "payload": {"prompt": "Check condition"}
            },
            {
                "step_id": "action",
                "type": "conditional",
                "condition": "check.result == 'true'",
                "then_step": "success",
                "else_step": "failure"
            }
        ]
    }
    
    result = await engine.execute_workflow(workflow)
    return result
```

### Pattern 4: Error Handling

Robust error handling:

```python
async def robust_execution():
    service = BrowserAIService()
    
    try:
        await service.initialize()
        
        task = {"payload": {"prompt": "Test"}}
        result = await service.execute_task(task)
        
    except TimeoutError:
        print("Task timed out!")
    except ValidationError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await service.shutdown()
```

---

## Configuration

### Basic Configuration

```python
from helix_web_os import BrowserAIService

service = BrowserAIService(
    service_id="my_service",
    api_key="your_api_key",
    api_url="http://localhost:8000",
    timeout=30,
    max_retries=3
)
```

### Environment Configuration

```bash
# .env file
HELIX_API_KEY=your_api_key
HELIX_API_URL=http://localhost:8000
HELIX_TIMEOUT=30
HELIX_MAX_RETRIES=3
HELIX_LOG_LEVEL=INFO
```

### Advanced Configuration

```python
config = {
    "service": {
        "timeout": 60,
        "max_retries": 5,
        "enable_monitoring": True
    },
    "file_system": {
        "root_path": "/home/user",
        "max_file_size": 10485760
    },
    "terminal": {
        "shell": "/bin/bash",
        "timeout": 120
    },
    "workflow": {
        "max_workflows": 100,
        "timeout": 300
    }
}
```

---

## Monitoring

### Health Checks

```python
from helix_web_os import HealthMonitor

monitor = HealthMonitor()

# Check service health
health = await monitor.check_service_health()
print(f"Status: {health['status']}")

# Get full report
report = await monitor.get_health_report()
print(report)
```

### Metrics Collection

```python
from helix_web_os import MetricsCollector

collector = MetricsCollector()

# Record metrics
collector.record_metric("latency", 15.5)
collector.record_metric("throughput", 100)

# Get metrics
metrics = collector.get_metrics()
print(metrics)
```

---

## Troubleshooting

### Issue: Service fails to initialize

**Solution**: Check API credentials and network connectivity
```bash
export HELIX_API_KEY=your_correct_key
export HELIX_API_URL=http://localhost:8000
```

### Issue: File operations timeout

**Solution**: Increase timeout value
```python
fs = FileSystem(timeout=60)
```

### Issue: Terminal command not found

**Solution**: Use full path to command
```python
result = await executor.execute_command("/usr/bin/python3 script.py")
```

### Issue: Workflow execution fails

**Solution**: Check workflow configuration and enable logging
```python
engine = WorkflowEngine(enable_logging=True)
```

---

## Testing

### Run Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_web_os_components.py::test_browser_ai_service_initialization
```

### Write Tests

```python
import pytest
from helix_web_os import BrowserAIService

@pytest.mark.asyncio
async def test_task_execution(mock_browser_ai_service):
    result = await mock_browser_ai_service.execute_task({"task_id": "test"})
    assert result["status"] == "success"
```

---

## Next Steps

1. **Explore Examples**: Check the `examples/` directory
2. **Read API Reference**: See `docs/API_REFERENCE.md`
3. **Join Community**: Contribute to the project
4. **Report Issues**: Use GitHub Issues for bugs

---

## Resources

- **GitHub**: https://github.com/Deathcharge/helix-web-os
- **Documentation**: https://helix-web-os.readthedocs.io
- **API Reference**: See `docs/API_REFERENCE.md`
- **Examples**: See `examples/` directory

---

**Last Updated**: 2024-04-07  
**Version**: 1.0.0
