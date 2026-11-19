// Graph search: breadth-first search for the fewest hops, Dijkstra for the cheapest path.
//
//     java Graph.java
//
// The same program as ../graph.py, on the same map of services calling each other (latency in ms).
//
//   BFS        visit nodes in rings of distance 1, 2, 3...; uses a queue (ArrayDeque).   O(V + E)
//   Dijkstra   always expand the cheapest path found so far; uses a PriorityQueue.      O((V + E) log V)
//
// One Java difference matters here. A Python dict keeps the order you inserted keys, so BFS tries
// neighbours in the order written. Java's HashMap and Map.of promise no order at all, so the graph
// is built from LinkedHashMap, which keeps insertion order. With ties (two paths of equal length),
// neighbour order decides which one BFS returns.

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Deque;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;

public class Graph {

    static final Map<String, Map<String, Integer>> CALLS = new LinkedHashMap<>();

    static {
        edges("gateway", "auth", 5, "orders", 20, "search", 40, "ledger", 200);   // a direct but slow call
        edges("auth", "users", 5);
        edges("orders", "payments", 30, "inventory", 10);
        edges("search", "inventory", 5);
        edges("users");
        edges("payments", "ledger", 15);
        edges("inventory", "ledger", 50);
        edges("ledger");
    }

    static void edges(String from, Object... calleeThenLatency) {
        Map<String, Integer> out = new LinkedHashMap<>();
        for (int i = 0; i < calleeThenLatency.length; i += 2) {
            out.put((String) calleeThenLatency[i], (Integer) calleeThenLatency[i + 1]);
        }
        CALLS.put(from, out);
    }

    /** The path with the fewest edges, or null if the goal cannot be reached. */
    static List<String> bfsPath(Map<String, Map<String, Integer>> graph, String start, String goal) {
        Deque<List<String>> queue = new ArrayDeque<>();
        queue.add(List.of(start));
        Set<String> seen = new HashSet<>(Set.of(start));
        while (!queue.isEmpty()) {
            List<String> path = queue.removeFirst();          // first in, first out: nearest rings first
            String node = path.get(path.size() - 1);
            if (node.equals(goal)) {
                return path;
            }
            for (String next : graph.get(node).keySet()) {
                if (seen.add(next)) {
                    List<String> longer = new ArrayList<>(path);
                    longer.add(next);
                    queue.addLast(longer);
                }
            }
        }
        return null;
    }

    record Route(int cost, List<String> path) {}

    /** The cheapest path, or null if the goal cannot be reached. Every edge cost must be zero or more. */
    static Route dijkstra(Map<String, Map<String, Integer>> graph, String start, String goal) {
        PriorityQueue<Route> frontier = new PriorityQueue<>(Comparator.comparingInt(Route::cost));
        frontier.add(new Route(0, List.of(start)));
        Set<String> done = new HashSet<>();
        while (!frontier.isEmpty()) {
            Route route = frontier.poll();
            String node = route.path().get(route.path().size() - 1);
            if (node.equals(goal)) {
                return route;
            }
            if (!done.add(node)) {
                continue;                                     // already expanded by a cheaper route
            }
            for (Map.Entry<String, Integer> edge : graph.get(node).entrySet()) {
                if (!done.contains(edge.getKey())) {
                    List<String> longer = new ArrayList<>(route.path());
                    longer.add(edge.getKey());
                    frontier.add(new Route(route.cost() + edge.getValue(), longer));
                }
            }
        }
        return null;
    }

    public static void main(String[] args) {
        System.out.println("fewest calls   gateway -> ledger: " + String.join(" -> ", bfsPath(CALLS, "gateway", "ledger")));
        Route r = dijkstra(CALLS, "gateway", "ledger");
        System.out.println("lowest latency gateway -> ledger: " + String.join(" -> ", r.path()) + " (" + r.cost() + " ms)");
    }
}
