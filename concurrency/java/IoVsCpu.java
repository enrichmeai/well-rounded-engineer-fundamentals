// Java threads speed up waiting AND arithmetic; virtual threads make one thread per task cheap.
//
//     java IoVsCpu.java
//
// The counterpart of ../io_vs_cpu.py, and the place the two languages differ most.
//
// Part 1 does ten "requests" that each wait 0.2 s (Thread.sleep stands in for a network or disk
// wait). One after another they take about 2 s; with ten threads they overlap and take about 0.2 s.
// Same as Python.
//
// Part 2 does four chunks of pure arithmetic. The JVM has no global interpreter lock: each Java
// thread is an operating-system thread, and several run Java code at the same moment on different
// cores. So four threads beat one thread, where in standard CPython they did not and you needed
// processes.
//
// Part 3 is 10,000 waits. An OS thread is costly (memory for its stack, work for the kernel), so
// programs cap them with a pool, and a pool of 500 threads gets through 10,000 waits of 0.1 s in
// about 2 s. A virtual thread (Java 21, JEP 444) is a thread the JVM schedules on a few OS threads
// and parks while it waits, so one per task is cheap: the same 10,000 waits take about 0.1 s.
// Virtual threads make waiting cheaper; they do not make arithmetic faster.
//
// Timings depend on your machine, so your numbers will differ; compare the rows, not the values.

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

public class IoVsCpu {

    static void waitLikeIo(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    static long busyCpu(int n) {
        long total = 0;
        for (int i = 0; i < n; i++) {
            total += (long) i * i % 7;
        }
        return total;                  // returned and summed, so the JIT cannot skip the loop
    }

    interface Work {
        void run() throws Exception;
    }

    static double timed(Work work) throws Exception {
        long start = System.nanoTime();
        work.run();
        return (System.nanoTime() - start) / 1e9;
    }

    /** Run `count` copies of a task on an executor and wait for them all. */
    static long onExecutor(ExecutorService pool, int count, java.util.concurrent.Callable<Long> task)
            throws Exception {
        try (pool) {                   // ExecutorService is AutoCloseable since Java 19
            List<Future<Long>> futures = new ArrayList<>();
            for (int i = 0; i < count; i++) {
                futures.add(pool.submit(task));
            }
            long sum = 0;
            for (Future<Long> f : futures) {
                sum += f.get();
            }
            return sum;
        }
    }

    static final int CHUNK = 200_000_000;

    public static void main(String[] args) throws Exception {
        System.out.println("Java " + Runtime.version().feature() + ", "
                + Runtime.getRuntime().availableProcessors() + " processors");
        busyCpu(CHUNK);                // warm up, so the JIT has compiled the loop before we time it

        System.out.println("1. ten waits of 0.2 s (I/O-bound)");
        System.out.printf("   one after another : %.2f s%n", timed(() -> {
            for (int i = 0; i < 10; i++) waitLikeIo(200);
        }));
        System.out.printf("   ten threads       : %.2f s%n", timed(() ->
                onExecutor(Executors.newFixedThreadPool(10), 10, () -> { waitLikeIo(200); return 0L; })));

        System.out.println("2. four chunks of arithmetic (CPU-bound)");
        System.out.printf("   one after another : %.2f s%n", timed(() -> {
            for (int i = 0; i < 4; i++) busyCpu(CHUNK);
        }));
        System.out.printf("   four threads      : %.2f s%n", timed(() ->
                onExecutor(Executors.newFixedThreadPool(4), 4, () -> busyCpu(CHUNK))));

        System.out.println("3. 10,000 waits of 0.1 s");
        System.out.printf("   pool of 500 OS threads      : %.2f s%n", timed(() ->
                onExecutor(Executors.newFixedThreadPool(500), 10_000, () -> { waitLikeIo(100); return 0L; })));
        System.out.printf("   one virtual thread per wait : %.2f s%n", timed(() ->
                onExecutor(Executors.newVirtualThreadPerTaskExecutor(), 10_000, () -> { waitLikeIo(100); return 0L; })));
    }
}
