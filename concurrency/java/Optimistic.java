// Optimistic concurrency: no lock while you work; check a version number when you save.
//
//     java Optimistic.java
//
// The same program as ../optimistic.py. Databases often do this with a `version` column:
//
//     UPDATE accounts SET balance = :new, version = version + 1
//     WHERE id = :id AND version = :version_you_read
//
// Two writers read version 0, the first save wins, the second is rejected and retries with fresh
// data. Nothing is lost, and nobody waited on a lock while working. A Java record plays the part
// of Python's frozen dataclass: an immutable row.

import java.util.List;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;

public class Optimistic {

    record Row(int balance, int version) {}

    /** One row, with a compare-and-set save: it succeeds only if the version is unchanged. */
    static class Store {
        private Row row = new Row(0, 0);

        synchronized Row read() {               // synchronized guards the store's own internals
            return row;
        }

        synchronized boolean saveIfVersion(int expectedVersion, int newBalance) {
            if (row.version() != expectedVersion) {
                return false;                   // someone else saved first: conflict
            }
            row = new Row(newBalance, expectedVersion + 1);
            return true;
        }
    }

    /** Read, compute, try to save; on a conflict, read again and retry. */
    static void deposit(Store store, int amount, List<String> log, String name, int maxTries,
                        Runnable beforeSave) {
        for (int attempt = 1; attempt <= maxTries; attempt++) {
            Row row = store.read();
            if (beforeSave != null) {
                beforeSave.run();               // in the demo: wait so both writers read first
            }
            if (store.saveIfVersion(row.version(), row.balance() + amount)) {
                log.add(name + ": attempt " + attempt + " saved " + row.balance() + " -> "
                        + (row.balance() + amount) + " (version " + row.version() + " -> "
                        + (row.version() + 1) + ")");
                return;
            }
            log.add(name + ": attempt " + attempt + " conflict (read version " + row.version()
                    + ", it has changed); retrying");
            beforeSave = null;                  // only force the clash on the first attempt
        }
        throw new IllegalStateException(name + ": gave up after " + maxTries + " conflicts");
    }

    record Outcome(Row row, List<String> log) {}

    /** Two writers deposit 100 each; both read before either saves. A saves first, then B. */
    static Outcome demo() throws InterruptedException {
        Store store = new Store();
        List<String> log = new CopyOnWriteArrayList<>();
        CyclicBarrier bothHaveRead = new CyclicBarrier(2);
        CountDownLatch aSaved = new CountDownLatch(1);   // Python's threading.Event

        Thread a = Thread.ofPlatform().start(() -> {
            deposit(store, 100, log, "A", 5, () -> await(bothHaveRead));
            aSaved.countDown();
        });
        Thread b = Thread.ofPlatform().start(() -> deposit(store, 100, log, "B", 5, () -> {
            await(bothHaveRead);
            try {
                aSaved.await();
            } catch (InterruptedException e) {
                throw new IllegalStateException(e);
            }
        }));
        a.join();
        b.join();
        return new Outcome(store.read(), log);
    }

    static void await(CyclicBarrier barrier) {
        try {
            barrier.await();
        } catch (InterruptedException | BrokenBarrierException e) {
            throw new IllegalStateException(e);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Outcome outcome = demo();
        outcome.log().forEach(System.out::println);
        System.out.println("final balance " + outcome.row().balance() + ", version " + outcome.row().version());
    }
}
