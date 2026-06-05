"""
Performance timing layer for GraphEngine.

Provides a dedicated layer that logs high-precision timing data for workflow
execution analysis. All log entries are prefixed with [PERF_TIMING] for easy
filtering and parsing.
"""

import logging
import time
from typing import final

from typing_extensions import override

from dify_graph.graph_events import (
    GraphEngineEvent,
    GraphRunFailedEvent,
    GraphRunPartialSucceededEvent,
    GraphRunStartedEvent,
    GraphRunSucceededEvent,
    NodeRunFailedEvent,
    NodeRunStartedEvent,
    NodeRunSucceededEvent,
)
from dify_graph.nodes.base.node import Node

from .base import GraphEngineLayer

logger = logging.getLogger("GraphEngine.PerformanceTiming")


@final
class PerformanceTimingLayer(GraphEngineLayer):
    """Layer that records per-node and per-workflow timing with [PERF_TIMING] logs."""

    def __init__(self) -> None:
        super().__init__()
        self._graph_start_time: float | None = None
        self._node_start_times: dict[str, float] = {}
        self._node_count = 0

    @override
    def on_graph_start(self) -> None:
        self._graph_start_time = time.perf_counter()
        workflow_id = self.graph_runtime_state.workflow_id
        logger.info(
            "[PERF_TIMING] event=graph_start | workflow_id=%s | timestamp=%.6f",
            workflow_id,
            self._graph_start_time,
        )

    @override
    def on_event(self, event: GraphEngineEvent) -> None:
        workflow_id = self.graph_runtime_state.workflow_id
        ts = time.perf_counter()

        if isinstance(event, GraphRunStartedEvent):
            logger.info(
                "[PERF_TIMING] event=graph_run_started | workflow_id=%s | timestamp=%.6f",
                workflow_id,
                ts,
            )

        elif isinstance(event, GraphRunSucceededEvent):
            elapsed = ts - self._graph_start_time if self._graph_start_time else 0
            logger.info(
                "[PERF_TIMING] event=graph_run_succeeded | workflow_id=%s | elapsed=%.6f | node_count=%d",
                workflow_id,
                elapsed,
                self._node_count,
            )

        elif isinstance(event, GraphRunPartialSucceededEvent):
            elapsed = ts - self._graph_start_time if self._graph_start_time else 0
            logger.info(
                "[PERF_TIMING] event=graph_run_partial_succeeded | workflow_id=%s | elapsed=%.6f | "
                "node_count=%d | exceptions=%d",
                workflow_id,
                elapsed,
                self._node_count,
                event.exceptions_count,
            )

        elif isinstance(event, GraphRunFailedEvent):
            elapsed = ts - self._graph_start_time if self._graph_start_time else 0
            logger.info(
                "[PERF_TIMING] event=graph_run_failed | workflow_id=%s | elapsed=%.6f | error=%s",
                workflow_id,
                elapsed,
                event.error,
            )

        elif isinstance(event, NodeRunStartedEvent):
            self._node_start_times[event.node_id] = ts
            logger.info(
                "[PERF_TIMING] event=node_start | workflow_id=%s | node_id=%s | node_type=%s | "
                "node_title=%s | timestamp=%.6f",
                workflow_id,
                event.node_id,
                event.node_type,
                event.node_title,
                ts,
            )

        elif isinstance(event, NodeRunSucceededEvent):
            start_ts = self._node_start_times.pop(event.node_id, None)
            elapsed = ts - start_ts if start_ts else 0
            self._node_count += 1
            logger.info(
                "[PERF_TIMING] event=node_succeeded | workflow_id=%s | node_id=%s | "
                "node_type=%s | elapsed=%.6f | timestamp=%.6f",
                workflow_id,
                event.node_id,
                event.node_type,
                elapsed,
                ts,
            )

        elif isinstance(event, NodeRunFailedEvent):
            start_ts = self._node_start_times.pop(event.node_id, None)
            elapsed = ts - start_ts if start_ts else 0
            logger.info(
                "[PERF_TIMING] event=node_failed | workflow_id=%s | node_id=%s | "
                "node_type=%s | elapsed=%.6f | error=%s",
                workflow_id,
                event.node_id,
                event.node_type,
                elapsed,
                event.error,
            )

    @override
    def on_graph_end(self, error: Exception | None) -> None:
        ts = time.perf_counter()
        workflow_id = self.graph_runtime_state.workflow_id
        total_elapsed = ts - self._graph_start_time if self._graph_start_time else 0
        logger.info(
            "[PERF_TIMING] event=graph_end | workflow_id=%s | total_elapsed=%.6f | node_count=%d | has_error=%s",
            workflow_id,
            total_elapsed,
            self._node_count,
            error is not None,
        )

    @override
    def on_node_run_start(self, node: Node) -> None:
        self._node_start_times[node.id] = time.perf_counter()

    @override
    def on_node_run_end(
        self, node: Node, error: Exception | None, result_event=None
    ) -> None:
        # Node timing is already captured in on_event via NodeRunSucceededEvent/NodeRunFailedEvent.
        # This hook acts as a fallback for cases where events might be missed.
        pass
