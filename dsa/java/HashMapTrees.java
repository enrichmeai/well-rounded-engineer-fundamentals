// What Java's own HashMap does when every key has the same hash, and why Comparable rescues it.
//
//     java HashMapTrees.java
//
// HashTable.java showed that a hash function sending every key to one bucket turns each lookup
// into a linear search. java.util.HashMap defends against that: when one bucket holds 8 or more
// entries (TREEIFY_THRESHOLD in the JDK source) and the table has at least 64 buckets, the bucket
// becomes a small red-black tree. A tree can only be searched quickly if keys can be ORDERED, so:
//
//   keys with a good hashCode                    short buckets, O(1) on average
//   keys that all hash to 42, but are Comparable  one tree, searched in O(log n)
//   keys that all hash to 42, not Comparable      one tree that cannot be searched by order: O(n)
//
// There is no Python equivalent: a Python dict with one hash for every key is simply slow.
// The lesson for your own classes: write a hashCode() that spreads keys out, and if the class has
// a natural order, implement Comparable too. Timings depend on your machine: compare the rows.

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class HashMapTrees {

    record Good(int id) {}                                   // a record's hashCode uses its fields

    record SameHashOrdered(int id) implements Comparable<SameHashOrdered> {
        @Override
        public int hashCode() {
            return 42;
        }

        public int compareTo(SameHashOrdered other) {
            return Integer.compare(id, other.id);
        }
    }

    record SameHash(int id) {
        @Override
        public int hashCode() {
            return 42;
        }
    }

    /** Put every key in a HashMap, then look each one up once. Returns milliseconds for the lookups. */
    static <K> double lookupMillis(List<K> keys) {
        Map<K, Integer> map = new HashMap<>();
        for (K k : keys) {
            map.put(k, 1);
        }
        long start = System.nanoTime();
        int found = 0;
        for (K k : keys) {
            if (map.containsKey(k)) found++;
        }
        if (found != keys.size()) {
            throw new IllegalStateException("lost a key");
        }
        return (System.nanoTime() - start) / 1e6;
    }

    public static void main(String[] args) {
        int n = 5_000;
        List<Good> good = new ArrayList<>();
        List<SameHashOrdered> ordered = new ArrayList<>();
        List<SameHash> plain = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            good.add(new Good(i));
            ordered.add(new SameHashOrdered(i));
            plain.add(new SameHash(i));
        }
        lookupMillis(good);                                  // warm up the JIT once
        System.out.printf("%,d lookups in a HashMap of %,d keys%n", n, n);
        System.out.printf("  good hashCode                     : %8.1f ms%n", lookupMillis(good));
        System.out.printf("  every hash 42, keys Comparable    : %8.1f ms%n", lookupMillis(ordered));
        System.out.printf("  every hash 42, keys not Comparable: %8.1f ms%n", lookupMillis(plain));
    }
}
