from datetime import datetime, timedelta, timezone
from typing import Dict, Any


def calculate_sm2(
    interval: int, ease_factor: float, repetitions: int, score: int
) -> Dict[str, Any]:
    """
    SuperMemo-2 (SM-2) Spaced Repetition Algorithm.

    Score mapping from frontend 1-4 scale to SM-2 0-5 quality scale:
    - 1 -> 0 (Blackout)
    - 2 -> 2 (Hard)
    - 3 -> 4 (Good)
    - 4 -> 5 (Easy)
    """
    # Map score to quality
    if score == 1:
        quality = 0
    elif score == 2:
        quality = 2
    elif score == 3:
        quality = 4
    elif score == 4:
        quality = 5
    else:
        quality = max(0, min(5, score))

    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(round(interval * ease_factor))
        repetitions += 1
    else:
        repetitions = 0
        interval = 1

    # Update ease factor formula
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ease_factor < 1.3:
        ease_factor = 1.3

    next_review_date = datetime.now(timezone.utc) + timedelta(days=interval)

    return {
        "interval": interval,
        "ease_factor": ease_factor,
        "repetitions": repetitions,
        "next_review_date": next_review_date,
    }
