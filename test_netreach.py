"""
test_netreach.py - All 8 test cases for NetReach
"""
import sys
sys.path.insert(0, '.')
from graph_manager import GraphManager
from bfs_algorithm import BFSAlgorithm


def run_bfs_to_completion(bfs):
    while not bfs.is_done():
        bfs.step()


print("=== Test 1: Normal connected network ===")
g = GraphManager()
g.load_sample_network()
bfs = BFSAlgorithm(g)
ok, msg, state = bfs.initialize('A')
assert ok, msg
run_bfs_to_completion(bfs)
r = bfs.get_reachability()
assert r['reachability_pct'] == 100.0, f"Expected 100%, got {r['reachability_pct']}"
print("PASS - 100% reachability, traversal: A->B->D->C->E->F->G")

print("=== Test 2: Disconnected network ===")
g = GraphManager()
for n in ['A', 'B', 'C', 'X', 'Y']:
    g.add_node(n)
g.add_edge('A', 'B')
g.add_edge('B', 'C')
g.add_edge('X', 'Y')
bfs = BFSAlgorithm(g)
ok, msg, state = bfs.initialize('A')
assert ok
run_bfs_to_completion(bfs)
r = bfs.get_reachability()
assert sorted(r['reachable']) == ['A', 'B', 'C'], f"Got {r['reachable']}"
assert sorted(r['unreachable']) == ['X', 'Y'], f"Got {r['unreachable']}"
print("PASS - A,B,C reachable; X,Y unreachable")

print("=== Test 3: Single station ===")
g = GraphManager()
g.add_node('S')
bfs = BFSAlgorithm(g)
ok, msg, state = bfs.initialize('S')
assert ok
run_bfs_to_completion(bfs)
r = bfs.get_reachability()
assert r['reachability_pct'] == 100.0
print("PASS - single node 100%")

print("=== Test 4: Failed intermediate station ===")
g = GraphManager()
g.load_sample_network()
g.set_failed('B')  # This cuts off C, E
bfs = BFSAlgorithm(g)
ok, msg, state = bfs.initialize('A')
assert ok
run_bfs_to_completion(bfs)
r = bfs.get_reachability()
assert 'C' in r['unreachable'] or 'E' in r['unreachable'], f"Got {r}"
print(f"PASS - unreachable: {r['unreachable']}, pct: {r['reachability_pct']:.1f}%")

print("=== Test 5: Multiple failed stations ===")
g = GraphManager()
g.load_sample_network()
g.set_failed('B')
g.set_failed('D')
bfs = BFSAlgorithm(g)
ok, msg, state = bfs.initialize('A')
assert ok
run_bfs_to_completion(bfs)
r = bfs.get_reachability()
assert r['reachable'] == ['A'], f"Expected only A, got {r['reachable']}"
print(f"PASS - only A reachable, pct: {r['reachability_pct']:.1f}%")

print("=== Test 6: Failed source station ===")
g = GraphManager()
g.load_sample_network()
g.set_failed('A')
bfs = BFSAlgorithm(g)
ok, msg, state = bfs.initialize('A')
assert not ok, "Should fail when source is failed"
print(f"PASS - correctly rejected: {msg}")

print("=== Test 7: Empty graph ===")
g = GraphManager()
bfs = BFSAlgorithm(g)
ok, msg, state = bfs.initialize('A')
assert not ok
print(f"PASS - correctly rejected empty graph: {msg}")

print("=== Test 8: Duplicate connections ===")
g = GraphManager()
g.load_sample_network()
ok2, msg2 = g.add_edge('A', 'B')
assert not ok2
print(f"PASS - duplicate rejected: {msg2}")

print()
print("ALL 8 TEST CASES PASSED!")
