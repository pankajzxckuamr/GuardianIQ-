from enum import Enum


class SourceType(str, Enum):
    POSTGRES = "POSTGRES"

    MYSQL = "MYSQL"

    API = "API"

    S3 = "S3"

    EXTERNAL_API = "EXTERNAL_API"
