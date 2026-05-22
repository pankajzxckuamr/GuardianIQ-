from enum import Enum


class PolicyStatus(str, Enum):
    DRAFT = "DRAFT"

    ACTIVE = "ACTIVE"

    PAUSED = "PAUSED"

    RETIRED = "RETIRED"
