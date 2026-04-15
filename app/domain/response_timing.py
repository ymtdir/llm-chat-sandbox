"""Response timing calculation logic."""

import random
from datetime import datetime, timedelta


class ResponseTimingCalculator:
    """Calculate response timing based on character configuration."""

    @staticmethod
    def calculate_response_delay(
        character_config: dict,
        current_time: datetime | None = None,
    ) -> timedelta:
        """Calculate delay time for AI response.

        Args:
            character_config: Character configuration containing response_patterns
            current_time: Current datetime (defaults to now)

        Returns:
            Delay timedelta before sending response

        """
        if current_time is None:
            current_time = datetime.now()

        response_patterns = character_config.get("response_patterns", {})

        # 1. Get base delay
        base_delay_config = response_patterns.get(
            "base_delay_minutes", {"min": 5, "max": 15}
        )
        min_delay = base_delay_config.get("min", 5)
        max_delay = base_delay_config.get("max", 15)
        base_delay_minutes = random.uniform(min_delay, max_delay)

        # 2. Apply time of day modifiers
        current_hour = current_time.hour
        time_modifiers = response_patterns.get("time_of_day_modifiers", [])

        multiplier = 1.0
        for modifier in time_modifiers:
            hours = modifier.get("hours", [])
            if current_hour in hours:
                multiplier = modifier.get("multiplier", 1.0)
                break

        delay_minutes = base_delay_minutes * multiplier

        # 3. Add randomness
        randomness_factor = response_patterns.get("randomness_factor", 0.2)
        random_adjustment = random.uniform(-randomness_factor, randomness_factor)
        delay_minutes *= 1 + random_adjustment

        # 4. Check reply probability (for "read but don't reply" behavior)
        reply_probability = response_patterns.get("reply_probability", 1.0)
        if random.random() > reply_probability:
            # Skip this time - add very long delay (effectively "no reply")
            delay_minutes += 60 * 24  # Add 1 day

        # Ensure minimum delay of 1 minute
        delay_minutes = max(delay_minutes, 1)

        return timedelta(minutes=delay_minutes)
