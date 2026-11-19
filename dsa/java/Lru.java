// An LRU (least recently used) cache from scratch: a HashMap for O(1) lookup, plus a doubly linked
// list that keeps items in order of use. Then the same cache in five lines with LinkedHashMap.
//
//     java Lru.java
//
// The same program as ../lru.py.
//
//   get(key)   look it up in the map; move its node to the front (most recently used)
//   put(key)   add a node at the front; if over capacity, remove the node at the back
//              (least recently used) from both the list and the map
//
// Java's standard library already has this pair of structures in one class: a LinkedHashMap
// built with accessOrder = true keeps entries in order of use, and overriding removeEldestEntry
// evicts the oldest. BuiltIn below is that version; the tests check both evict the same keys.

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class Lru<K, V> {

    static final class Node<K, V> {
        K key;
        V value;
        Node<K, V> prev, next;

        Node(K key, V value) {
            this.key = key;
            this.value = value;
        }
    }

    final int capacity;
    final Map<K, Node<K, V>> map = new HashMap<>();
    final Node<K, V> head = new Node<>(null, null), tail = new Node<>(null, null);   // sentinels
    final List<K> evicted = new ArrayList<>();

    Lru(int capacity) {
        if (capacity < 1) {
            throw new IllegalArgumentException("capacity must be at least 1");
        }
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    void unlink(Node<K, V> node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    void pushFront(Node<K, V> node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }

    V get(K key) {
        Node<K, V> node = map.get(key);
        if (node == null) {
            return null;
        }
        unlink(node);
        pushFront(node);
        return node.value;
    }

    void put(K key, V value) {
        Node<K, V> node = map.get(key);
        if (node != null) {
            node.value = value;
            unlink(node);
        } else {
            node = new Node<>(key, value);
            map.put(key, node);
            if (map.size() > capacity) {
                Node<K, V> oldest = tail.prev;
                unlink(oldest);
                map.remove(oldest.key);
                evicted.add(oldest.key);
            }
        }
        pushFront(node);
    }

    /** Keys from most to least recently used. */
    List<K> order() {
        List<K> out = new ArrayList<>();
        for (Node<K, V> n = head.next; n != tail; n = n.next) {
            out.add(n.key);
        }
        return out;
    }

    /** The same cache, from the standard library. (LinkedHashMap is Serializable; this demo never serializes it.) */
    @SuppressWarnings("serial")
    static final class BuiltIn<K, V> extends LinkedHashMap<K, V> {
        final int capacity;
        final List<K> evicted = new ArrayList<>();

        BuiltIn(int capacity) {
            super(16, 0.75f, true);                // true = access order, not insertion order
            this.capacity = capacity;
        }

        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            boolean full = size() > capacity;
            if (full) {
                evicted.add(eldest.getKey());
            }
            return full;
        }
    }

    public static void main(String[] args) {
        Lru<String, String> c = new Lru<>(3);
        for (String step : List.of("put a", "put b", "put c", "get a", "put d", "get b", "put e")) {
            String[] parts = step.split(" ");
            String shown = "";
            if (parts[0].equals("put")) {
                c.put(parts[1], parts[1].toUpperCase());
            } else {
                shown = " -> " + c.get(parts[1]);
            }
            System.out.printf("%-6s%-8s order (newest first): %s  evicted so far: %s%n", step, shown, c.order(), c.evicted);
        }
    }
}
