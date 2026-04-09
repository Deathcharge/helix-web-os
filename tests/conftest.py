"""
Pytest Configuration and Fixtures for Helix Web OS

Provides comprehensive fixtures, mocks, and utilities for testing
the browser-based AI service platform.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional


# =============================================================================
# EVENT LOOP FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# BROWSER AI SERVICE FIXTURES
# =============================================================================

@pytest.fixture
def mock_browser_ai_service():
    """Mock BrowserAIService."""
    service = AsyncMock()
    service.service_id = "service_001"
    service.name = "Browser AI Service"
    service.status = "active"
    
    # Methods
    service.initialize = AsyncMock(return_value=True)
    service.shutdown = AsyncMock(return_value=True)
    service.execute_workflow = AsyncMock(return_value={"status": "success"})
    service.execute_task = AsyncMock(return_value={"status": "success"})
    service.get_status = AsyncMock(return_value={"status": "active"})
    
    return service


@pytest.fixture
def browser_ai_config() -> Dict[str, Any]:
    """Browser AI Service configuration."""
    return {
        "service_id": "service_001",
        "name": "Browser AI Service",
        "api_key": "test_key_123",
        "api_url": "http://localhost:8000",
        "timeout": 30,
        "max_retries": 3,
        "enable_logging": True,
        "enable_monitoring": True,
    }


# =============================================================================
# FILE SYSTEM FIXTURES
# =============================================================================

@pytest.fixture
def mock_file_system():
    """Mock FileSystem."""
    fs = AsyncMock()
    fs.fs_id = "fs_001"
    fs.root_path = "/home/user"
    
    # Methods
    fs.initialize = AsyncMock(return_value=True)
    fs.read_file = AsyncMock(return_value="file content")
    fs.write_file = AsyncMock(return_value=True)
    fs.delete_file = AsyncMock(return_value=True)
    fs.list_files = AsyncMock(return_value=["file1.txt", "file2.txt"])
    fs.get_file_info = AsyncMock(return_value={"size": 1024, "type": "text"})
    fs.create_directory = AsyncMock(return_value=True)
    fs.delete_directory = AsyncMock(return_value=True)
    
    return fs


@pytest.fixture
def file_system_config() -> Dict[str, Any]:
    """File system configuration."""
    return {
        "fs_id": "fs_001",
        "root_path": "/home/user",
        "max_file_size": 10485760,  # 10MB
        "allowed_extensions": [".txt", ".py", ".json", ".md"],
        "enable_logging": True,
    }


# =============================================================================
# TERMINAL EXECUTOR FIXTURES
# =============================================================================

@pytest.fixture
def mock_terminal_executor():
    """Mock TerminalExecutor."""
    executor = AsyncMock()
    executor.executor_id = "executor_001"
    executor.shell = "/bin/bash"
    
    # Methods
    executor.initialize = AsyncMock(return_value=True)
    executor.execute_command = AsyncMock(return_value={
        "status": "success",
        "output": "command output",
        "exit_code": 0
    })
    executor.execute_script = AsyncMock(return_value={
        "status": "success",
        "output": "script output"
    })
    executor.get_status = AsyncMock(return_value={"status": "active"})
    
    return executor


@pytest.fixture
def terminal_config() -> Dict[str, Any]:
    """Terminal executor configuration."""
    return {
        "executor_id": "executor_001",
        "shell": "/bin/bash",
        "timeout": 60,
        "max_output_size": 1048576,  # 1MB
        "allowed_commands": ["ls", "pwd", "cat", "echo"],
        "enable_logging": True,
    }


# =============================================================================
# WORKFLOW ENGINE FIXTURES
# =============================================================================

@pytest.fixture
def mock_workflow_engine():
    """Mock WorkflowEngine."""
    engine = AsyncMock()
    engine.engine_id = "engine_001"
    engine.workflows = {}
    
    # Methods
    engine.initialize = AsyncMock(return_value=True)
    engine.create_workflow = AsyncMock(return_value={"workflow_id": "wf_001"})
    engine.execute_workflow = AsyncMock(return_value={"status": "success"})
    engine.get_workflow_status = AsyncMock(return_value={"status": "running"})
    engine.cancel_workflow = AsyncMock(return_value=True)
    engine.list_workflows = AsyncMock(return_value=[])
    
    return engine


@pytest.fixture
def workflow_config() -> Dict[str, Any]:
    """Workflow configuration."""
    return {
        "engine_id": "engine_001",
        "max_workflows": 100,
        "timeout": 300,
        "enable_logging": True,
    }


# =============================================================================
# TASK FIXTURES
# =============================================================================

@pytest.fixture
def sample_task() -> Dict[str, Any]:
    """Sample task for testing."""
    return {
        "task_id": "task_001",
        "type": "ai_execution",
        "priority": "high",
        "payload": {
            "prompt": "What is the capital of France?",
            "model": "gpt-4",
            "temperature": 0.7
        },
        "timeout": 30,
        "retries": 3,
    }


@pytest.fixture
def sample_workflow() -> Dict[str, Any]:
    """Sample workflow for testing."""
    return {
        "workflow_id": "wf_001",
        "name": "Test Workflow",
        "steps": [
            {
                "step_id": "step_001",
                "type": "ai_execution",
                "payload": {"prompt": "Step 1"}
            },
            {
                "step_id": "step_002",
                "type": "file_operation",
                "payload": {"operation": "write", "file": "output.txt"}
            },
            {
                "step_id": "step_003",
                "type": "terminal_execution",
                "payload": {"command": "echo 'Done'"}
            }
        ],
        "timeout": 300,
    }


# =============================================================================
# MONITORING FIXTURES
# =============================================================================

@pytest.fixture
def mock_metrics_collector():
    """Mock MetricsCollector."""
    collector = Mock()
    collector.metrics = {}
    collector.events = []
    
    def record_metric(name: str, value: float):
        collector.metrics[name] = value
    
    def record_event(event_type: str, data: Dict):
        collector.events.append({"type": event_type, "data": data})
    
    def get_metrics():
        return collector.metrics
    
    def get_events():
        return collector.events
    
    collector.record_metric = record_metric
    collector.record_event = record_event
    collector.get_metrics = get_metrics
    collector.get_events = get_events
    
    return collector


@pytest.fixture
def sample_metrics() -> Dict[str, Any]:
    """Sample metrics data."""
    return {
        "latency": 15.5,
        "throughput": 100,
        "cpu_usage": 45.5,
        "memory_usage": 60.2,
        "active_tasks": 5,
        "completed_tasks": 100,
    }


# =============================================================================
# HEALTH MONITORING FIXTURES
# =============================================================================

@pytest.fixture
def mock_health_monitor():
    """Mock HealthMonitor."""
    monitor = AsyncMock()
    
    # Methods
    monitor.check_service_health = AsyncMock(return_value={
        "status": "healthy",
        "cpu": 45,
        "memory": 60,
        "latency": 10
    })
    monitor.check_component_health = AsyncMock(return_value={
        "status": "healthy"
    })
    monitor.get_health_report = AsyncMock(return_value={
        "status": "healthy",
        "components": {}
    })
    
    return monitor


# =============================================================================
# EXCEPTION HANDLER FIXTURES
# =============================================================================

@pytest.fixture
def mock_exception_handler():
    """Mock ExceptionHandler."""
    handler = AsyncMock()
    handler.errors = []
    
    async def handle(error: Exception) -> Dict[str, Any]:
        handler.errors.append(error)
        return {"handled": True, "error": str(error)}
    
    def get_error_count() -> int:
        return len(handler.errors)
    
    handler.handle = handle
    handler.get_error_count = get_error_count
    
    return handler


# =============================================================================
# PERFORMANCE TESTING FIXTURES
# =============================================================================

@pytest.fixture
def performance_timer():
    """Performance timer for benchmarking."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self) -> float:
            self.end_time = time.time()
            return self.end_time - self.start_time
    
    return Timer()


# =============================================================================
# MOCK AGENTS FIXTURES
# =============================================================================

@pytest.fixture
def mock_agent():
    """Mock Agent."""
    agent = AsyncMock()
    agent.agent_id = "agent_001"
    agent.name = "Test Agent"
    agent.role = "worker"
    agent.capabilities = ["reasoning", "tool_use"]
    
    # Methods
    agent.initialize = AsyncMock(return_value=True)
    agent.execute = AsyncMock(return_value={"status": "success"})
    agent.get_status = AsyncMock(return_value={"status": "active"})
    
    return agent


# =============================================================================
# PYTEST MARKERS
# =============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "slow: slow tests")
    config.addinivalue_line("markers", "asyncio: async tests")


# =============================================================================
# PYTEST HOOKS
# =============================================================================

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test."""
    yield
    # Cleanup happens here


@pytest.fixture
def mock_api_response():
    """Mock API response."""
    def _mock_response(status_code=200, json_data=None, text_data=""):
        response = Mock()
        response.status_code = status_code
        response.json = Mock(return_value=json_data or {})
        response.text = text_data
        return response
    
    return _mock_response
