// Amdahl's law: how much faster can more processors make a job?
//
//     java Amdahl.java            # the table for a job that is 90% parallel
//     java Amdahl.java 0.5        # try a job that is only half parallel
//
// The same program as ../amdahl.py. If a fraction p of the work can run in parallel on s
// processors, and the rest must run one step at a time, the speed-up is
//
//     1 / ((1 - p) + p / s)
//
// The serial part sets a ceiling: however many processors you add, the speed-up never passes
// 1 / (1 - p). For p = 0.9 that ceiling is 10. The law is the same in every language.

public class Amdahl {

    static double speedup(double p, double s) {
        if (p < 0 || p > 1) {
            throw new IllegalArgumentException("p is a fraction between 0 and 1");
        }
        if (s < 1) {
            throw new IllegalArgumentException("s is a number of processors, at least 1");
        }
        return 1 / ((1 - p) + p / s);
    }

    static double ceiling(double p) {
        return p == 1 ? Double.POSITIVE_INFINITY : 1 / (1 - p);
    }

    public static void main(String[] args) {
        double p = args.length > 0 ? Double.parseDouble(args[0]) : 0.9;
        System.out.printf("p = %.0f%% parallel%n", p * 100);
        for (int s : new int[] {1, 2, 4, 8, 16, 64, 1024}) {
            System.out.printf("  %5d processors: %6.2fx%n", s, speedup(p, s));
        }
        System.out.printf("  ceiling          : %6.2fx%n", ceiling(p));
    }
}
