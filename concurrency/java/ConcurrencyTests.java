// Tests for the Java concurrency examples: the same checks as ../tests/test_concurrency.py.
// Plain Java, no test framework, so there is nothing to download. From this folder:
//
//     javac -d out *.java && java -cp out ConcurrencyTests
//
// Each check prints PASS or FAIL; the program exits with status 1 if any check failed.

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;

public class ConcurrencyTests {

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
        if (!expected.equals(actual)) {
            throw new AssertionError("expected " + expected + " but got " + actual);
        }
    }

    static void assertTrue(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    public static void main(String[] args) throws Exception {
        for (int run = 1; run <= 5; run++) {
            // The barrier forces the bad interleaving, so this is the same on every run.
            test("unsafe deposits always lose one update, run " + run,
                    () -> assertEquals(100, LostUpdate.unsafeDeposits(100)));
            test("locked deposits keep both, run " + run,
                    () -> assertEquals(200, LostUpdate.lockedDeposits(100)));
            test("atomic deposits keep both, run " + run,
                    () -> assertEquals(200, LostUpdate.atomicDeposits(100)));
        }

        test("opposite lock orders deadlock", () -> assertEquals(
                Map.of("A", "holds lock1, stuck waiting for lock2", "B", "holds lock2, stuck waiting for lock1"),
                Deadlock.run(new String[] {"lock1", "lock2"}, new String[] {"lock2", "lock1"}, 1000)));
        test("same lock order does not deadlock", () -> assertEquals(
                Map.of("A", "took lock1 then lock2", "B", "took lock1 then lock2"),
                Deadlock.run(new String[] {"lock1", "lock2"}, new String[] {"lock1", "lock2"}, 1000)));

        test("store rejects a stale version", () -> {
            Optimistic.Store store = new Optimistic.Store();
            assertEquals(true, store.saveIfVersion(0, 50));
            assertEquals(false, store.saveIfVersion(0, 999));     // version is now 1
            assertEquals(new Optimistic.Row(50, 1), store.read());
        });
        test("optimistic demo detects the conflict and loses nothing", () -> {
            Optimistic.Outcome outcome = Optimistic.demo();
            assertEquals(new Optimistic.Row(200, 2), outcome.row());
            assertTrue(outcome.log().stream().anyMatch(line -> line.contains("conflict")), "no conflict logged");
            assertTrue(outcome.log().get(outcome.log().size() - 1).startsWith("B: attempt 2 saved 100 -> 200"),
                    "last line: " + outcome.log());
        });
        test("deposit gives up after max tries", () -> {
            Optimistic.Store alwaysConflicts = new Optimistic.Store() {
                @Override
                synchronized boolean saveIfVersion(int expectedVersion, int newBalance) {
                    return false;              // another writer always saves first
                }
            };
            List<String> log = new ArrayList<>();
            try {
                Optimistic.deposit(alwaysConflicts, 100, log, "C", 3, null);
                throw new AssertionError("expected it to give up");
            } catch (IllegalStateException e) {
                assertTrue(e.getMessage().contains("gave up after 3 conflicts"), e.getMessage());
            }
            assertEquals(3, log.size());
        });

        test("threads overlap waits", () -> {
            double sequential = IoVsCpu.timed(() -> {
                for (int i = 0; i < 8; i++) IoVsCpu.waitLikeIo(50);
            });
            double threaded = IoVsCpu.timed(() -> IoVsCpu.onExecutor(
                    Executors.newFixedThreadPool(8), 8, () -> { IoVsCpu.waitLikeIo(50); return 0L; }));
            assertTrue(sequential >= 0.35, "8 x 0.05 s one after another took " + sequential);
            assertTrue(threaded < sequential / 3, "threads took " + threaded + " vs " + sequential);
        });
        test("busyCpu computes the same sum as the Python version", () -> {
            long expected = 0;
            for (int i = 0; i < 10; i++) expected += (long) i * i % 7;
            assertEquals(expected, IoVsCpu.busyCpu(10));
        });
        test("threads run arithmetic in parallel (no GIL)", () -> {
            int cores = Runtime.getRuntime().availableProcessors();
            if (cores < 2) {
                System.out.println("     (skipped the timing: this machine has 1 processor)");
                return;
            }
            int chunk = 50_000_000;
            IoVsCpu.busyCpu(chunk);            // warm up the JIT
            double sequential = IoVsCpu.timed(() -> {
                for (int i = 0; i < 2; i++) IoVsCpu.busyCpu(chunk);
            });
            double threaded = IoVsCpu.timed(() -> IoVsCpu.onExecutor(
                    Executors.newFixedThreadPool(2), 2, () -> IoVsCpu.busyCpu(chunk)));
            // Two cores should nearly halve it; a wide margin so a busy CI machine still passes.
            assertTrue(threaded < sequential / 1.3, "threads took " + threaded + " vs " + sequential);
        });
        test("10,000 virtual threads wait at the same time", () -> {
            double seconds = IoVsCpu.timed(() -> IoVsCpu.onExecutor(
                    Executors.newVirtualThreadPerTaskExecutor(), 10_000, () -> { IoVsCpu.waitLikeIo(50); return 0L; }));
            assertTrue(seconds < 5, "10,000 waits of 0.05 s took " + seconds + " s (one after another: 500 s)");
        });

        int[][] shapes = {{1, 1}, {2, 3}, {4, 1}};
        for (int[] shape : shapes) {
            test("pipeline prices every order once, workers=" + shape[0] + " capacity=" + shape[1], () -> {
                List<Pipeline.Order> orders = new ArrayList<>();
                for (int i = 1; i <= 20; i++) {
                    orders.add(new Pipeline.Order(i, i % 2 == 1 ? "tea" : "cake", i));
                }
                List<Pipeline.Result> results = Pipeline.run(orders, Map.of("tea", 3, "cake", 5), shape[0], shape[1]);
                assertEquals(20, results.size());
                for (int i = 0; i < 20; i++) assertEquals(i + 1, results.get(i).id());
                assertEquals(new Pipeline.Result(1, 3), results.get(0));
                assertEquals(new Pipeline.Result(2, 10), results.get(1));
            });
        }

        test("Amdahl matches the guide's table", () -> {
            assertEquals("1.82", String.format("%.2f", Amdahl.speedup(0.9, 2)));
            assertEquals("4.71", String.format("%.2f", Amdahl.speedup(0.9, 8)));
            assertEquals("8.77", String.format("%.2f", Amdahl.speedup(0.9, 64)));
            assertTrue(Math.abs(Amdahl.ceiling(0.9) - 10) < 1e-9, "ceiling");
            assertEquals(1.0, Amdahl.speedup(0.9, 1));
        });
        test("Amdahl rejects nonsense", () -> {
            for (double[] bad : new double[][] {{1.5, 2}, {0.5, 0}}) {
                try {
                    Amdahl.speedup(bad[0], bad[1]);
                    throw new AssertionError("accepted p=" + bad[0] + " s=" + bad[1]);
                } catch (IllegalArgumentException expected) {
                    // good
                }
            }
        });

        System.out.println(passed + " passed, " + failed.size() + " failed");
        if (!failed.isEmpty()) {
            System.exit(1);
        }
    }
}
