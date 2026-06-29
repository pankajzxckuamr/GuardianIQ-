class WorkflowRunStateError(Exception):
    def __init__(self, from_status: str, to_status: str, message: str = None):
        self.from_status = from_status
        self.to_status = to_status
        self.message = message or f"Invalid transition from {from_status} to {to_status}"
        super().__init__(self.message)

class WorkflowStateMachine:
    VALID_TRANSITIONS = {
        "QUEUED": ["RUNNING", "SKIPPED", "CANCELLED"],
        "RUNNING": ["COMPLETED", "FAILED", "CANCELLED"],
        "RETRY_QUEUED": ["RUNNING", "CANCELLED"],
        "FAILED": ["RETRY_QUEUED"],
        "COMPLETED": [],
        "SKIPPED": [],
        "CANCELLED": []
    }

    @classmethod
    def validate_transition(cls, from_status: str, to_status: str):
        from_status_str = from_status.value if hasattr(from_status, "value") else str(from_status)
        to_status_str = to_status.value if hasattr(to_status, "value") else str(to_status)

        allowed = cls.VALID_TRANSITIONS.get(from_status_str, [])
        if to_status_str not in allowed:
            raise WorkflowRunStateError(from_status_str, to_status_str)
