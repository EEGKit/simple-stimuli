from ._base import BaseTrigger
from .utils._docs import copy_doc
from .utils.logs import _use_log_level, logger


class MockTrigger(BaseTrigger):
    """Mock trigger class.

    Delivered triggers are logged at the 'INFO' level.
    """

    def __init__(self):
        pass

    @copy_doc(BaseTrigger.signal)
    def signal(self, value: int) -> None:
        value = super().signal(value)
        with _use_log_level("INFO"):
            logger.info("Mock set to %i.", value)
