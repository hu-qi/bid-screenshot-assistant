from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from bid_screenshot_assistant.domain.models import (
    AdapterRequest,
    PlatformDescriptor,
    PlatformExecutionResult,
)


class PlatformAdapter(ABC):
    descriptor: PlatformDescriptor

    @abstractmethod
    async def execute(
        self,
        request: AdapterRequest,
        item_dir: Path,
    ) -> PlatformExecutionResult:
        """Execute one query on one platform and write evidence below item_dir."""


class AdapterRegistry:
    def __init__(self, adapters: list[PlatformAdapter]) -> None:
        self._adapters = {adapter.descriptor.platform_id: adapter for adapter in adapters}

    def get(self, platform_id):
        try:
            return self._adapters[platform_id]
        except KeyError as exc:
            raise KeyError(f"No adapter registered for {platform_id}") from exc

    def descriptors(self) -> list[PlatformDescriptor]:
        return [adapter.descriptor for adapter in self._adapters.values()]
