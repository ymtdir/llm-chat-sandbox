"""Tests for response timing calculator."""

from datetime import datetime, timedelta

from app.domain.response_timing import ResponseTimingCalculator


def test_calculate_response_delay_with_defaults():
    """Test response delay calculation with default configuration."""
    character_config = {
        "response_patterns": {
            "base_delay_minutes": {"min": 5, "max": 15},
            "randomness_factor": 0.2,
            "reply_probability": 1.0,  # Always reply
        }
    }

    delay = ResponseTimingCalculator.calculate_response_delay(character_config)

    # Should be between (5 * 0.8) and (15 * 1.2) minutes
    assert isinstance(delay, timedelta)
    assert delay >= timedelta(minutes=1)  # Minimum is 1 minute
    assert delay <= timedelta(minutes=20)  # Max with randomness


def test_calculate_response_delay_time_of_day_modifier():
    """Test that time of day modifiers affect delay."""
    character_config = {
        "response_patterns": {
            "base_delay_minutes": {"min": 10, "max": 10},  # Fixed base
            "randomness_factor": 0.0,  # No randomness
            "reply_probability": 1.0,
            "time_of_day_modifiers": [
                {"hours": [9, 10, 11, 12, 13, 14, 15, 16, 17], "multiplier": 2.0},  # Work hours
                {"hours": [0, 1, 2, 3, 4, 5], "multiplier": 5.0},  # Sleep hours
            ],
        }
    }

    # Test during work hours (multiplier 2.0)
    work_time = datetime(2024, 1, 1, 14, 0, 0)  # 2 PM
    delay = ResponseTimingCalculator.calculate_response_delay(character_config, work_time)
    assert delay == timedelta(minutes=20)  # 10 * 2.0

    # Test during sleep hours (multiplier 5.0)
    sleep_time = datetime(2024, 1, 1, 2, 0, 0)  # 2 AM
    delay = ResponseTimingCalculator.calculate_response_delay(character_config, sleep_time)
    assert delay == timedelta(minutes=50)  # 10 * 5.0

    # Test during normal hours (no modifier, multiplier 1.0)
    normal_time = datetime(2024, 1, 1, 20, 0, 0)  # 8 PM
    delay = ResponseTimingCalculator.calculate_response_delay(character_config, normal_time)
    assert delay == timedelta(minutes=10)  # 10 * 1.0


def test_calculate_response_delay_randomness():
    """Test that randomness factor creates variation."""
    character_config = {
        "response_patterns": {
            "base_delay_minutes": {"min": 10, "max": 10},
            "randomness_factor": 0.3,  # ±30%
            "reply_probability": 1.0,
        }
    }

    # Run multiple times to ensure variation
    delays = []
    for _ in range(10):
        delay = ResponseTimingCalculator.calculate_response_delay(character_config)
        delays.append(delay.total_seconds() / 60)  # Convert to minutes

    # Should have variation due to randomness
    # With 30% randomness, expect range of [7, 13] minutes (10 * 0.7 to 10 * 1.3)
    assert min(delays) >= 7
    assert max(delays) <= 13
    # Should not all be the same
    assert len(set(delays)) > 1


def test_calculate_response_delay_minimum_enforced():
    """Test that minimum delay of 1 minute is enforced."""
    character_config = {
        "response_patterns": {
            "base_delay_minutes": {"min": 0.1, "max": 0.1},  # Very small
            "randomness_factor": 0.0,
            "reply_probability": 1.0,
        }
    }

    delay = ResponseTimingCalculator.calculate_response_delay(character_config)
    assert delay >= timedelta(minutes=1)


def test_calculate_response_delay_no_reply_probability():
    """Test that low reply probability adds significant delay."""
    character_config = {
        "response_patterns": {
            "base_delay_minutes": {"min": 5, "max": 5},
            "randomness_factor": 0.0,
            "reply_probability": 0.0,  # Never reply immediately
        }
    }

    # With 0% reply probability, should add 1 day
    delay = ResponseTimingCalculator.calculate_response_delay(character_config)
    # Should be approximately 1 day + 5 minutes
    assert delay >= timedelta(days=1)


def test_calculate_response_delay_missing_config():
    """Test that missing config values use defaults."""
    # Empty config
    character_config = {}

    delay = ResponseTimingCalculator.calculate_response_delay(character_config)

    # Should use defaults and not crash
    assert isinstance(delay, timedelta)
    assert delay >= timedelta(minutes=1)


def test_calculate_response_delay_partial_config():
    """Test with partial configuration."""
    character_config = {
        "response_patterns": {
            "base_delay_minutes": {"min": 3, "max": 7},
            # Missing other fields - should use defaults
        }
    }

    delay = ResponseTimingCalculator.calculate_response_delay(character_config)

    # Should work with defaults for missing fields
    assert isinstance(delay, timedelta)
    assert delay >= timedelta(minutes=1)


def test_calculate_response_delay_different_current_times():
    """Test that different current times produce different results for time-based modifiers."""
    character_config = {
        "response_patterns": {
            "base_delay_minutes": {"min": 10, "max": 10},
            "randomness_factor": 0.0,
            "reply_probability": 1.0,
            "time_of_day_modifiers": [
                {"hours": [12], "multiplier": 3.0},  # Only noon
            ],
        }
    }

    # Noon - should apply multiplier
    noon = datetime(2024, 1, 1, 12, 30, 0)
    delay_noon = ResponseTimingCalculator.calculate_response_delay(character_config, noon)
    assert delay_noon == timedelta(minutes=30)  # 10 * 3.0

    # Not noon - should not apply multiplier
    not_noon = datetime(2024, 1, 1, 13, 30, 0)
    delay_not_noon = ResponseTimingCalculator.calculate_response_delay(character_config, not_noon)
    assert delay_not_noon == timedelta(minutes=10)  # 10 * 1.0
