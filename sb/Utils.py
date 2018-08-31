
from enum import Enum,unique

@unique
class ProductCode(Enum):
    SB = 1
    GJJ = 2
    OTHER = 3


@unique
class CustomerStatusCode(Enum):
    Disabled = 0
    SB = 1
    GJJ = 2
    OTHER = 4


@unique
class CustomerOperations(Enum):
    ADD = 1
    REORDER =2
    REMOVE = 3