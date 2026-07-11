from typing import Tuple, List, Dict
from app.modules.relationship.constants import LifecycleState

# State machine map: current_state -> list of allowed next states
_LIFECYCLE_TRANSITIONS: Dict[str, List[str]] = {
    LifecycleState.PROPOSED.value: [LifecycleState.PENDING_APPROVAL.value, LifecycleState.ACTIVE.value, LifecycleState.REVOKED.value],
    LifecycleState.PENDING_APPROVAL.value: [LifecycleState.ACTIVE.value, LifecycleState.REJECTED.value, LifecycleState.REVOKED.value],
    LifecycleState.ACTIVE.value: [LifecycleState.SUSPENDED.value, LifecycleState.REVOKED.value, LifecycleState.EXPIRED.value],
    LifecycleState.SUSPENDED.value: [LifecycleState.ACTIVE.value, LifecycleState.REVOKED.value],
    LifecycleState.REVOKED.value: [LifecycleState.ARCHIVED.value],
    LifecycleState.EXPIRED.value: [LifecycleState.ARCHIVED.value],
    LifecycleState.ARCHIVED.value: [],
    LifecycleState.REJECTED.value: [LifecycleState.ARCHIVED.value]
}

def validate_transition(current_state: str, requested_state: str) -> Tuple[bool, str]:
    if current_state not in _LIFECYCLE_TRANSITIONS:
        return False, f"Invalid current state: {current_state}"
        
    allowed_transitions = _LIFECYCLE_TRANSITIONS[current_state]
    if requested_state not in allowed_transitions:
        return False, f"Cannot transition from {current_state} to {requested_state}. Allowed: {allowed_transitions}"
        
    return True, "Valid transition"
