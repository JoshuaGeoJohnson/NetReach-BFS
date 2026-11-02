"""
visualization.py
----------------
Canvas-based graph rendering engine.

Draws communication stations (circular nodes) and connections (edges).
Colors nodes according to their current BFS state:

    Gray   (#7f8c8d) – Unvisited station
    Green  (#27ae60) – Source station
    Yellow (#f39c12) – Currently processing (dequeued)
    Blue   (#2980b9) – Visited station
    Red    (#c0392b) – Failed station

Also draws BFS level labels beside each node.
Supports dynamic layout computation (circular or spring-like).
"""

import tkinter as tk
import math
from typing import Optional


# ── Color constants ──────────────────────────────────────────────────
COLOR_UNVISITED    = "#7f8c8d"   # gray
COLOR_SOURCE       = "#27ae60"   # green
COLOR_CURRENT      = "#f39c12"   # yellow/amber
COLOR_VISITED      = "#2980b9"   # blue
COLOR_FAILED       = "#c0392b"   # red
COLOR_ENQUEUED     = "#8e44ad"   # purple (in queue but not yet dequeued)
COLOR_EXAMINING    = "#e67e22"   # orange (neighbor being examined)

COLOR_EDGE         = "#bdc3c7"   # light gray
COLOR_EDGE_ACTIVE  = "#3498db"   # blue for edges to visited nodes
COLOR_EDGE_FAILED  = "#e74c3c"   # red for edges to/from failed

COLOR_BG           = "#1a1a2e"   # canvas background (dark navy)
COLOR_TEXT_LIGHT   = "#ecf0f1"   # node label text
COLOR_LEVEL_LABEL  = "#f1c40f"   # BFS level text

NODE_RADIUS        = 28
EDGE_WIDTH         = 2
ACTIVE_EDGE_WIDTH  = 3


