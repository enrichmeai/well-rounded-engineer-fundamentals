// A deadlock between two threads, detected instead of hanging, and the fix: one lock order.
//
//     java Deadlock.java
//
// The same program as ../deadlock.py. Thread A takes lock 1 then wants lock 2; thread B takes
// lock 2 then wants lock 1. Each holds what the other needs, so neither can go on.
//
// So the demo does not hang your terminal, each thread asks for its second lock with
// ReentrantLock.tryLock(timeout). A timeout that expires is how we *detect* the deadlock. (A plain
// `synchronized` block has no timeout: two threads stuck in one wait for ever. That is why
// java.util.concurrent.locks exists.) The fix breaks the circular wait: every thread takes the
// locks in the same order.

import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.locks.ReentrantLock;

public class Deadlock {

    /** Run two threads that each take two locks in the given orders. Returns what each one managed. */
    static Map<String, String> run(String[] orderA, String[] orderB, long timeoutMillis)
            throws InterruptedException {
        Map<String, ReentrantLock> locks = Map.of("lock1", new ReentrantLock(), "lock2", new ReentrantLock());
        CyclicBarrier bothHoldFirst = new CyclicBarrier(2);
        CyclicBarrier bothHaveTried = new CyclicBarrier(2);
        Map<String, String> result = new ConcurrentHashMap<>();

        class Worker implements Runnable {
            final String name;
            final String[] order;

            Worker(String name, String[] order) {
                this.name = name;
                this.order = order;
            }

            public void run() {
                ReentrantLock first = locks.get(order[0]);
                ReentrantLock second = locks.get(order[1]);
                first.lock();
                try {
                    // Wait until the other thread holds its first lock too (forces the bad timing).
                    // With the SAME order, the other thread is blocked waiting for our first lock,
                    // so it never arrives and the wait times out. That is expected and harmless.
                    awaitQuietly(bothHoldFirst, timeoutMillis);
                    if (second.tryLock(timeoutMillis, TimeUnit.MILLISECONDS)) {
                        second.unlock();
                        result.put(name, "took " + order[0] + " then " + order[1]);
                    } else {
                        result.put(name, "holds " + order[0] + ", stuck waiting for " + order[1]);
                    }
                    // Keep holding the first lock until the other thread has tried too, so a
                    // thread that gives up cannot hand its lock to the other one mid-attempt.
                    awaitQuietly(bothHaveTried, timeoutMillis);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    first.unlock();
                }
            }
        }

        Thread a = Thread.ofPlatform().start(new Worker("A", orderA));
        Thread b = Thread.ofPlatform().start(new Worker("B", orderB));
        a.join();
        b.join();
        return new TreeMap<>(result);
    }

    static void awaitQuietly(CyclicBarrier barrier, long timeoutMillis) throws InterruptedException {
        try {
            barrier.await(timeoutMillis, TimeUnit.MILLISECONDS);
        } catch (BrokenBarrierException | TimeoutException e) {
            // the other thread did not arrive in time: carry on, as the Python version does
        }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("opposite orders (A: 1 then 2, B: 2 then 1):");
        run(new String[] {"lock1", "lock2"}, new String[] {"lock2", "lock1"}, 500)
                .forEach((name, what) -> System.out.println("  " + name + " " + what));
        System.out.println("same order (both: 1 then 2):");
        run(new String[] {"lock1", "lock2"}, new String[] {"lock1", "lock2"}, 500)
                .forEach((name, what) -> System.out.println("  " + name + " " + what));
    }
}
