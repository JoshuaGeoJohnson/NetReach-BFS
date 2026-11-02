"""
bfs_algorithm.py
----------------
Pure BFS implementation decoupled from any GUI code.

The BFS algorithm explores a graph level by level using a queue (collections.deque).

Time Complexity : O(V + E)  where V = vertices (stations), E = edges (connections)
Space Complexity: O(V)      for the visited set and queue

Each call to step() performs exactly ONE logical BFS operation so the GUI
can animate the traversal one step at a time.
"""

from collections import deque
from typing import Optional


# ------------------------------------------------------------------
# State snapshot returned by step()
# ------------------------------------------------------------------

class BFSState:
    """
    Immutable snapshot of BFS state after one step.
    The GUI reads this to update all panels.
    """

    def __init__(
        self,
        phase: str,                    # "init" | "dequeue" | "examine" | "enqueue" | "done"
        current: Optional[str],        # station currently being processed
        examining: Optional[str],      # neighbor currently being examined (examine phase)
        queue: list[str],              # current queue contents (front → back)
        visited: list[str],            # visited stations in discovery order
        levels: dict[str, int],        # station → BFS level
        traversal_order: list[str],    # stations dequeued so far (traversal order)
        log_entry: str,                # human-readable log line for this step
        step_number: int,              # global step counter
        done: bool,                    # True when BFS is complete
    ):
        self.phase = phase
        self.current = current
        self.examining = examining
        self.queue = list(queue)
        self.visited = list(visited)
        self.levels = dict(levels)
        self.traversal_order = list(traversal_order)
        self.log_entry = log_entry
        self.step_number = step_number
        self.done = done


# ------------------------------------------------------------------
# BFS Engine
# ------------------------------------------------------------------

