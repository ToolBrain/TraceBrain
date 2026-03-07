"""Trace ID context helpers for async/thread-safe usage."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

_TRACE_ID: ContextVar[Optional[str]] = ContextVar("tracebrain_trace_id", default=None)


def get_trace_id() -> Optional[str]:
    return _TRACE_ID.get()


def set_trace_id(trace_id: str):
    return _TRACE_ID.set(trace_id)


def reset_trace_id(token) -> None:
    _TRACE_ID.reset(token)