class GraphCanvas(tk.Canvas):
    """
    A Tkinter Canvas subclass responsible for all graph rendering.

    The GUI creates one instance and calls:
        canvas.draw_graph(graph_manager, bfs_state)
    after every BFS step or network change.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=COLOR_BG,
            highlightthickness=0,
            **kwargs,
        )
        self._positions: dict[str, tuple[float, float]] = {}
        self._dragging: Optional[str] = None
        self._drag_offset = (0, 0)

        # Enable node dragging
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", self._on_resize)

        self._graph = None
        self._state = None
        self._on_resize_cb = None  # optional external resize callback

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def draw_graph(self, graph_manager, bfs_state=None):
        """Full redraw. Call after every state change."""
        self._graph = graph_manager
        self._state = bfs_state
        self._ensure_positions()
        self._render()

    def reset_layout(self):
        """Force recompute of all node positions."""
        self._positions = {}
        if self._graph:
            self._render()

    # ------------------------------------------------------------------
    # Layout computation
    # ------------------------------------------------------------------

    def _ensure_positions(self):
        """Assign positions to any new nodes using a circular layout."""
        if not self._graph:
            return

        nodes = self._graph.get_nodes()
        existing = set(self._positions.keys())

        # Remove positions of deleted nodes
        for n in list(self._positions):
            if n not in nodes:
                del self._positions[n]

        new_nodes = [n for n in nodes if n not in existing]
        if not new_nodes:
            return

        w = self.winfo_width() or 600
        h = self.winfo_height() or 500
        cx, cy = w / 2, h / 2

        all_nodes = self._graph.get_nodes()
        n_total = len(all_nodes)
        radius = min(w, h) * 0.35

        for i, node in enumerate(all_nodes):
            if node not in self._positions:
                angle = (2 * math.pi * i / max(n_total, 1)) - math.pi / 2
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                self._positions[node] = (x, y)

    def _recompute_layout(self):
        """Recompute all positions from scratch (circular layout)."""
        if not self._graph:
            return
        self._positions = {}
        self._ensure_positions()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self):
        self.delete("all")
        if not self._graph:
            self._draw_empty_message()
            return

        nodes = self._graph.get_nodes()
        if not nodes:
            self._draw_empty_message()
            return

        self._draw_edges()
        self._draw_nodes()
        self._draw_legend()

    def _draw_empty_message(self):
        w = self.winfo_width() or 600
        h = self.winfo_height() or 500
        self.create_text(
            w / 2, h / 2,
            text="No stations in network.\nAdd stations using the left panel.",
            fill="#555577",
            font=("Segoe UI", 14),
            justify="center",
        )

    def _get_node_color(self, node: str) -> str:
        """Determine fill color based on BFS state."""
        if self._graph.is_failed(node):
            return COLOR_FAILED

        if self._state is None:
            return COLOR_UNVISITED

        state = self._state

        if node == state.current and state.phase == "dequeue":
            return COLOR_CURRENT

        if node == state.examining and state.phase == "enqueue":
            return COLOR_ENQUEUED

        if node == state.examining and state.phase == "examine":
            return COLOR_EXAMINING

        if node in state.visited:
            src = state.levels.get(node)
            if src == 0:
                return COLOR_SOURCE
            return COLOR_VISITED

        if node in state.queue:
            return COLOR_ENQUEUED

        return COLOR_UNVISITED

    def _draw_edges(self):
        """Draw all edges before nodes so nodes render on top."""
        for u, v in self._graph.get_edges():
            if u not in self._positions or v not in self._positions:
                continue
            x1, y1 = self._positions[u]
            x2, y2 = self._positions[v]

            u_failed = self._graph.is_failed(u)
            v_failed = self._graph.is_failed(v)

            if u_failed or v_failed:
                color = COLOR_EDGE_FAILED
                width = EDGE_WIDTH
                dash = (4, 4)
            elif (self._state and
                  u in self._state.visited and
                  v in self._state.visited):
                color = COLOR_EDGE_ACTIVE
                width = ACTIVE_EDGE_WIDTH
                dash = ()
            else:
                color = COLOR_EDGE
                width = EDGE_WIDTH
                dash = ()

            self.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=width,
                dash=dash,
                smooth=True,
            )

    def _draw_nodes(self):
        """Draw each node circle with label and BFS level."""
        for node in self._graph.get_nodes():
            if node not in self._positions:
                continue

            x, y = self._positions[node]
            fill = self._get_node_color(node)

            # Outer glow ring for current/source
            if self._state and node == self._state.current and self._state.phase == "dequeue":
                self.create_oval(
                    x - NODE_RADIUS - 6, y - NODE_RADIUS - 6,
                    x + NODE_RADIUS + 6, y + NODE_RADIUS + 6,
                    fill="", outline="#f39c12", width=3,
                )
            elif self._state and self._state.levels.get(node) == 0:
                self.create_oval(
                    x - NODE_RADIUS - 6, y - NODE_RADIUS - 6,
                    x + NODE_RADIUS + 6, y + NODE_RADIUS + 6,
                    fill="", outline="#2ecc71", width=3,
                )

            # Node circle
            self.create_oval(
                x - NODE_RADIUS, y - NODE_RADIUS,
                x + NODE_RADIUS, y + NODE_RADIUS,
                fill=fill,
                outline="#ecf0f1",
                width=2,
            )

            # Station name
            self.create_text(
                x, y,
                text=node,
                fill=COLOR_TEXT_LIGHT,
                font=("Segoe UI", 11, "bold"),
            )

            # BFS level label
            if self._state and node in self._state.levels:
                level = self._state.levels[node]
                self.create_text(
                    x + NODE_RADIUS + 14, y - NODE_RADIUS + 6,
                    text=f"L{level}",
                    fill=COLOR_LEVEL_LABEL,
                    font=("Segoe UI", 8, "bold"),
                )

            # Failed marker
            if self._graph.is_failed(node):
                self.create_text(
                    x, y + NODE_RADIUS + 12,
                    text="✖ FAILED",
                    fill=COLOR_FAILED,
                    font=("Segoe UI", 7, "bold"),
                )

    def _draw_legend(self):
        """Draw color legend at bottom-left of canvas."""
        legend_items = [
            (COLOR_UNVISITED, "Unvisited"),
            (COLOR_SOURCE,    "Source"),
            (COLOR_CURRENT,   "Processing"),
            (COLOR_VISITED,   "Visited"),
            (COLOR_ENQUEUED,  "In Queue"),
            (COLOR_FAILED,    "Failed"),
        ]
        x0, y0 = 12, 12
        box_size = 12
        spacing = 22

        self.create_rectangle(
            x0 - 6, y0 - 6,
            x0 + 110, y0 + spacing * len(legend_items) + 2,
            fill="#16213e", outline="#334", width=1,
        )

        for i, (color, label) in enumerate(legend_items):
            y = y0 + i * spacing
            self.create_rectangle(x0, y, x0 + box_size, y + box_size, fill=color, outline="")
            self.create_text(
                x0 + box_size + 6, y + box_size // 2,
                text=label,
                fill="#aab",
                font=("Segoe UI", 8),
                anchor="w",
            )

    # ------------------------------------------------------------------
    # Drag interaction
    # ------------------------------------------------------------------

    def _on_press(self, event):
        node = self._node_at(event.x, event.y)
        if node:
            self._dragging = node
            px, py = self._positions[node]
            self._drag_offset = (px - event.x, py - event.y)

    def _on_drag(self, event):
        if self._dragging:
            ox, oy = self._drag_offset
            self._positions[self._dragging] = (event.x + ox, event.y + oy)
            self._render()

    def _on_release(self, event):
        self._dragging = None

    def _node_at(self, x: float, y: float) -> Optional[str]:
        """Return node name if (x,y) is within its radius."""
        for node, (nx, ny) in self._positions.items():
            if math.hypot(x - nx, y - ny) <= NODE_RADIUS + 4:
                return node
        return None

    def _on_resize(self, event):
        self._recompute_layout()
        self._render()
