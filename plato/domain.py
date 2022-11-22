from enum import Enum


class StorageType(str, Enum):
    S3 = 's3'
    DISK = 'disk'
