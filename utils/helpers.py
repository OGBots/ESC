import random
import string
from config import ESCROW_ID_PREFIX, REDEEM_CODE_PREFIX

def generate_unique_id(prefix: str, length: int = 5) -> str:
    """Generate a unique ID with the given prefix"""
    chars = string.ascii_uppercase + string.digits
    random_str = ''.join(random.choices(chars, k=length))
    return f"{prefix}{random_str}"

def calculate_fee(amount: float, percentage: float) -> float:
    """Calculate fee based on percentage"""
    return (amount * percentage) / 100

def format_currency(amount: float) -> str:
    """Format currency with 2 decimal places"""
    return f"₹{amount:.2f}"

def validate_amount(amount: str) -> bool:
    """Validate if string is a valid positive number"""
    try:
        value = float(amount)
        return value > 0
    except ValueError:
        return False
