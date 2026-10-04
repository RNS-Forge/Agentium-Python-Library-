"""
Workflow Helper Module - Orchestrate tasks & triggers

This module provides workflow orchestration capabilities for complex task management,
automation, and trigger-based operations.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future

from ..utils.logger_utils import LoggerUtils


class WorkflowStatus(Enum):
    """Workflow execution statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskStatus(Enum):
    """Individual task statuses"""
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TriggerType(Enum):
    """Types of workflow triggers"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    WEBHOOK = "webhook"
    FILE_WATCH = "file_watch"
    CONDITION = "condition"


@dataclass
class Task:
    """Individual task definition"""
    id: str
    name: str
    function: Union[Callable, str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: Optional[int] = None
    retry_attempts: int = 0
    retry_delay: int = 1
    condition: Optional[Callable] = None
    on_success: Optional[Callable] = None
    on_failure: Optional[Callable] = None
    status: TaskStatus = TaskStatus.WAITING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution"""
    max_parallel_tasks: int = 5
    default_timeout: int = 300
    retry_failed_tasks: bool = True
    continue_on_failure: bool = False
    save_intermediate_results: bool = True
    log_level: str = "INFO"


class WorkflowHelper:
    """
    Advanced workflow orchestration system.
    
    Features:
    - Task dependency management
    - Parallel execution
    - Error handling and retries
    - Conditional execution
    - Event-based triggers
    - Progress monitoring
    - Result persistence
    - Workflow templates
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        self.config = config or WorkflowConfig()
        self.logger = LoggerUtils.get_logger(__name__)
        self.active_workflows: Dict[str, Dict] = {}
        self.workflow_templates: Dict[str, Dict] = {}
        self.triggers: Dict[str, Dict] = {}
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_parallel_tasks)
    
    @LoggerUtils.log_operation("create_workflow")
    def create_workflow(self, name: str, tasks: List[Task], **kwargs) -> str:
        """
        Create a new workflow
        
        Args:
            name: Workflow name
            tasks: List of tasks to execute
            **kwargs: Additional workflow parameters
            
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        
        workflow = {
            'id': workflow_id,
            'name': name,
            'tasks': {task.id: task for task in tasks},
            'status': WorkflowStatus.PENDING,
            'created_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'results': {},
            'metadata': kwargs
        }
        
        # Validate workflow
        self._validate_workflow(workflow)
        
        self.active_workflows[workflow_id] = workflow
        self.logger.info(f"Created workflow '{name}' with {len(tasks)} tasks")
        
        return workflow_id
    
    @LoggerUtils.log_operation("execute_workflow")
    async def execute_workflow(self, workflow_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a workflow
        
        Args:
            workflow_id: ID of workflow to execute
            **kwargs: Runtime parameters
            
        Returns:
            Execution results
        """
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        workflow['status'] = WorkflowStatus.RUNNING
        workflow['started_at'] = datetime.now()
        
        self.logger.info(f"Starting workflow execution: {workflow['name']}")
        
        try:
            # Execute tasks based on dependencies
            results = await self._execute_tasks(workflow, **kwargs)
            
            workflow['status'] = WorkflowStatus.COMPLETED
            workflow['completed_at'] = datetime.now()
            workflow['results'] = results
            
            self.logger.info(f"Workflow completed successfully: {workflow['name']}")
            
            return {
                'workflow_id': workflow_id,
                'status': WorkflowStatus.COMPLETED.value,
                'results': results,
                'execution_time': (workflow['completed_at'] - workflow['started_at']).total_seconds(),
                'tasks_completed': len([t for t in workflow['tasks'].values() if t.status == TaskStatus.COMPLETED])
            }
            
        except Exception as e:
            workflow['status'] = WorkflowStatus.FAILED
            workflow['completed_at'] = datetime.now()
            workflow['error'] = str(e)
            
            self.logger.error(f"Workflow failed: {workflow['name']}: {str(e)}")
            
            return {
                'workflow_id': workflow_id,
                'status': WorkflowStatus.FAILED.value,
                'error': str(e),
                'execution_time': (workflow['completed_at'] - workflow['started_at']).total_seconds(),
                'tasks_completed': len([t for t in workflow['tasks'].values() if t.status == TaskStatus.COMPLETED])
            }
    
    async def _execute_tasks(self, workflow: Dict, **kwargs) -> Dict[str, Any]:
        """Execute tasks based on dependency order"""
        tasks = workflow['tasks']
        results = {}
        completed_tasks = set()
        
        while len(completed_tasks) < len(tasks):
            # Find tasks ready to execute
            ready_tasks = []
            for task_id, task in tasks.items():
                if (task_id not in completed_tasks and 
                    task.status == TaskStatus.WAITING and
                    all(dep in completed_tasks for dep in task.dependencies)):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Check if we're stuck
                remaining_tasks = [t for t in tasks.values() if t.id not in completed_tasks]
                if remaining_tasks:
                    waiting_tasks = [t for t in remaining_tasks if t.status == TaskStatus.WAITING]
                    if waiting_tasks:
                        raise Exception(f"Circular dependency or missing dependencies detected for tasks: {[t.name for t in waiting_tasks]}")
                break
            
            # Execute ready tasks in parallel
            task_futures = []
            for task in ready_tasks[:self.config.max_parallel_tasks]:
                future = self._execute_task_async(task, results, **kwargs)
                task_futures.append((task, future))
            
            # Wait for tasks to complete
            for task, future in task_futures:
                try:
                    result = await future
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    task.end_time = datetime.now()
                    results[task.id] = result
                    completed_tasks.add(task.id)
                    
                    # Execute success callback
                    if task.on_success:
                        try:
                            task.on_success(result)
                        except Exception as e:
                            self.logger.warning(f"Success callback failed for task {task.name}: {str(e)}")
                    
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.end_time = datetime.now()
                    
                    # Execute failure callback
                    if task.on_failure:
                        try:
                            task.on_failure(e)
                        except Exception as callback_error:
                            self.logger.warning(f"Failure callback failed for task {task.name}: {str(callback_error)}")
                    
                    if not self.config.continue_on_failure:
                        raise Exception(f"Task {task.name} failed: {str(e)}")
                    
                    completed_tasks.add(task.id)  # Mark as completed even if failed
        
        return results
    
    async def _execute_task_async(self, task: Task, context: Dict[str, Any], **kwargs) -> Any:
        """Execute a single task asynchronously"""
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        
        self.logger.info(f"Executing task: {task.name}")
        
        # Check condition if specified
        if task.condition and not task.condition(context):
            task.status = TaskStatus.SKIPPED
            self.logger.info(f"Task {task.name} skipped due to condition")
            return None
        
        # Prepare parameters
        params = {**task.parameters, **kwargs}
        params['context'] = context
        
        # Execute task with retries
        for attempt in range(task.retry_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(task.function):
                    # Async function
                    if task.timeout_seconds:
                        result = await asyncio.wait_for(
                            task.function(**params),
                            timeout=task.timeout_seconds
                        )
                    else:
                        result = await task.function(**params)
                else:
                    # Sync function - run in executor
                    loop = asyncio.get_event_loop()
                    if task.timeout_seconds:
                        result = await asyncio.wait_for(
                            loop.run_in_executor(self.executor, lambda: task.function(**params)),
                            timeout=task.timeout_seconds
                        )
                    else:
                        result = await loop.run_in_executor(self.executor, lambda: task.function(**params))
                
                return result
                
            except Exception as e:
                if attempt == task.retry_attempts:
                    raise e
                
                self.logger.warning(f"Task {task.name} failed (attempt {attempt + 1}): {str(e)}")
                await asyncio.sleep(task.retry_delay)
    
    def _validate_workflow(self, workflow: Dict):
        """Validate workflow definition"""
        tasks = workflow['tasks']
        task_ids = set(tasks.keys())
        
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id: str) -> bool:
            if task_id in rec_stack:
                return True
            if task_id in visited:
                return False
            
            visited.add(task_id)
            rec_stack.add(task_id)
            
            for dep in tasks[task_id].dependencies:
                if dep not in task_ids:
                    raise ValueError(f"Task {task_id} depends on non-existent task {dep}")
                if has_cycle(dep):
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        for task_id in task_ids:
            if has_cycle(task_id):
                raise ValueError(f"Circular dependency detected involving task {task_id}")
    
    def add_trigger(self, trigger_type: TriggerType, trigger_config: Dict[str, Any], workflow_id: str) -> str:
        """Add a trigger to a workflow"""
        trigger_id = str(uuid.uuid4())
        
        trigger = {
            'id': trigger_id,
            'type': trigger_type,
            'config': trigger_config,
            'workflow_id': workflow_id,
            'active': True,
            'created_at': datetime.now()
        }
        
        self.triggers[trigger_id] = trigger
        
        # Setup trigger based on type
        if trigger_type == TriggerType.SCHEDULED:
            self._setup_scheduled_trigger(trigger)
        elif trigger_type == TriggerType.EVENT:
            self._setup_event_trigger(trigger)
        elif trigger_type == TriggerType.FILE_WATCH:
            self._setup_file_watch_trigger(trigger)
        elif trigger_type == TriggerType.WEBHOOK:
            self._setup_webhook_trigger(trigger)
        
        return trigger_id
    
    def _setup_scheduled_trigger(self, trigger: Dict):
        """Setup scheduled trigger"""
        # This would integrate with a scheduler like APScheduler
        self.logger.info(f"Scheduled trigger setup (placeholder): {trigger['id']}")
    
    def _setup_event_trigger(self, trigger: Dict):
        """Setup event-based trigger"""
        self.logger.info(f"Event trigger setup (placeholder): {trigger['id']}")
    
    def _setup_file_watch_trigger(self, trigger: Dict):
        """Setup file watch trigger"""
        self.logger.info(f"File watch trigger setup (placeholder): {trigger['id']}")
    
    def _setup_webhook_trigger(self, trigger: Dict):
        """Setup webhook trigger"""
        self.logger.info(f"Webhook trigger setup (placeholder): {trigger['id']}")
    
    def create_template(self, name: str, workflow_definition: Dict[str, Any]) -> str:
        """Create a workflow template"""
        template_id = str(uuid.uuid4())
        
        template = {
            'id': template_id,
            'name': name,
            'definition': workflow_definition,
            'created_at': datetime.now(),
            'usage_count': 0
        }
        
        self.workflow_templates[template_id] = template
        self.logger.info(f"Created workflow template: {name}")
        
        return template_id
    
    def create_from_template(self, template_id: str, name: str, parameters: Optional[Dict] = None) -> str:
        """Create workflow from template"""
        if template_id not in self.workflow_templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.workflow_templates[template_id]
        definition = template['definition'].copy()
        
        # Apply parameters if provided
        if parameters:
            definition = self._apply_template_parameters(definition, parameters)
        
        # Create tasks from definition
        tasks = []
        for task_def in definition.get('tasks', []):
            task = Task(
                id=task_def['id'],
                name=task_def['name'],
                function=task_def['function'],
                parameters=task_def.get('parameters', {}),
                dependencies=task_def.get('dependencies', []),
                timeout_seconds=task_def.get('timeout_seconds'),
                retry_attempts=task_def.get('retry_attempts', 0)
            )
            tasks.append(task)
        
        workflow_id = self.create_workflow(name, tasks)
        template['usage_count'] += 1
        
        return workflow_id
    
    def _apply_template_parameters(self, definition: Dict, parameters: Dict) -> Dict:
        """Apply parameters to template definition"""
        # Simple parameter substitution
        definition_str = json.dumps(definition)
        for key, value in parameters.items():
            definition_str = definition_str.replace(f"{{{{ {key} }}}}", str(value))
        
        return json.loads(definition_str)
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow status"""
        if workflow_id not in self.active_workflows:
            return {'error': 'Workflow not found'}
        
        workflow = self.active_workflows[workflow_id]
        tasks = workflow['tasks']
        
        task_statuses = {}
        for task_id, task in tasks.items():
            task_statuses[task_id] = {
                'name': task.name,
                'status': task.status.value,
                'result': task.result,
                'error': task.error,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None
            }
        
        return {
            'workflow_id': workflow_id,
            'name': workflow['name'],
            'status': workflow['status'].value,
            'created_at': workflow['created_at'].isoformat(),
            'started_at': workflow['started_at'].isoformat() if workflow['started_at'] else None,
            'completed_at': workflow['completed_at'].isoformat() if workflow['completed_at'] else None,
            'tasks': task_statuses,
            'progress': len([t for t in tasks.values() if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]]) / len(tasks) * 100
        }
    
    def pause_workflow(self, workflow_id: str):
        """Pause workflow execution"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            if workflow['status'] == WorkflowStatus.RUNNING:
                workflow['status'] = WorkflowStatus.PAUSED
                self.logger.info(f"Paused workflow: {workflow['name']}")
    
    def resume_workflow(self, workflow_id: str):
        """Resume paused workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            if workflow['status'] == WorkflowStatus.PAUSED:
                workflow['status'] = WorkflowStatus.RUNNING
                self.logger.info(f"Resumed workflow: {workflow['name']}")
    
    def cancel_workflow(self, workflow_id: str):
        """Cancel workflow execution"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow['status'] = WorkflowStatus.CANCELLED
            workflow['completed_at'] = datetime.now()
            self.logger.info(f"Cancelled workflow: {workflow['name']}")
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get workflow execution metrics"""
        total_workflows = len(self.active_workflows)
        status_counts = {}
        total_execution_time = 0
        
        for workflow in self.active_workflows.values():
            status = workflow['status'].value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if workflow['started_at'] and workflow['completed_at']:
                total_execution_time += (workflow['completed_at'] - workflow['started_at']).total_seconds()
        
        return {
            'total_workflows': total_workflows,
            'status_distribution': status_counts,
            'total_templates': len(self.workflow_templates),
            'active_triggers': len([t for t in self.triggers.values() if t['active']]),
            'average_execution_time': total_execution_time / max(1, sum(status_counts.get(s, 0) for s in ['completed', 'failed'])),
        }
    
    def cleanup_completed_workflows(self, older_than_days: int = 7):
        """Clean up old completed workflows"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        to_remove = []
        for workflow_id, workflow in self.active_workflows.items():
            if (workflow['status'] in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                workflow.get('completed_at', datetime.now()) < cutoff_date):
                to_remove.append(workflow_id)
        
        for workflow_id in to_remove:
            del self.active_workflows[workflow_id]
        
        self.logger.info(f"Cleaned up {len(to_remove)} old workflows")
        return len(to_remove)