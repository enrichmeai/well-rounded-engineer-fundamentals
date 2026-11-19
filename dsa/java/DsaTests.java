// Tests for the Java data structures: the same checks as ../tests/test_dsa.py, and each structure
// checked against Java's own (HashMap, PriorityQueue, LinkedHashMap, Arrays.sort).
// Plain Java, no test framework, so there is nothing to download. From this folder:
//
//     javac -d out *.java && java -cp out DsaTests

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.PriorityQueue;
import java.util.Random;

public class DsaTests {

    static int passed = 0;
    static final List<String> failed = new ArrayList<>();

    interface Check {
        void run() throws Exception;
    }

    static void test(String name, Check check) {
        try {
            check.run();
            passed++;
            System.out.println("PASS " + name);
        } catch (Throwable e) {
            failed.add(name);
            System.out.println("FAIL " + name + ": " + e);
        }
    }

    static void assertEquals(Object expected, Object actual) {
        if (!java.util.Objects.equals(expected, actual)) {
            throw new AssertionError("expected " + expected + " but got " + actual);
        }
    }

    static void assertTrue(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    static void expectThrows(Class<? extends Throwable> type, Check check) throws Exception {
        try {
            check.run();
        } catch (Throwable e) {
            if (type.isInstance(e)) return;
            throw e;
        }
        throw new AssertionError("expected " + type.getSimpleName());
    }

    static int[] range(int n) {
        int[] a = new int[n];
        for (int i = 0; i < n; i++) a[i] = i;
        return a;
    }

    public static void main(String[] args) throws Exception {
        // --- Big O ---------------------------------------------------------------------------
        test("searches find the right index", () -> {
            int[] items = new int[100];
            for (int i = 0; i < 100; i++) items[i] = 2 * i;
            for (int target : new int[] {0, 98, 198}) {
                assertEquals(target / 2, BigO.linearSearch(items, target).index());
                assertEquals(target / 2, BigO.binarySearch(items, target).index());
            }
            assertEquals(-1, BigO.binarySearch(items, 7).index());
        });
        test("binary search steps are logarithmic", () -> {
            for (int n : new int[] {10, 1000, 100_000}) {
                long steps = BigO.binarySearch(range(n), n).steps();
                assertTrue(steps <= (long) Math.floor(Math.log(n) / Math.log(2)) + 1, n + " took " + steps);
            }
        });
        test("growth matches Big O", () -> {
            List<BigO.Row> rows = BigO.table(10, 100, 1_000, 10_000);
            BigO.Row a = rows.get(0), b = rows.get(rows.size() - 1);
            assertEquals(b.n() / a.n(), (int) (b.linear() / a.linear()));
            assertEquals(b.n() / a.n(), (int) (b.set() / a.set()));
            assertEquals((long) b.n() * (b.n() - 1) / 2, b.nested());   // every pair once
        });
        test("duplicate checks agree", () -> {
            assertEquals(true, BigO.hasDuplicateSet(new int[] {3, 1, 4, 1, 5}).yes());
            assertEquals(true, BigO.hasDuplicateNested(new int[] {3, 1, 4, 1, 5}).yes());
            assertEquals(false, BigO.hasDuplicateSet(new int[] {1, 2, 3}).yes());
            assertEquals(false, BigO.hasDuplicateNested(new int[] {1, 2, 3}).yes());
        });

        // --- Hash table ----------------------------------------------------------------------
        test("FNV-1a follows the published algorithm, and int overflow is the modulo", () -> {
            assertEquals(0x811C9DC5, HashTable.fnv1a(""));                     // the offset basis
            long expected = ((0x811C9DC5L ^ 'a') * 0x01000193L) & 0xFFFFFFFFL;  // Python's version, in a long
            assertEquals(expected, Integer.toUnsignedLong(HashTable.fnv1a("a")));
        });
        test("String.hashCode is the documented formula", () -> {
            String s = "user-999";
            int h = 0;
            for (char c : s.toCharArray()) h = 31 * h + c;
            assertEquals(h, s.hashCode());
        });
        test("hash table behaves like HashMap", () -> {
            HashTable<String, Double> t = new HashTable<>(HashTable::fnv1a);
            Map<String, Double> ref = new HashMap<>();
            Random rng = new Random(1);
            for (int i = 0; i < 2000; i++) {
                String k = "k" + rng.nextInt(501);
                double v = rng.nextDouble();
                t.put(k, v);
                ref.put(k, v);
            }
            assertEquals(ref.size(), t.size);
            for (Map.Entry<String, Double> e : ref.entrySet()) assertEquals(e.getValue(), t.get(e.getKey()).value());
            expectThrows(NoSuchElementException.class, () -> t.get("missing"));
        });
        test("resizing keeps buckets short", () -> {
            HashTable<String, Integer> t = HashTable.fill(1000, HashTable::fnv1a);
            assertTrue((double) t.size / t.buckets.size() <= 0.75, "load factor");
            assertTrue(t.longestBucket() <= 8, "longest bucket " + t.longestBucket());
        });
        test("a bad hash makes lookup linear", () -> {
            HashTable<String, Integer> t = HashTable.fill(500, HashTable::badHash);
            assertEquals(500, t.longestBucket());
            assertEquals(500, t.get("user-499").comparisons());
        });
        test("HashMap still finds every key when every hash is 42", () -> {
            List<HashMapTrees.SameHash> plain = new ArrayList<>();
            List<HashMapTrees.SameHashOrdered> ordered = new ArrayList<>();
            for (int i = 0; i < 500; i++) {
                plain.add(new HashMapTrees.SameHash(i));
                ordered.add(new HashMapTrees.SameHashOrdered(i));
            }
            HashMapTrees.lookupMillis(plain);              // throws if a key were lost
            HashMapTrees.lookupMillis(ordered);
        });

        // --- Heap ----------------------------------------------------------------------------
        test("heap pops in the same order as PriorityQueue", () -> {
            Random rng = new Random(7);
            Heap<Integer> h = new Heap<>();
            PriorityQueue<Integer> ref = new PriorityQueue<>();
            for (int i = 0; i < 300; i++) {
                int v = rng.nextInt(101);
                h.push(v);
                ref.add(v);
            }
            for (int i = 0; i < 300; i++) assertEquals(ref.poll(), h.pop());
            expectThrows(NoSuchElementException.class, h::pop);
        });
        test("jobs pop by priority, then by name, like Python tuples", () -> {
            Heap<Heap.Job> h = new Heap<>();
            h.push(new Heap.Job(1, "restart db"));
            h.push(new Heap.Job(2, "retry payment"));
            h.push(new Heap.Job(1, "page on-call"));
            assertEquals("page on-call", h.pop().name());
            assertEquals("restart db", h.pop().name());
        });
        test("top k", () -> {
            Random rng = new Random(3);
            List<Integer> values = new ArrayList<>();
            for (int i = 0; i < 1000; i++) values.add(rng.nextInt(1_000_001));
            List<Integer> sorted = new ArrayList<>(values);
            sorted.sort(Collections.reverseOrder());
            assertEquals(sorted.subList(0, 5), Heap.topKLargest(values, 5));
        });

        // --- Graphs --------------------------------------------------------------------------
        test("BFS finds fewest hops and Dijkstra lowest cost", () -> {
            assertEquals(List.of("gateway", "ledger"), Graph.bfsPath(Graph.CALLS, "gateway", "ledger"));
            assertEquals(new Graph.Route(65, List.of("gateway", "orders", "payments", "ledger")),
                    Graph.dijkstra(Graph.CALLS, "gateway", "ledger"));
        });
        test("unreachable returns null", () -> {
            assertEquals(null, Graph.bfsPath(Graph.CALLS, "users", "ledger"));
            assertEquals(null, Graph.dijkstra(Graph.CALLS, "users", "ledger"));
        });

        // --- LRU cache -----------------------------------------------------------------------
        test("LRU evicts the least recently used", () -> {
            Lru<String, Integer> c = new Lru<>(2);
            c.put("a", 1);
            c.put("b", 2);
            assertEquals(1, c.get("a"));                   // a is now the most recent
            c.put("c", 3);                                 // evicts b, not a
            assertEquals(List.of("b"), c.evicted);
            assertEquals(null, c.get("b"));
            assertEquals(1, c.get("a"));
            assertEquals(3, c.get("c"));
            assertEquals(List.of("c", "a"), c.order());
        });
        test("LRU update does not grow", () -> {
            Lru<String, Integer> c = new Lru<>(2);
            c.put("a", 1);
            c.put("a", 2);
            assertEquals(1, c.map.size());
            assertEquals(2, c.get("a"));
        });
        test("hand-written LRU evicts the same keys as LinkedHashMap", () -> {
            Lru<Integer, Integer> mine = new Lru<>(5);
            Lru.BuiltIn<Integer, Integer> builtIn = new Lru.BuiltIn<>(5);
            Random rng = new Random(11);
            for (int i = 0; i < 2000; i++) {
                int key = rng.nextInt(12);
                if (rng.nextBoolean()) {
                    mine.put(key, i);
                    builtIn.put(key, i);
                } else {
                    assertEquals(builtIn.get(key), mine.get(key));
                }
            }
            assertEquals(builtIn.evicted, mine.evicted);
        });

        // --- Sorting -------------------------------------------------------------------------
        for (int n : new int[] {0, 1, 2, 50, 500}) {
            test("sorts agree with Arrays.sort, n=" + n, () -> {
                Random rng = new Random(n);
                int[] data = new int[n];
                for (int i = 0; i < n; i++) data[i] = rng.nextInt(2001) - 1000;
                int[] expected = data.clone();
                Arrays.sort(expected);
                assertTrue(Arrays.equals(expected, Sorting.insertionSort(data).items()), "insertion sort");
                assertTrue(Arrays.equals(expected, Sorting.mergeSort(data).items()), "merge sort");
            });
        }
        test("merge sort stays within n log n", () -> {
            Random rng = new Random(9);
            for (int n : new int[] {100, 1000, 4000}) {
                int[] data = new int[n];
                for (int i = 0; i < n; i++) data[i] = rng.nextInt();
                long bound = (long) n * (long) Math.ceil(Math.log(n) / Math.log(2));
                assertTrue(Sorting.mergeSort(data).comparisons() <= bound, "n=" + n);
            }
        });
        test("insertion sort is quadratic on reversed input", () -> {
            int n = 300;
            int[] reversed = new int[n];
            for (int i = 0; i < n; i++) reversed[i] = n - i;
            assertEquals((long) n * (n - 1) / 2, Sorting.insertionSort(reversed).comparisons());
        });

        System.out.println(passed + " passed, " + failed.size() + " failed");
        if (!failed.isEmpty()) {
            System.exit(1);
        }
    }
}
