// A hash table from scratch: buckets, a hash function, collisions, and resizing.
//
//     java HashTable.java
//
// The same program as ../hash_table.py: separate chaining, FNV-1a, doubling at a load factor of
// 0.75 (also the default of Java's own HashMap). Two things are different in Java, and worth seeing:
//
// 1. FNV-1a needs no "& 0xFFFFFFFF". A Java int is exactly 32 bits and multiplication wraps around,
//    so the overflow IS the modulo 2^32. But an int is signed, so a hash can be negative, and
//    -7 % 8 is -7 in Java: Integer.remainderUnsigned treats the bits as unsigned, as Python does.
// 2. Java's own String.hashCode() is the same on every run (s[0]*31^(n-1) + ... + s[n-1]), where
//    Python salts str hashes each time it starts. So Java could use it here, and the demo shows it.
//    Java's HashMap also turns a bucket of 8 or more entries into a small tree (TREEIFY_THRESHOLD in
//    the JDK source), so even the bad-hash case below stays O(log n) there, not O(n).

import java.util.ArrayList;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.function.ToIntFunction;

public class HashTable<K, V> {

    /** FNV-1a, 32-bit: start from an offset, then for each byte XOR it in and multiply by a prime. */
    static int fnv1a(String key) {
        int h = 0x811C9DC5;
        for (byte b : key.getBytes(java.nio.charset.StandardCharsets.UTF_8)) {
            h ^= (b & 0xFF);                  // & 0xFF: a Java byte is signed, -128..127
            h *= 0x01000193;                  // wraps at 32 bits by itself
        }
        return h;
    }

    record Entry<K, V>(K key, V value) {}

    record Got<V>(V value, int comparisons) {}

    List<List<Entry<K, V>>> buckets;
    final ToIntFunction<K> hashFn;
    final double maxLoad;
    int size = 0;
    int resizes = 0;

    HashTable(int buckets, ToIntFunction<K> hashFn, double maxLoad) {
        this.buckets = emptyBuckets(buckets);
        this.hashFn = hashFn;
        this.maxLoad = maxLoad;
    }

    HashTable(ToIntFunction<K> hashFn) {
        this(8, hashFn, 0.75);
    }

    static <K, V> List<List<Entry<K, V>>> emptyBuckets(int n) {
        List<List<Entry<K, V>>> list = new ArrayList<>(n);
        for (int i = 0; i < n; i++) list.add(new ArrayList<>());
        return list;
    }

    List<Entry<K, V>> bucket(K key) {
        return buckets.get(Integer.remainderUnsigned(hashFn.applyAsInt(key), buckets.size()));
    }

    void put(K key, V value) {
        List<Entry<K, V>> bucket = bucket(key);
        for (int i = 0; i < bucket.size(); i++) {
            if (bucket.get(i).key().equals(key)) {
                bucket.set(i, new Entry<>(key, value));      // replace an existing key
                return;
            }
        }
        bucket.add(new Entry<>(key, value));
        size++;
        if ((double) size / buckets.size() > maxLoad) {
            resize();
        }
    }

    /** Returns the value and how many comparisons it took. Throws if the key is absent. */
    Got<V> get(K key) {
        int steps = 0;
        for (Entry<K, V> e : bucket(key)) {
            steps++;
            if (e.key().equals(key)) {
                return new Got<>(e.value(), steps);
            }
        }
        throw new NoSuchElementException(String.valueOf(key));
    }

    void resize() {
        List<Entry<K, V>> old = new ArrayList<>();
        buckets.forEach(old::addAll);
        buckets = emptyBuckets(buckets.size() * 2);
        size = 0;
        resizes++;
        for (Entry<K, V> e : old) {
            put(e.key(), e.value());
        }
    }

    int longestBucket() {
        return buckets.stream().mapToInt(List::size).max().orElse(0);
    }

    static HashTable<String, Integer> fill(int n, ToIntFunction<String> hashFn) {
        HashTable<String, Integer> t = new HashTable<>(hashFn);
        for (int i = 0; i < n; i++) {
            t.put("user-" + i, i);
        }
        return t;
    }

    static int badHash(String key) {
        return 42;                            // every key collides
    }

    static String report(String label, HashTable<String, Integer> t) {
        return String.format("%-15s: 1000 keys, %d buckets after %d resizes, longest bucket %d, get('user-999') took %d comparisons",
                label, t.buckets.size(), t.resizes, t.longestBucket(), t.get("user-999").comparisons());
    }

    public static void main(String[] args) {
        System.out.println(report("FNV-1a", fill(1000, HashTable::fnv1a)));
        System.out.println(report("String.hashCode", fill(1000, String::hashCode)));
        System.out.println(report("bad hash", fill(1000, HashTable::badHash)));
        System.out.println("\"user-999\".hashCode() = " + "user-999".hashCode() + " on every run, on every JVM");
    }
}
