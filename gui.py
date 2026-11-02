"""
gui.py
------
Main application window for NetReach.

Layout:
    ┌─────────────────────────────────────────────────────────┐
    │  HEADER: NetReach title + BFS badge                     │
    ├──────────────┬──────────────────────┬───────────────────┤
    │  LEFT        │  CENTER              │  RIGHT            │
    │  Controls    │  Graph Canvas        │  BFS Info Panel   │
    │  Sidebar     │                      │                   │
    ├──────────────┴──────────────────────┴───────────────────┤
    │  BOTTOM: Algorithm Execution Log                        │
    ├─────────────────────────────────────────────────────────┤
    │  COMPLEXITY: O(V+E) explanation                         │
    └─────────────────────────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import time

from graph_manager import GraphManager
from bfs_algorithm import BFSAlgorithm
from visualization import GraphCanvas


# ── Theme colors ─────────────────────────────────────────────────────
BG_DARK    = "#0f0f23"
BG_PANEL   = "#16213e"
BG_CARD    = "#1a1a2e"
BG_HEADER  = "#0d0d1a"
ACCENT     = "#3498db"
ACCENT2    = "#2ecc71"
ACCENT3    = "#e74c3c"
GOLD       = "#f1c40f"
TEXT_MAIN  = "#ecf0f1"
TEXT_DIM   = "#95a5a6"
TEXT_WARN  = "#e74c3c"
BORDER     = "#2c3e50"

BTN_PRIMARY  = {"bg": "#2980b9", "fg": "white", "activebackground": "#3498db", "activeforeground": "white"}
BTN_SUCCESS  = {"bg": "#27ae60", "fg": "white", "activebackground": "#2ecc71", "activeforeground": "white"}
BTN_DANGER   = {"bg": "#c0392b", "fg": "white", "activebackground": "#e74c3c", "activeforeground": "white"}
BTN_WARNING  = {"bg": "#d35400", "fg": "white", "activebackground": "#e67e22", "activeforeground": "white"}
BTN_NEUTRAL  = {"bg": "#2c3e50", "fg": "#ecf0f1", "activebackground": "#34495e", "activeforeground": "white"}
BTN_GOLD     = {"bg": "#b7950b", "fg": "white", "activebackground": "#f1c40f", "activeforeground": "#1a1a2e"}

AUTO_RUN_DELAY_MS = 700  # milliseconds between auto steps


class NetReachApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("NetReach – Emergency Communication Network Analyzer")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        self.configure(bg=BG_DARK)

        # Core objects
        self.graph = GraphManager()
        self.bfs = BFSAlgorithm(self.graph)
        self._bfs_initialized = False
        self._auto_running = False
        self._auto_after_id = None
        self._last_state = None
        self._step_count = 0

        # Build UI
        self._build_header()
        self._build_main_area()
        self._build_log_panel()
        self._build_complexity_panel()

        # Load sample network
        self.graph.load_sample_network()
        self._refresh_dropdowns()
        self._refresh_canvas()
        self._refresh_info_panel(None)
        self._log("Application started. Sample network loaded (A–G).")
        self._log("Select source station and click 'Start BFS' to begin.")

    # ==================================================================
    # UI CONSTRUCTION
    # ==================================================================

    def _build_header(self):
        header = tk.Frame(self, bg=BG_HEADER, height=70)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        # Left: Logo + title
        left = tk.Frame(header, bg=BG_HEADER)
        left.pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(left, text="⚡ NetReach",
                 font=("Segoe UI", 22, "bold"),
                 fg=ACCENT, bg=BG_HEADER).pack(anchor="w")
        tk.Label(left, text="Emergency Communication Network Reachability Analyzer",
                 font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=BG_HEADER).pack(anchor="w")

        # Right: Algorithm badge
        right = tk.Frame(header, bg=BG_HEADER)
        right.pack(side=tk.RIGHT, padx=20)

        badge = tk.Frame(right, bg="#1a3a5c", padx=12, pady=6)
        badge.pack()
        tk.Label(badge, text="Algorithm: Breadth-First Search  |  BFS",
                 font=("Segoe UI", 10, "bold"),
                 fg=GOLD, bg="#1a3a5c").pack()
        tk.Label(badge, text="Time: O(V+E)   Space: O(V)",
                 font=("Segoe UI", 8),
                 fg=TEXT_DIM, bg="#1a3a5c").pack()

        # Separator line
        tk.Frame(self, bg=ACCENT, height=2).pack(fill=tk.X)

    def _build_main_area(self):
        """Three-column main area: left sidebar | canvas | right panel."""
        main = tk.Frame(self, bg=BG_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self._build_left_sidebar(main)
        self._build_right_panel(main)
        self._build_canvas_panel(main)

    # ── LEFT SIDEBAR ─────────────────────────────────────────────────

    def _build_left_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=BG_PANEL, width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1))
        sidebar.pack_propagate(False)

        canvas_scroll = tk.Canvas(sidebar, bg=BG_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(sidebar, orient="vertical", command=canvas_scroll.yview)
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(canvas_scroll, bg=BG_PANEL)
        win_id = canvas_scroll.create_window((0, 0), window=inner, anchor="nw")

        def _on_frame_configure(event):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))

        def _on_canvas_configure(event):
            canvas_scroll.itemconfig(win_id, width=event.width)

        inner.bind("<Configure>", _on_frame_configure)
        canvas_scroll.bind("<Configure>", _on_canvas_configure)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas_scroll.yview_scroll(-1 * (event.delta // 120), "units")
        canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel)

        self._build_sidebar_content(inner)

    def _build_sidebar_content(self, parent):
        pad = {"padx": 10, "pady": 4}

        def section(text):
            tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, padx=6, pady=(8, 2))
            tk.Label(parent, text=text, font=("Segoe UI", 8, "bold"),
                     fg=GOLD, bg=BG_PANEL).pack(anchor="w", **pad)

        def btn(text, cmd, style=BTN_NEUTRAL, w=18):
            b = tk.Button(parent, text=text, command=cmd, width=w,
                          relief="flat", cursor="hand2",
                          font=("Segoe UI", 9), **style)
            b.pack(**pad)
            return b

        # ── BFS Source ──
        section("▶  BFS SOURCE")
        tk.Label(parent, text="Source Station:", fg=TEXT_DIM,
                 bg=BG_PANEL, font=("Segoe UI", 9)).pack(anchor="w", padx=10)
        self._source_var = tk.StringVar(value="A")
        self._source_dropdown = ttk.Combobox(parent, textvariable=self._source_var,
                                              state="readonly", width=17,
                                              font=("Segoe UI", 9))
        self._source_dropdown.pack(padx=10, pady=2)

        # ── BFS Controls ──
        section("⚙  BFS CONTROLS")
        self._btn_start   = btn("▶  Start BFS",     self._cmd_start_bfs,   BTN_SUCCESS)
        self._btn_next    = btn("⏭  Next Step",     self._cmd_next_step,   BTN_PRIMARY)
        self._btn_auto    = btn("⚡ Auto Run",       self._cmd_auto_run,    BTN_WARNING)
        self._btn_pause   = btn("⏸  Pause",          self._cmd_pause,       BTN_NEUTRAL)
        self._btn_reset_b = btn("↺  Reset BFS",     self._cmd_reset_bfs,   BTN_NEUTRAL)

        self._btn_next["state"]  = "disabled"
        self._btn_auto["state"]  = "disabled"
        self._btn_pause["state"] = "disabled"

        # ── Station Management ──
        section("🏠  STATIONS")
        tk.Label(parent, text="Station Name:", fg=TEXT_DIM,
                 bg=BG_PANEL, font=("Segoe UI", 9)).pack(anchor="w", padx=10)
        self._station_name_var = tk.StringVar()
        tk.Entry(parent, textvariable=self._station_name_var, width=19,
                 bg=BG_CARD, fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
                 relief="flat", font=("Segoe UI", 9)).pack(padx=10, pady=2)

        btn("＋ Add Station",    self._cmd_add_station,    BTN_SUCCESS)
        btn("－ Remove Station", self._cmd_remove_station, BTN_DANGER)

        # ── Connection Management ──
        section("🔗  CONNECTIONS")
        for lbl, var_name in [("From:", "_conn_from_var"), ("To:", "_conn_to_var")]:
            tk.Label(parent, text=lbl, fg=TEXT_DIM,
                     bg=BG_PANEL, font=("Segoe UI", 9)).pack(anchor="w", padx=10)
            var = tk.StringVar()
            setattr(self, var_name, var)
            cb = ttk.Combobox(parent, textvariable=var, state="readonly",
                              width=17, font=("Segoe UI", 9))
            setattr(self, var_name.replace("_var", "_dropdown"), cb)
            cb.pack(padx=10, pady=2)

        btn("＋ Add Connection",    self._cmd_add_edge,    BTN_SUCCESS)
        btn("－ Remove Connection", self._cmd_remove_edge, BTN_DANGER)

        # ── Failure Simulation ──
        section("⚠  FAILURE SIMULATION")
        tk.Label(parent, text="Select Station:", fg=TEXT_DIM,
                 bg=BG_PANEL, font=("Segoe UI", 9)).pack(anchor="w", padx=10)
        self._fail_var = tk.StringVar()
        self._fail_dropdown = ttk.Combobox(parent, textvariable=self._fail_var,
                                            state="readonly", width=17,
                                            font=("Segoe UI", 9))
        self._fail_dropdown.pack(padx=10, pady=2)

        btn("💥 Simulate Failure",   self._cmd_fail_station,    BTN_DANGER)
        btn("✔  Restore Station",    self._cmd_restore_station, BTN_SUCCESS)

        # ── Network ──
        section("🌐  NETWORK")
        btn("↺  Reset Network",  self._cmd_reset_network, BTN_DANGER)
        btn("📋 Load Sample",    self._cmd_load_sample,   BTN_NEUTRAL)
        btn("💾 Save Network",   self._cmd_save_network,  BTN_NEUTRAL)
        btn("📂 Load Network",   self._cmd_load_network,  BTN_NEUTRAL)

        tk.Frame(parent, height=10, bg=BG_PANEL).pack()

    # ── CENTER CANVAS ─────────────────────────────────────────────────

    def _build_canvas_panel(self, parent):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Network Graph Visualization",
                 font=("Segoe UI", 10, "bold"),
                 fg=TEXT_DIM, bg=BG_DARK).pack(anchor="w", padx=10, pady=(6, 0))

        self._canvas = GraphCanvas(frame)
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    # ── RIGHT PANEL ───────────────────────────────────────────────────

    def _build_right_panel(self, parent):
        panel = tk.Frame(parent, bg=BG_PANEL, width=240)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(1, 0))
        panel.pack_propagate(False)

        tk.Label(panel, text="BFS Information",
                 font=("Segoe UI", 11, "bold"),
                 fg=ACCENT, bg=BG_PANEL).pack(pady=(10, 4))

        tk.Frame(panel, bg=BORDER, height=1).pack(fill=tk.X, padx=8)

        # Info labels
        self._info_vars = {}
        info_fields = [
            ("current",      "Current Station",   GOLD),
            ("level",        "BFS Level",         ACCENT),
            ("phase",        "Phase",             "#9b59b6"),
            ("queue",        "Queue",             ACCENT2),
            ("visited",      "Visited",           ACCENT),
            ("traversal",    "Traversal Order",   TEXT_MAIN),
            ("reachable",    "Reachable",         ACCENT2),
            ("unreachable",  "Unreachable",       TEXT_WARN),
            ("active_total", "Active Stations",   TEXT_MAIN),
            ("failed_total", "Failed Stations",   TEXT_WARN),
            ("pct",          "Reachability %",    GOLD),
        ]

        scroll_frame = tk.Frame(panel, bg=BG_PANEL)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        for key, label, color in info_fields:
            card = tk.Frame(scroll_frame, bg=BG_CARD, pady=4)
            card.pack(fill=tk.X, pady=2)

            tk.Label(card, text=label, font=("Segoe UI", 8),
                     fg=TEXT_DIM, bg=BG_CARD).pack(anchor="w", padx=8)

            var = tk.StringVar(value="—")
            self._info_vars[key] = var
            tk.Label(card, textvariable=var,
                     font=("Segoe UI", 9, "bold"),
                     fg=color, bg=BG_CARD,
                     wraplength=210, justify="left").pack(anchor="w", padx=8)

        # Reachability progress bar
        tk.Label(panel, text="Reachability", font=("Segoe UI", 8),
                 fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w", padx=10)
        self._progress = ttk.Progressbar(panel, length=200, mode="determinate",
                                          maximum=100)
        self._progress.pack(padx=10, pady=(0, 8))

        # BFS Levels summary
        tk.Frame(panel, bg=BORDER, height=1).pack(fill=tk.X, padx=8)
        tk.Label(panel, text="BFS Levels", font=("Segoe UI", 9, "bold"),
                 fg=GOLD, bg=BG_PANEL).pack(pady=(6, 2))

        self._levels_text = tk.Text(panel, height=6, width=26,
                                     bg=BG_CARD, fg=TEXT_MAIN,
                                     font=("Consolas", 8),
                                     relief="flat", state="disabled",
                                     wrap="word", padx=6, pady=4)
        self._levels_text.pack(padx=6, pady=(0, 8))

    # ── LOG PANEL ─────────────────────────────────────────────────────

    def _build_log_panel(self):
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        frame = tk.Frame(self, bg=BG_CARD, height=160)
        frame.pack(fill=tk.X)
        frame.pack_propagate(False)

        header = tk.Frame(frame, bg=BG_CARD)
        header.pack(fill=tk.X, padx=8, pady=(6, 2))
        tk.Label(header, text="Algorithm Execution Log",
                 font=("Segoe UI", 9, "bold"),
                 fg=ACCENT, bg=BG_CARD).pack(side=tk.LEFT)
        tk.Button(header, text="Clear Log", command=self._clear_log,
                  font=("Segoe UI", 8), relief="flat", cursor="hand2",
                  bg=BG_PANEL, fg=TEXT_DIM, activebackground=BG_DARK).pack(side=tk.RIGHT)

        log_frame = tk.Frame(frame, bg=BG_CARD)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))

        self._log_text = tk.Text(log_frame, bg=BG_CARD, fg=TEXT_MAIN,
                                  font=("Consolas", 8),
                                  relief="flat", state="disabled",
                                  wrap="word", padx=4)
        log_scrollbar = ttk.Scrollbar(log_frame, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=log_scrollbar.set)

        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._log_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for coloring
        self._log_text.tag_configure("step",  foreground=GOLD)
        self._log_text.tag_configure("info",  foreground=ACCENT)
        self._log_text.tag_configure("ok",    foreground=ACCENT2)
        self._log_text.tag_configure("warn",  foreground=TEXT_WARN)
        self._log_text.tag_configure("enqueue", foreground="#9b59b6")

    # ── COMPLEXITY PANEL ─────────────────────────────────────────────

    def _build_complexity_panel(self):
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        frame = tk.Frame(self, bg=BG_HEADER)
        frame.pack(fill=tk.X)

        inner = tk.Frame(frame, bg=BG_HEADER)
        inner.pack(fill=tk.X, padx=20, pady=8)

        tk.Label(inner, text="Complexity Analysis",
                 font=("Segoe UI", 9, "bold"),
                 fg=GOLD, bg=BG_HEADER).pack(side=tk.LEFT, padx=(0, 20))

        complexities = [
            ("Time Complexity", "O(V + E)", "Every vertex and edge is visited exactly once."),
            ("Space Complexity", "O(V)",    "Queue + visited set each hold at most V nodes."),
        ]
        for label, big_o, note in complexities:
            box = tk.Frame(inner, bg=BG_CARD, padx=10, pady=4)
            box.pack(side=tk.LEFT, padx=6)
            tk.Label(box, text=label, font=("Segoe UI", 7), fg=TEXT_DIM, bg=BG_CARD).pack()
            tk.Label(box, text=big_o, font=("Segoe UI", 13, "bold"), fg=ACCENT2, bg=BG_CARD).pack()
            tk.Label(box, text=note, font=("Segoe UI", 7), fg=TEXT_DIM, bg=BG_CARD,
                     wraplength=180, justify="center").pack()

        tk.Label(inner,
                 text="BFS uses a FIFO queue so nodes are explored level by level. "
                      "All nodes at depth d are visited before any node at depth d+1.  "
                      "V = Stations,  E = Connections",
                 font=("Segoe UI", 8), fg=TEXT_DIM, bg=BG_HEADER,
                 wraplength=500, justify="left").pack(side=tk.LEFT, padx=16)

    # ==================================================================
    # COMMANDS
    # ==================================================================

    def _cmd_start_bfs(self):
        source = self._source_var.get().strip()
        if not source:
            self._show_error("Please select a source station.")
            return

        ok, msg, state = self.bfs.initialize(source)
        if not ok:
            self._show_error(msg)
            self._log(f"ERROR: {msg}", tag="warn")
            return

        self._bfs_initialized = True
        self._step_count = 0
        self._btn_next["state"]  = "normal"
        self._btn_auto["state"]  = "normal"
        self._btn_pause["state"] = "disabled"

        self._log(f"{'='*55}", tag="step")
        self._log(f"BFS STARTED  |  Source: {source}", tag="step")
        self._log(f"{'='*55}", tag="step")
        self._log(state.log_entry, tag="info")

        self._last_state = state
        self._refresh_canvas()
        self._refresh_info_panel(state)

    def _cmd_next_step(self):
        if not self._bfs_initialized:
            self._show_error("Please start BFS first.")
            return

        state = self.bfs.step()
        if state is None:
            self._log("BFS is already complete.", tag="ok")
            return

        self._last_state = state
        self._step_count += 1

        # Color the log line based on phase
        tag_map = {
            "dequeue": "step",
            "enqueue": "enqueue",
            "examine": "info",
            "done":    "ok",
        }
        tag = tag_map.get(state.phase, "info")
        self._log(state.log_entry, tag=tag)

        self._refresh_canvas()
        self._refresh_info_panel(state)

        if state.done:
            self._btn_next["state"]  = "disabled"
            self._btn_auto["state"]  = "disabled"
            self._btn_pause["state"] = "disabled"
            self._log("✔  BFS Complete! All reachable stations discovered.", tag="ok")
            self._show_completion_summary()

    def _cmd_auto_run(self):
        if self._auto_running:
            return
        if not self._bfs_initialized:
            self._show_error("Please start BFS first.")
            return

        self._auto_running = True
        self._btn_auto["state"]  = "disabled"
        self._btn_pause["state"] = "normal"
        self._btn_next["state"]  = "disabled"
        self._schedule_auto_step()

    def _schedule_auto_step(self):
        if not self._auto_running:
            return
        if self.bfs.is_done():
            self._stop_auto()
            return
        self._cmd_next_step()
        if not self.bfs.is_done():
            self._auto_after_id = self.after(AUTO_RUN_DELAY_MS, self._schedule_auto_step)
        else:
            self._stop_auto()

    def _cmd_pause(self):
        self._stop_auto()

    def _stop_auto(self):
        self._auto_running = False
        if self._auto_after_id:
            self.after_cancel(self._auto_after_id)
            self._auto_after_id = None
        self._btn_auto["state"]  = "normal" if self._bfs_initialized and not self.bfs.is_done() else "disabled"
        self._btn_pause["state"] = "disabled"
        self._btn_next["state"]  = "normal" if self._bfs_initialized and not self.bfs.is_done() else "disabled"

    def _cmd_reset_bfs(self):
        """Reset BFS state but keep the network intact."""
        self._stop_auto()
        self.bfs = BFSAlgorithm(self.graph)
        self._bfs_initialized = False
        self._last_state = None
        self._step_count = 0

        self._btn_next["state"]  = "disabled"
        self._btn_auto["state"]  = "disabled"
        self._btn_pause["state"] = "disabled"

        self._refresh_canvas()
        self._refresh_info_panel(None)
        self._log("BFS reset. Network preserved.", tag="info")

    def _cmd_add_station(self):
        name = self._station_name_var.get().strip().upper()
        ok, msg = self.graph.add_node(name)
        self._log(msg, tag="ok" if ok else "warn")
        if ok:
            self._station_name_var.set("")
            self._refresh_dropdowns()
            self._refresh_canvas()
            self._cmd_reset_bfs()

    def _cmd_remove_station(self):
        name = self._source_var.get().strip()
        if not name:
            self._show_error("Select a station to remove.")
            return
        if not messagebox.askyesno("Confirm", f"Remove station '{name}' and all its connections?"):
            return
        ok, msg = self.graph.remove_node(name)
        self._log(msg, tag="ok" if ok else "warn")
        if ok:
            self._refresh_dropdowns()
            self._refresh_canvas()
            self._cmd_reset_bfs()

    def _cmd_add_edge(self):
        u = self._conn_from_var.get().strip()
        v = self._conn_to_var.get().strip()
        if not u or not v:
            self._show_error("Select both 'From' and 'To' stations.")
            return
        ok, msg = self.graph.add_edge(u, v)
        self._log(msg, tag="ok" if ok else "warn")
        if ok:
            self._refresh_canvas()

    def _cmd_remove_edge(self):
        u = self._conn_from_var.get().strip()
        v = self._conn_to_var.get().strip()
        if not u or not v:
            self._show_error("Select both stations for the connection to remove.")
            return
        ok, msg = self.graph.remove_edge(u, v)
        self._log(msg, tag="ok" if ok else "warn")
        if ok:
            self._refresh_canvas()

    def _cmd_fail_station(self):
        name = self._fail_var.get().strip()
        if not name:
            self._show_error("Select a station to mark as failed.")
            return
        ok, msg = self.graph.set_failed(name)
        self._log(msg, tag="warn" if ok else "warn")
        if ok:
            self._refresh_canvas()
            self._refresh_info_panel(self._last_state)
            self._cmd_reset_bfs()

    def _cmd_restore_station(self):
        name = self._fail_var.get().strip()
        if not name:
            self._show_error("Select a failed station to restore.")
            return
        ok, msg = self.graph.restore(name)
        self._log(msg, tag="ok" if ok else "warn")
        if ok:
            self._refresh_canvas()
            self._refresh_info_panel(self._last_state)
            self._cmd_reset_bfs()

    def _cmd_reset_network(self):
        if not messagebox.askyesno("Confirm", "Reset the entire network? This cannot be undone."):
            return
        self._stop_auto()
        self.graph.reset()
        self.bfs = BFSAlgorithm(self.graph)
        self._bfs_initialized = False
        self._last_state = None
        self._canvas._positions = {}
        self._refresh_dropdowns()
        self._refresh_canvas()
        self._refresh_info_panel(None)
        self._log("Network reset to empty.", tag="warn")

    def _cmd_load_sample(self):
        self._stop_auto()
        self.graph.load_sample_network()
        self.bfs = BFSAlgorithm(self.graph)
        self._bfs_initialized = False
        self._last_state = None
        self._canvas._positions = {}
        self._source_var.set("A")
        self._refresh_dropdowns()
        self._refresh_canvas()
        self._refresh_info_panel(None)
        self._log("Sample network loaded: A–B–C–D–E–F–G", tag="ok")

    def _cmd_save_network(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Network Configuration",
        )
        if not path:
            return
        ok, msg = self.graph.save_to_json(path)
        self._log(msg, tag="ok" if ok else "warn")
        if not ok:
            self._show_error(msg)

    def _cmd_load_network(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Network Configuration",
        )
        if not path:
            return
        self._stop_auto()
        ok, msg = self.graph.load_from_json(path)
        self._log(msg, tag="ok" if ok else "warn")
        if ok:
            self.bfs = BFSAlgorithm(self.graph)
            self._bfs_initialized = False
            self._last_state = None
            self._canvas._positions = {}
            self._refresh_dropdowns()
            self._refresh_canvas()
            self._refresh_info_panel(None)
        else:
            self._show_error(msg)

    # ==================================================================
    # REFRESH HELPERS
    # ==================================================================

    def _refresh_dropdowns(self):
        nodes = self.graph.get_nodes()

        for cb_attr, var_attr in [
            ("_source_dropdown", "_source_var"),
            ("_conn_from_dropdown", "_conn_from_var"),
            ("_conn_to_dropdown", "_conn_to_var"),
            ("_fail_dropdown", "_fail_var"),
        ]:
            cb = getattr(self, cb_attr)
            var = getattr(self, var_attr)
            cb["values"] = nodes
            if nodes and var.get() not in nodes:
                var.set(nodes[0])
            elif not nodes:
                var.set("")

    def _refresh_canvas(self):
        self._canvas.draw_graph(self.graph, self._last_state)

    def _refresh_info_panel(self, state):
        reach = self.bfs.get_reachability()

        if state:
            current_lvl = state.levels.get(state.current, "—") if state.current else "—"
            self._info_vars["current"].set(state.current or "—")
            self._info_vars["level"].set(str(current_lvl))
            self._info_vars["phase"].set(state.phase.capitalize())
            self._info_vars["queue"].set(
                "  →  ".join(state.queue) if state.queue else "[ empty ]"
            )
            self._info_vars["visited"].set(
                ",  ".join(state.visited) if state.visited else "None"
            )
            self._info_vars["traversal"].set(
                " → ".join(state.traversal_order) if state.traversal_order else "—"
            )
        else:
            for k in ["current", "level", "phase", "queue", "visited", "traversal"]:
                self._info_vars[k].set("—")

        self._info_vars["reachable"].set(
            ",  ".join(reach["reachable"]) if reach["reachable"] else "None"
        )
        self._info_vars["unreachable"].set(
            ",  ".join(reach["unreachable"]) if reach["unreachable"] else "None"
        )
        self._info_vars["active_total"].set(str(reach["active_total"]))
        self._info_vars["failed_total"].set(str(reach["failed_total"]))
        pct = reach["reachability_pct"]
        self._info_vars["pct"].set(f"{pct:.1f}%")
        self._progress["value"] = pct

        # BFS levels summary
        levels = self.bfs.get_levels_summary()
        self._levels_text.configure(state="normal")
        self._levels_text.delete("1.0", tk.END)
        if levels:
            for lvl in sorted(levels.keys()):
                stations = ", ".join(levels[lvl])
                self._levels_text.insert(tk.END, f"Level {lvl}: {stations}\n")
        else:
            self._levels_text.insert(tk.END, "BFS not started yet.")
        self._levels_text.configure(state="disabled")

    def _show_completion_summary(self):
        reach = self.bfs.get_reachability()
        levels = self.bfs.get_levels_summary()
        levels_str = "\n".join(
            f"  Level {l}: {', '.join(stations)}"
            for l, stations in sorted(levels.items())
        )
        summary = (
            f"BFS Complete!\n\n"
            f"Reachability: {reach['reachability_pct']:.1f}%\n"
            f"Reachable stations ({len(reach['reachable'])}): "
            f"{', '.join(reach['reachable'])}\n"
            f"Unreachable stations ({len(reach['unreachable'])}): "
            f"{', '.join(reach['unreachable']) or 'None'}\n\n"
            f"BFS Levels:\n{levels_str}"
        )
        messagebox.showinfo("BFS Traversal Complete", summary)

    # ==================================================================
    # LOG HELPERS
    # ==================================================================

    def _log(self, message: str, tag: str = "info"):
        self._log_text.configure(state="normal")
        self._log_text.insert(tk.END, message + "\n", tag)
        self._log_text.see(tk.END)
        self._log_text.configure(state="disabled")

    def _clear_log(self):
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", tk.END)
        self._log_text.configure(state="disabled")

    def _show_error(self, message: str):
        messagebox.showerror("Error", message)
