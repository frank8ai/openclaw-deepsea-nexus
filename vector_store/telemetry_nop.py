"""Chroma product telemetry no-op implementation.

Chroma 0.5.x defaults to posthog-based telemetry which pulls in `posthog`.
On Python 3.8 that dependency can crash at import-time due to newer typing
syntax (e.g. dict[str, ...]).

We provide a minimal ProductTelemetryClient that does nothing.
"""

from __future__ import annotations

from chromadb.telemetry.product import ProductTelemetryClient, ProductTelemetryEvent
from overrides import override


class NopProductTelemetryClient(ProductTelemetryClient):
    @override
    def capture(self, event: ProductTelemetryEvent) -> None:
        return
