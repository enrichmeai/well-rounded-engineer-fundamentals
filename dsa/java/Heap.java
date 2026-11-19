// A binary min-heap from scratch: the structure behind priority queues.
//
//     java Heap.java
//
// The same program as ../heap.py. The heap is an array read as a tree: the children of index i are
// at 2i+1 and 2i+2, and every parent is <= its children, so the smallest item is always at index 0.
//
//   push   add at the end, then swap upwards while smaller than the parent      O(log n)
//   pop    take index 0, move the last item to the top, swap it downwards       O(log n)
//
// Java's java.util.PriorityQueue is this same structure; the tests check both give the same order.
//
// The Java difference: Python compares (priority, name) tuples by itself. Java has to be told how
// to order things, so the heap takes any T that is Comparable, and Job says how Jobs compare.

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.NoSuchElementException;

public class Heap<T extends Comparable<? super T>> {

    final List<T> items = new ArrayList<>();

    void push(T item) {
        items.add(item);
        int i = items.size() - 1;
        while (i > 0) {
            int parent = (i - 1) / 2;
            if (items.get(i).compareTo(items.get(parent)) < 0) {
                swap(i, parent);
                i = parent;
            } else {
                break;
            }
        }
    }

    T pop() {
        if (items.isEmpty()) {
            throw new NoSuchElementException("pop from an empty heap");
        }
        T smallest = items.get(0);
        T last = items.remove(items.size() - 1);
        if (!items.isEmpty()) {
            items.set(0, last);
            int i = 0;
            while (true) {
                int left = 2 * i + 1, right = 2 * i + 2, small = i;
                if (left < items.size() && items.get(left).compareTo(items.get(small)) < 0) small = left;
                if (right < items.size() && items.get(right).compareTo(items.get(small)) < 0) small = right;
                if (small == i) break;
                swap(i, small);
                i = small;
            }
        }
        return smallest;
    }

    int size() {
        return items.size();
    }

    void swap(int a, int b) {
        T t = items.get(a);
        items.set(a, items.get(b));
        items.set(b, t);
    }

    /** Keep a heap of the k largest seen so far: O(n log k), not a full sort. */
    static List<Integer> topKLargest(List<Integer> values, int k) {
        Heap<Integer> h = new Heap<>();
        for (int v : values) {
            h.push(v);
            if (h.size() > k) {
                h.pop();                   // drop the smallest of the k + 1
            }
        }
        List<Integer> out = new ArrayList<>(h.items);
        out.sort(Comparator.reverseOrder());
        return out;
    }

    /** A job ordered like Python's (priority, name) tuple: by priority, then by name. */
    record Job(int priority, String name) implements Comparable<Job> {
        static final Comparator<Job> ORDER = Comparator.comparingInt(Job::priority).thenComparing(Job::name);

        public int compareTo(Job other) {
            return ORDER.compare(this, other);
        }

        @Override
        public String toString() {
            return "(" + priority + ", '" + name + "')";
        }
    }

    public static void main(String[] args) {
        Heap<Job> h = new Heap<>();
        List<Job> jobs = List.of(new Job(3, "send report"), new Job(1, "page on-call"), new Job(2, "retry payment"),
                new Job(5, "tidy logs"), new Job(1, "restart db"));
        for (Job job : jobs) {
            h.push(job);
            System.out.printf("push %-22s heap as a list: %s%n", job, h.items.stream().map(Job::priority).toList());
        }
        List<Job> order = new ArrayList<>();
        while (h.size() > 0) order.add(h.pop());
        System.out.println("pop order: " + order);
        System.out.println("top 3 of [7, 2, 9, 4, 11, 5]: " + topKLargest(List.of(7, 2, 9, 4, 11, 5), 3));
    }
}
