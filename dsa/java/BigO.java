// Big O, counted instead of timed: how the number of steps grows with the input.
//
//     java BigO.java
//
// The same program as ../big_o.py, printing the same table. Each method returns how many
// comparisons it made, so you can see the growth directly:
//
//   linear search      O(n)        look at each item until you find it
//   binary search      O(log n)    halve a SORTED array each time
//   duplicates, nested O(n^2)      compare every pair
//   duplicates, set    O(n)        remember what you have seen in a HashSet
//
// Java has no tuples, so each method returns a small record: (answer, steps).

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class BigO {

    record Found(int index, long steps) {}

    record Answer(boolean yes, long steps) {}

    static Found linearSearch(int[] items, int target) {
        long steps = 0;
        for (int i = 0; i < items.length; i++) {
            steps++;
            if (items[i] == target) {
                return new Found(i, steps);
            }
        }
        return new Found(-1, steps);
    }

    /** The array must be sorted. */
    static Found binarySearch(int[] sorted, int target) {
        int lo = 0, hi = sorted.length - 1;
        long steps = 0;
        while (lo <= hi) {
            int mid = (lo + hi) >>> 1;          // >>> 1, not / 2: no overflow when lo + hi passes 2^31
            steps++;
            if (sorted[mid] == target) {
                return new Found(mid, steps);
            }
            if (sorted[mid] < target) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        return new Found(-1, steps);
    }

    static Answer hasDuplicateNested(int[] items) {
        long steps = 0;
        for (int i = 0; i < items.length; i++) {
            for (int j = i + 1; j < items.length; j++) {
                steps++;
                if (items[i] == items[j]) {
                    return new Answer(true, steps);
                }
            }
        }
        return new Answer(false, steps);
    }

    static Answer hasDuplicateSet(int[] items) {
        Set<Integer> seen = new HashSet<>();
        long steps = 0;
        for (int item : items) {
            steps++;                            // one hash-set lookup (average O(1)) per item
            if (!seen.add(item)) {              // add() returns false if it was already there
                return new Answer(true, steps);
            }
        }
        return new Answer(false, steps);
    }

    record Row(int n, long linear, long binary, long nested, long set) {}

    static List<Row> table(int... sizes) {
        List<Row> rows = new ArrayList<>();
        for (int n : sizes) {
            int[] items = new int[n];
            for (int i = 0; i < n; i++) items[i] = i;   // sorted, no duplicates: the worst case
            int missing = n;                            // a value that is not there
            rows.add(new Row(n, linearSearch(items, missing).steps(), binarySearch(items, missing).steps(),
                    hasDuplicateNested(items).steps(), hasDuplicateSet(items).steps()));
        }
        return rows;
    }

    public static void main(String[] args) {
        List<Row> rows = table(10, 100, 1_000, 10_000);
        System.out.printf("%9s %9s %7s %12s %8s%n", "n", "linear", "binary", "nested dup", "set dup");
        for (Row r : rows) {
            System.out.printf("%9d %9d %7d %12d %8d%n", r.n(), r.linear(), r.binary(), r.nested(), r.set());
        }
        Row first = rows.get(0), last = rows.get(rows.size() - 1);
        System.out.printf("%nn grew %,d times. Steps grew: linear %,.0fx, binary %,.1fx, nested %,.0fx, set %,.0fx.%n",
                last.n() / first.n(), (double) last.linear() / first.linear(), (double) last.binary() / first.binary(),
                (double) last.nested() / first.nested(), (double) last.set() / first.set());
    }
}
