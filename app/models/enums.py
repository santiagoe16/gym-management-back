
from enum import Enum


class PaymentType(str, Enum):
    CASH = "cash"
    TRANSFER = "transfer"

class PlanRole(str, Enum):
    REGULAR = "regular"
    TAQUILLERO = "taquillero"

class UserRole(str, Enum):
    ADMIN = "admin"
    TRAINER = "trainer"
    USER = "user"
