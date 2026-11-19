// A lost update between two threads, forced to happen every time, and three ways to prevent it.
//
//     java LostUpdate.java
//
// The same program as ../lost_update.py. Two threads each deposit 100 into a shared balance that
// starts at 0. Each one reads the balance, then writes back (what it read + 100). If both read
// before either writes, the second write overwrites the first, and one deposit is lost.
//
// A CyclicBarrier makes both threads wait until both have read, so the bad order happens on every
// run. Then the fixes: a synchronized block (Python's `with lock:`), and an AtomicInteger, which
// does read-add-write as one indivisible step. Python's standard library has no atomic integer.

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.atomic.AtomicInteger;

public class LostUpdate {

    static class Account {
        int balance;
    }

    /** Two deposits with no lock, both reads forced to happen before either write. */
    static int unsafeDeposits(int amount) throws InterruptedException {
        Account account = new Account();
        CyclicBarrier bothHaveRead = new CyclicBarrier(2);
        runTwice(() -> {
            int seen = account.balance;        // 1. read
            await(bothHaveRead);               // 2. wait until the other thread has read too
            account.balance = seen + amount;   // 3. write: based on a value that is now stale
        });
        return account.balance;
    }

    /** The same two deposits, with read-and-write done together while holding a lock. */
    static int lockedDeposits(int amount) throws InterruptedException {
        Account account = new Account();
        Object lock = new Object();
        runTwice(() -> {
            synchronized (lock) {              // only one thread at a time runs this block
                int seen = account.balance;
                account.balance = seen + amount;
            }
        });
        return account.balance;
    }

    /** No lock of our own: the hardware adds in one step that another thread cannot split. */
    static int atomicDeposits(int amount) throws InterruptedException {
        AtomicInteger balance = new AtomicInteger();
        runTwice(() -> balance.addAndGet(amount));
        return balance.get();
    }

    static void runTwice(Runnable work) throws InterruptedException {
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 2; i++) {
            threads.add(Thread.ofPlatform().start(work));
        }
        for (Thread t : threads) {
            t.join();                          // join also makes the threads' writes visible here
        }
    }

    static void await(CyclicBarrier barrier) {
        try {
            barrier.await();
        } catch (InterruptedException | BrokenBarrierException e) {
            throw new IllegalStateException(e);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("two deposits of 100, unsafe: " + unsafeDeposits(100));
        System.out.println("two deposits of 100, locked: " + lockedDeposits(100));
        System.out.println("two deposits of 100, atomic: " + atomicDeposits(100));
    }
}
