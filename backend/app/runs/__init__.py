"""Run engine + bus.

Today this is in-process pub/sub backed by ``asyncio.Queue`` — enough
for single-replica deployments and the desktop/mobile sidecar shells.

When the Helm chart scales to N replicas (Batch 32), the bus swaps to
a Redis stream behind the same interface — callers don't need to
change.
"""
