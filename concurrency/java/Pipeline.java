// Share data by passing it through a queue, instead of sharing memory: a producer-consumer pipeline.
//
//     java Pipeline.java
//
// The same program as ../pipeline.py. A producer puts orders on the first queue; two workers take
// them off, price them, and put results on a second queue; a collector reads the results. Java's
// BlockingQueue does its own locking, like Python's queue.Queue.
//
// A bounded queue (ArrayBlockingQueue with capacity 3) gives back-pressure: if the workers fall
// behind, the producer blocks on put() instead of filling memory. A special STOP order, compared
// by identity (==), tells each worker to finish.

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

public class Pipeline {

    record Order(int id, String item, int qty) {}

    record Result(int id, int total) {}

    static final Order STOP = new Order(-1, "", 0);      // no real order is this same object
    static final Result DONE = new Result(-1, 0);

    static void produce(List<Order> orders, BlockingQueue<Order> out, int workers) throws InterruptedException {
        for (Order order : orders) {
            out.put(order);              // blocks while the queue is full: back-pressure
        }
        for (int i = 0; i < workers; i++) {
            out.put(STOP);               // one STOP per worker, so each one finishes
        }
    }

    static void price(BlockingQueue<Order> inbox, BlockingQueue<Result> outbox, Map<String, Integer> prices)
            throws InterruptedException {
        while (true) {
            Order order = inbox.take();
            if (order == STOP) {
                outbox.put(DONE);
                return;
            }
            outbox.put(new Result(order.id(), prices.get(order.item()) * order.qty()));
        }
    }

    static List<Result> run(List<Order> orders, Map<String, Integer> prices, int workers, int capacity)
            throws InterruptedException {
        BlockingQueue<Order> todo = new ArrayBlockingQueue<>(capacity);
        BlockingQueue<Result> done = new LinkedBlockingQueue<>();
        List<Thread> threads = new ArrayList<>();
        threads.add(Thread.ofPlatform().start(() -> uninterrupted(() -> produce(orders, todo, workers))));
        for (int i = 0; i < workers; i++) {
            threads.add(Thread.ofPlatform().start(() -> uninterrupted(() -> price(todo, done, prices))));
        }
        List<Result> results = new ArrayList<>();
        int stopped = 0;
        while (stopped < workers) {      // collect until every worker has said it is finished
            Result item = done.take();
            if (item == DONE) {
                stopped++;
            } else {
                results.add(item);
            }
        }
        for (Thread t : threads) {
            t.join();
        }
        results.sort(Comparator.comparingInt(Result::id));   // workers finish in any order
        return results;
    }

    interface Blocking {
        void run() throws InterruptedException;
    }

    static void uninterrupted(Blocking work) {
        try {
            work.run();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Map<String, Integer> prices = Map.of("tea", 3, "cake", 5);
        List<Order> orders = new ArrayList<>();
        for (int i = 1; i <= 6; i++) {
            orders.add(new Order(i, i % 2 == 1 ? "tea" : "cake", i));
        }
        for (Result r : run(orders, prices, 2, 3)) {
            System.out.println("order " + r.id() + ": total " + r.total());
        }
    }
}
