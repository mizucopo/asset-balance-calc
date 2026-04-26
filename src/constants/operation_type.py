"""操作タイプのEnum"""

from enum import Enum


class OperationType(Enum):
    """操作タイプ"""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    NONE = "none"
