# -*- coding: utf-8 -*-
from .memory_bridge import (
    MemoryBridge,
    ContextSection,
    # Sync versions
    create_stage1_context,
    create_stage2a_context,
    create_stage2b_context,
    create_stage3_context,
    create_stage4_context,
    create_watcher_audit_context,
    # Async versions (use aiofiles for non-blocking I/O)
    create_stage1_context_async,
    create_stage2a_context_async,
    create_stage2b_context_async,
    create_stage3_context_async,
    create_stage4_context_async,
    create_watcher_audit_context_async,
)

__all__ = [
    "MemoryBridge",
    "ContextSection",
    # Sync versions
    "create_stage1_context",
    "create_stage2a_context",
    "create_stage2b_context",
    "create_stage3_context",
    "create_stage4_context",
    "create_watcher_audit_context",
    # Async versions
    "create_stage1_context_async",
    "create_stage2a_context_async",
    "create_stage2b_context_async",
    "create_stage3_context_async",
    "create_stage4_context_async",
    "create_watcher_audit_context_async",
]