class BFSAlgorithm:
    """
    Step-by-step BFS engine.

    Usage:
        engine = BFSAlgorithm(graph_manager)
        engine.initialize(source="A")

        while not engine.is_done():
            state = engine.step()
            # update GUI with state
    """

    def __init__(self, graph_manager):
        """
        Args:
            graph_manager: A GraphManager instance providing
                           get_active_neighbors() and is_failed()
        """
        self._graph = graph_manager
        self._reset_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize(self, source: str) -> tuple[bool, str, Optional[BFSState]]:
        """
        Seed BFS with the given source station.

        Returns (success, message, initial_state).
        Fails if source does not exist or is failed.
        """
        self._reset_state()

        if source not in self._graph.get_nodes():
            return False, f"Station '{source}' does not exist.", None
        if self._graph.is_failed(source):
            return False, f"Source station '{source}' is FAILED. Cannot start BFS.", None

        self._source = source
        self._queue.append(source)
        self._visited.add(source)
        self._visited_order.append(source)
        self._levels[source] = 0
        self._initialized = True
        self._step_number = 0

        state = self._make_state(
            phase="init",
            current=source,
            examining=None,
            log_entry=f"Step {self._step_number}: BFS initialized. Source station '{source}' "
                      f"added to queue. Level 0.",
        )
        return True, "BFS initialized successfully.", state

    def step(self) -> Optional[BFSState]:
        """
        Perform exactly ONE BFS operation.

        The sub-steps cycle through:
          1. dequeue  – pop front of queue, set current station
          2. examine  – examine each neighbor one at a time
          3. (repeat) – dequeue next station
          done        – queue empty

        Returns BFSState or None if BFS not initialized / already done.
        """
        if not self._initialized or self._done:
            return None

        self._step_number += 1

        # ── Phase: currently examining neighbors of self._current ──
        if self._current is not None and self._neighbor_iter:
            neighbor = self._neighbor_iter.pop(0)
            return self._examine_neighbor(neighbor)

        # ── Phase: dequeue next station ──
        if not self._queue:
            # BFS complete
            self._done = True
            self._current = None
            log = (
                f"Step {self._step_number}: Queue is empty. BFS complete!\n"
                f"  Traversal order: {' → '.join(self._traversal_order)}"
            )
            return self._make_state(phase="done", current=None, examining=None, log_entry=log)

        self._current = self._queue.popleft()
        self._traversal_order.append(self._current)
        neighbors = self._graph.get_active_neighbors(self._current)
        self._neighbor_iter = neighbors  # list to consume one by one

        level = self._levels.get(self._current, "?")
        log = (
            f"Step {self._step_number}: Dequeued station '{self._current}' "
            f"(Level {level}). Examining neighbors: {neighbors if neighbors else 'none'}."
        )
        return self._make_state(phase="dequeue", current=self._current, examining=None, log_entry=log)

    def is_done(self) -> bool:
        return self._done

    def is_initialized(self) -> bool:
        return self._initialized

    def get_reachability(self) -> dict:
        """
        Calculate reachability statistics after (or during) BFS.

        Returns dict with:
            reachable         – list of reachable stations (including source)
            unreachable       – list of active stations not yet visited
            active_total      – count of active (non-failed) stations
            failed_total      – count of failed stations
            reachability_pct  – float 0-100
        """
        active = set(self._graph.get_active_nodes())
        reachable = [n for n in self._visited_order if n in active]
        unreachable = sorted(active - set(reachable))
        active_total = len(active)
        pct = (len(reachable) / active_total * 100) if active_total > 0 else 0.0

        return {
            "reachable": reachable,
            "unreachable": unreachable,
            "active_total": active_total,
            "failed_total": len(self._graph.get_failed_nodes()),
            "reachability_pct": pct,
        }

    def get_levels_summary(self) -> dict[int, list[str]]:
        """Return {level: [stations]} mapping."""
        summary: dict[int, list[str]] = {}
        for station, lvl in self._levels.items():
            summary.setdefault(lvl, []).append(station)
        for lvl in summary:
            summary[lvl] = sorted(summary[lvl])
        return summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _reset_state(self):
        self._source: Optional[str] = None
        self._queue: deque[str] = deque()
        self._visited: set[str] = set()
        self._visited_order: list[str] = []
        self._levels: dict[str, int] = {}
        self._traversal_order: list[str] = []
        self._current: Optional[str] = None
        self._neighbor_iter: list[str] = []
        self._initialized: bool = False
        self._done: bool = False
        self._step_number: int = 0

    def _examine_neighbor(self, neighbor: str) -> BFSState:
        """Examine one neighbor: skip if visited/failed, else enqueue."""
        self._step_number  # already incremented by caller

        if neighbor in self._visited:
            log = (
                f"Step {self._step_number}: Examining neighbor '{neighbor}' "
                f"of '{self._current}' → already visited. Skip."
            )
            return self._make_state(
                phase="examine",
                current=self._current,
                examining=neighbor,
                log_entry=log,
            )

        if self._graph.is_failed(neighbor):
            log = (
                f"Step {self._step_number}: Examining neighbor '{neighbor}' "
                f"of '{self._current}' → FAILED station. Skip."
            )
            return self._make_state(
                phase="examine",
                current=self._current,
                examining=neighbor,
                log_entry=log,
            )

        # Newly discovered – enqueue
        self._queue.append(neighbor)
        self._visited.add(neighbor)
        self._visited_order.append(neighbor)
        self._levels[neighbor] = self._levels[self._current] + 1

        log = (
            f"Step {self._step_number}: Discovered '{neighbor}' "
            f"via '{self._current}'. Level {self._levels[neighbor]}. "
            f"Enqueued '{neighbor}'."
        )
        return self._make_state(
            phase="enqueue",
            current=self._current,
            examining=neighbor,
            log_entry=log,
        )

    def _make_state(self, phase: str, current, examining, log_entry: str) -> BFSState:
        return BFSState(
            phase=phase,
            current=current,
            examining=examining,
            queue=list(self._queue),
            visited=list(self._visited_order),
            levels=self._levels,
            traversal_order=self._traversal_order,
            log_entry=log_entry,
            step_number=self._step_number,
            done=self._done,
        )
