from __future__ import annotations

import pytest

from stimuli.trigger import MockTrigger


def test_trigger_mock(caplog: pytest.LogCaptureFixture) -> None:
    """Testing for Mock trigger."""
    trigger = MockTrigger()
    trigger.signal(1)
    assert "Mock set to 1" in caplog.text
    caplog.clear()
    trigger.signal(2)
    assert "Mock set to 2" in caplog.text
    caplog.clear()
    trigger.signal(str(101))  # convertible to int
    assert "Mock set to 101" in caplog.text
    caplog.clear()
    with pytest.raises(TypeError, match="between 1 and 255"):
        trigger.signal(lambda x: 101)
    with pytest.raises(ValueError, match="between 1 and 255"):
        trigger.signal(256)
    assert "Mock set" not in caplog.text
