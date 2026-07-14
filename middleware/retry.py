import random

def calculate_backoff(attempt: int) -> float:
    """Calculate exponential backoff with jitter."""
    return 2 ** attempt + random.uniform(0, 1)