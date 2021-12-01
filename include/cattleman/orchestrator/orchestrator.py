import signal
import time

from cattleman.types import KnowledgeBase


class Orchestrator:

    def __init__(self, min_frequency: float = 10.0):
        self._min_frequency: float = min_frequency
        self._current_frequency: float = min_frequency
        self._is_shutdown: bool = False
        # register CTRL-C handler
        signal.signal(signal.SIGINT, self.shutdown)

    @property
    def is_shutdown(self) -> bool:
        return self._is_shutdown

    def shutdown(self, _, __):
        self._is_shutdown = True

    def run(self):
        while not self._is_shutdown:
            pass
            # ---
            time.sleep(1.0 / self._current_frequency)
        # gracefully terminate resources
        KnowledgeBase.shutdown()
