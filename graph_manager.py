"""
graph_manager.py
----------------
Manages the communication network graph data structure.
Uses an adjacency list (dict of sets) for O(1) neighbor lookups.
Handles node/edge CRUD, validation, and JSON serialization.
"""

import json
from typing import Optional


class GraphManager:
    """
    Represents the emergency communication network as an undirected graph.

    Internally uses an adjacency list:
        self._adj: dict[str, set[str]]
            key   = station name
            value = set of directly connected station names
    """

    def __init__(self):
        self._adj: dict[str, set[str]] = {}
        self._failed: set[str] = set()

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def add_node(self, name: str) -> tuple[bool, str]:
        """Add a station. Returns (success, message)."""
        name = name.strip().upper()
        if not name:
            return False, "Station name cannot be empty."
        if len(name) > 10:
            return False, "Station name must be 10 characters or fewer."
        if name in self._adj:
            return False, f"Station '{name}' already exists."
        self._adj[name] = set()
        return True, f"Station '{name}' added successfully."

    def remove_node(self, name: str) -> tuple[bool, str]:
        """Remove a station and all its connections."""
        if name not in self._adj:
            return False, f"Station '{name}' does not exist."
        # Remove edges to this node from all neighbors
        for neighbor in list(self._adj[name]):
            self._adj[neighbor].discard(name)
        del self._adj[name]
        self._failed.discard(name)
        return True, f"Station '{name}' removed."

    # ------------------------------------------------------------------
    # Edge operations
    # ------------------------------------------------------------------

    def add_edge(self, u: str, v: str) -> tuple[bool, str]:
        """Add an undirected connection between stations u and v."""
        if u not in self._adj:
            return False, f"Station '{u}' does not exist."
        if v not in self._adj:
            return False, f"Station '{v}' does not exist."
        if u == v:
            return False, "Self-loops are not allowed."
        if v in self._adj[u]:
            return False, f"Connection '{u}-{v}' already exists."
        self._adj[u].add(v)
        self._adj[v].add(u)
        return True, f"Connection '{u}–{v}' added."

    def remove_edge(self, u: str, v: str) -> tuple[bool, str]:
        """Remove the connection between u and v."""
        if u not in self._adj or v not in self._adj[u]:
            return False, f"Connection '{u}-{v}' does not exist."
        self._adj[u].discard(v)
        self._adj[v].discard(u)
        return True, f"Connection '{u}–{v}' removed."

    # ------------------------------------------------------------------
    # Failure simulation
    # ------------------------------------------------------------------

    def set_failed(self, name: str) -> tuple[bool, str]:
        """Mark a station as failed."""
        if name not in self._adj:
            return False, f"Station '{name}' does not exist."
        self._failed.add(name)
        return True, f"Station '{name}' marked as FAILED."

    def restore(self, name: str) -> tuple[bool, str]:
        """Restore a failed station."""
        if name not in self._adj:
            return False, f"Station '{name}' does not exist."
        if name not in self._failed:
            return False, f"Station '{name}' is not failed."
        self._failed.discard(name)
        return True, f"Station '{name}' restored."

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_nodes(self) -> list[str]:
        """Return sorted list of all station names."""
        return sorted(self._adj.keys())

    def get_active_nodes(self) -> list[str]:
        """Return stations that are not failed."""
        return sorted(n for n in self._adj if n not in self._failed)

    def get_failed_nodes(self) -> list[str]:
        """Return list of failed station names."""
        return sorted(self._failed)

    def get_neighbors(self, name: str) -> list[str]:
        """Return sorted neighbors of a station (only active ones for BFS)."""
        return sorted(self._adj.get(name, set()))

    def get_active_neighbors(self, name: str) -> list[str]:
        """Return sorted active (non-failed) neighbors."""
        return sorted(n for n in self._adj.get(name, set()) if n not in self._failed)

    def get_edges(self) -> list[tuple[str, str]]:
        """Return list of unique edges as (u, v) pairs (u < v)."""
        edges = []
        seen = set()
        for u in self._adj:
            for v in self._adj[u]:
                key = (min(u, v), max(u, v))
                if key not in seen:
                    seen.add(key)
                    edges.append(key)
        return sorted(edges)

    def is_failed(self, name: str) -> bool:
        return name in self._failed

    def node_count(self) -> int:
        return len(self._adj)

    def active_node_count(self) -> int:
        return len(self._adj) - len(self._failed)

    def edge_count(self) -> int:
        return len(self.get_edges())

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_to_json(self, filepath: str) -> tuple[bool, str]:
        """Save network configuration to a JSON file."""
        try:
            data = {
                "stations": self.get_nodes(),
                "connections": [list(e) for e in self.get_edges()],
                "failed": list(self._failed),
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True, f"Network saved to '{filepath}'."
        except Exception as exc:
            return False, f"Save failed: {exc}"

    def load_from_json(self, filepath: str) -> tuple[bool, str]:
        """Load network configuration from a JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._adj = {}
            self._failed = set()

            for station in data.get("stations", []):
                self.add_node(station)
            for conn in data.get("connections", []):
                if len(conn) == 2:
                    self.add_edge(conn[0].upper(), conn[1].upper())
            for failed in data.get("failed", []):
                self.set_failed(failed.upper())

            return True, f"Network loaded from '{filepath}'."
        except FileNotFoundError:
            return False, f"File not found: '{filepath}'"
        except json.JSONDecodeError as exc:
            return False, f"Invalid JSON: {exc}"
        except Exception as exc:
            return False, f"Load failed: {exc}"

    def reset(self):
        """Clear the entire network."""
        self._adj = {}
        self._failed = set()

    def load_sample_network(self):
        """Load the predefined sample network for demonstration."""
        self.reset()
        for station in ["A", "B", "C", "D", "E", "F", "G"]:
            self.add_node(station)
        for u, v in [("A", "B"), ("A", "D"), ("B", "C"), ("B", "E"), ("D", "F"), ("D", "G")]:
            self.add_edge(u, v)
