from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepResult(BaseModel):
    step_id: str = Field(..., description="Unique step identifier")
    step_name: str = Field(..., description="Step name")
    action: Optional[str] = Field(default=None, description="Action executed by this step")
    status: str = Field(..., description="Execution status: success, failed, skipped")
    start_time: datetime = Field(..., description="Timestamp when step started")
    end_time: datetime = Field(..., description="Timestamp when step finished")
    duration_seconds: float = Field(..., description="Execution duration in seconds")
    output: Optional[Any] = Field(default=None, description="Output payload returned by the action")
    error_message: Optional[str] = Field(default=None, description="Error message if step failed")
    error_type: Optional[str] = Field(default=None, description="Error classification: Technical or Business")


class ExecutionMetrics(BaseModel):
    total_steps: int = Field(default=0, description="Total number of steps evaluated")
    successful_steps: int = Field(default=0, description="Number of successfully executed steps")
    failed_steps: int = Field(default=0, description="Number of failed steps")
    skipped_steps: int = Field(default=0, description="Number of skipped steps")
    total_duration_seconds: float = Field(default=0.0, description="Total flow run duration in seconds")
    hours_saved: float = Field(default=0.0, description="Estimated manual labour hours saved")
    cost_saved: float = Field(default=0.0, description="Estimated operational cost saved")


class FailureDetails(BaseModel):
    failed_step_id: str = Field(..., description="ID of the step that triggered the failure")
    failed_step_name: str = Field(..., description="Human-readable name of the failed step")
    action: str = Field(..., description="Action that failed (e.g. web.click, excel.read)")
    error_type: str = Field(default="Technical", description="Classification: Technical or Business exception")
    exception_class: str = Field(..., description="Python exception class name (e.g. FileNotFoundError, TimeoutError)")
    error_message: str = Field(..., description="Original error message")
    root_cause: str = Field(..., description="Direct summary of the root cause for AI and human diagnosis")
    suggested_fix: str = Field(..., description="Actionable recommendation to resolve the failure")
    error_screenshot_path: Optional[str] = Field(default=None, description="Path to screenshot captured at moment of failure if browser was active")


class ExecutionContext(BaseModel):
    flow_name: str = Field(..., description="Name of the executed workflow")
    start_time: datetime = Field(default_factory=datetime.now, description="Workflow start timestamp")
    variables: Dict[str, Any] = Field(default_factory=dict, description="In-memory variables captured during execution")
    step_results: List[StepResult] = Field(default_factory=list, description="Detailed per-step execution log")
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics, description="Aggregated run metrics and telemetry")
    is_completed: bool = Field(default=False, description="Whether the workflow completed all steps successfully")
    has_error: bool = Field(default=False, description="Whether an unhandled error occurred during execution")
    failure_details: Optional[FailureDetails] = Field(default=None, description="Structured root-cause diagnosis if has_error is true")

    def set_variable(self, name: str, value: Any) -> None:
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        return self.variables.get(name, default)
