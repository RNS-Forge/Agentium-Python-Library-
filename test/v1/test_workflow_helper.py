import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.workflow_helper import WorkflowHelper, Task

def step_one(**kwargs):
    return "Data ingested"

def step_two(**kwargs):
    return "Data processed successfully"

def test_workflow():
    print("=== Testing WorkflowHelper ===")
    helper = WorkflowHelper()
    
    # Define tasks with dependency
    t1 = Task(id="task_1", name="Ingest", function=step_one)
    t2 = Task(id="task_2", name="Process", function=step_two, dependencies=["task_1"])
    
    workflow_id = helper.create_workflow("Test ETL Workflow", [t1, t2])
    print(f"Created Workflow ID: {workflow_id}")
    
    # Run async workflow
    res = asyncio.run(helper.execute_workflow(workflow_id))
    print("Workflow Execution Result:", res)
    assert res.get("status") == "completed", "Workflow did not complete successfully"
    assert res.get("tasks_completed") == 2, "Not all tasks completed"
    
    print("Result: PASS\n")

if __name__ == "__main__":
    test_workflow()
