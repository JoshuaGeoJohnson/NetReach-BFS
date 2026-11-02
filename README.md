# NetReach – Emergency Communication Network Reachability Analyzer

**DAA Assignment Project | Algorithm: Breadth-First Search (BFS)**

---

## Overview

NetReach is a desktop application that simulates an emergency communication
network and uses the **Breadth-First Search (BFS)** algorithm to determine
which communication stations are reachable from a selected source station.

The application provides a full step-by-step BFS visualization with:
- Node coloring by BFS state
- Real-time algorithm execution log
- Communication station failure simulation
- Network reachability percentage analysis
- JSON save/load for network configurations

---

## Technology Stack

| Component         | Technology                   |
|-------------------|------------------------------|
| Language          | Python 3.8+                  |
| GUI               | Tkinter (built-in)           |
| Graph Visualization | Tkinter Canvas             |
| Algorithm         | Breadth-First Search (BFS)   |
| Data Structure    | Adjacency List (dict of sets)|
| Queue             | `collections.deque`          |
| Persistence       | JSON                         |

No external dependencies required – runs on any Python 3.8+ installation.

---

## Project Structure

```
NetReach/
├── main.py           # Entry point – launches the application
├── bfs_algorithm.py  # Pure BFS engine (no GUI code)
├── graph_manager.py  # Graph data structure + JSON persistence
├── visualization.py  # Tkinter Canvas rendering engine
├── gui.py            # Main application window + all panels
├── README.md         # This file
└── requirements.txt  # Dependencies (all stdlib)
```

---

## Setup and Running

### Prerequisites
- Python 3.8 or higher
- Tkinter (included with standard Python on Windows)

### Run the Application
```bash
cd NetReach
python main.py
```

On **Windows** with VS Code:
1. Open the `NetReach` folder in VS Code
2. Open a terminal (`Ctrl+` `)
3. Run: `python main.py`

---

## User Guide

### Starting the Application
The app loads with the sample network (stations A–G) ready to use.

### BFS Controls
| Button       | Action                                      |
|--------------|---------------------------------------------|
| Start BFS    | Initialize BFS with the selected source     |
| Next Step    | Execute exactly one BFS operation           |
| Auto Run     | Automatically step through BFS with delays  |
| Pause        | Pause auto-run                              |
| Reset BFS    | Reset BFS state, keep network intact        |

### Network Management
- **Add Station**: Type a name and click "Add Station"
- **Remove Station**: Select in Source dropdown → "Remove Station"
- **Add Connection**: Select From + To → "Add Connection"
- **Remove Connection**: Select From + To → "Remove Connection"

### Failure Simulation
1. Select a station in the "Failure Simulation" dropdown
2. Click "Simulate Failure" → station turns red
3. Re-run BFS to see impact on reachability
4. Click "Restore Station" to recover it

### Save/Load Network
- Click "Save Network" to export to JSON
- Click "Load Network" to import from JSON

---

## Node Color Legend

| Color  | Meaning                        |
|--------|--------------------------------|
| Gray   | Unvisited station              |
| Green  | Source station (Level 0)       |
| Yellow | Currently processing (dequeued)|
| Blue   | Visited (explored)             |
| Purple | In queue (discovered, pending) |
| Red    | Failed station                 |

---

## BFS Algorithm Explanation

```
BFS(Graph G, source s):
  visited = {s}
  queue = deque([s])
  level[s] = 0

  while queue is not empty:
      u = queue.popleft()          # Dequeue front

      for each neighbor v of u:
          if v not in visited and v not failed:
              visited.add(v)
              level[v] = level[u] + 1
              queue.append(v)      # Enqueue
```

**Why a Queue?**
BFS uses a FIFO queue to ensure nodes are explored level by level.
All nodes at depth `d` are visited before any node at depth `d+1`.

---

## Complexity Analysis

| Complexity | Bound  | Explanation                                       |
|------------|--------|---------------------------------------------------|
| Time       | O(V+E) | Every station and connection visited exactly once |
| Space      | O(V)   | Queue + visited set hold at most V nodes          |

Where **V** = number of stations, **E** = number of connections.

---

## Sample Network

```
        A
       / \
      B   D
     / \ / \
    C  E F  G
```

**Connections:** A-B, A-D, B-C, B-E, D-F, D-G

**BFS Traversal from A:** A → B → D → C → E → F → G

**BFS Levels:**
- Level 0: A
- Level 1: B, D
- Level 2: C, E, F, G

---

## Test Cases

| # | Scenario                    | Expected Behavior                               |
|---|-----------------------------|-------------------------------------------------|
| 1 | Normal connected network    | All stations reachable, 100% reachability       |
| 2 | Disconnected network        | Only connected component reachable              |
| 3 | Single station              | 100% reachability (source only)                 |
| 4 | Failed intermediate station | Subtree unreachable, reduced reachability %     |
| 5 | Multiple failed stations    | Multiple subtrees may be cut off                |
| 6 | Failed source station       | Error: "Source station is FAILED"               |
| 7 | Empty graph                 | Error: "Station does not exist"                 |
| 8 | Duplicate connections       | Error: "Connection already exists"              |

---

## Author Notes

This project demonstrates:
1. **BFS algorithm** with step-by-step visualization
2. **Graph data structures** (adjacency list)
3. **Queue usage** (`collections.deque`) in BFS
4. **Level-by-level traversal** property of BFS
5. **Real-world application** in network reachability analysis
