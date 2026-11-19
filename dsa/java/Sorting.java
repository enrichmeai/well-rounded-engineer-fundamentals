// Sorting, counted: insertion sort is O(n^2), merge sort is O(n log n).
//
//     java Sorting.java
//
// The same program as ../sorting.py. Both methods return the sorted array and the number of
// comparisons they made. Java's own List.sort (and Arrays.sort for objects) uses TimSort, which the
// JDK documentation says "was adapted from Tim Peters's list sort for Python": the same algorithm as
// Python's sorted(). (Arrays.sort on an int[] uses a dual-pivot quicksort instead.)
//
// The counts differ a little from the Python version because java.util.Random(42) is a different
// generator from Python's random.Random(42), so the "random" arrays are different. The growth is
// the same: that is the point.

import java.util.Arrays;
import java.util.Random;

public class Sorting {

    record Sorted(int[] items, long comparisons) {}

    static Sorted insertionSort(int[] input) {
        int[] out = input.clone();
        long steps = 0;
        for (int i = 1; i < out.length; i++) {
            for (int j = i; j > 0; j--) {
                steps++;
                if (out[j - 1] <= out[j]) {
                    break;
                }
                int t = out[j - 1];
                out[j - 1] = out[j];
                out[j] = t;
            }
        }
        return new Sorted(out, steps);
    }

    static Sorted mergeSort(int[] input) {
        if (input.length <= 1) {
            return new Sorted(input.clone(), 0);
        }
        int mid = input.length / 2;
        Sorted left = mergeSort(Arrays.copyOfRange(input, 0, mid));
        Sorted right = mergeSort(Arrays.copyOfRange(input, mid, input.length));
        int[] merged = new int[input.length];
        int i = 0, j = 0, k = 0;
        long steps = left.comparisons() + right.comparisons();
        while (i < left.items().length && j < right.items().length) {
            steps++;
            if (left.items()[i] <= right.items()[j]) {
                merged[k++] = left.items()[i++];
            } else {
                merged[k++] = right.items()[j++];
            }
        }
        while (i < left.items().length) merged[k++] = left.items()[i++];
        while (j < right.items().length) merged[k++] = right.items()[j++];
        return new Sorted(merged, steps);
    }

    public static void main(String[] args) {
        Random rng = new Random(42);              // fixed seed: the same "random" arrays every run
        System.out.printf("%6s %11s %8s%n", "n", "insertion", "merge");
        for (int n : new int[] {10, 100, 1000, 4000}) {
            int[] data = new int[n];
            for (int i = 0; i < n; i++) data[i] = rng.nextInt(1_000_001);   // 0 to 10^6, like randint
            System.out.printf("%6d %11d %8d%n", n, insertionSort(data).comparisons(), mergeSort(data).comparisons());
        }
    }
}
