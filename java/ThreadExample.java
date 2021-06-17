import com.google.common.util.concurrent.Uninterruptibles;

import java.time.LocalTime;
import java.util.Arrays;
import java.util.Collection;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;

public class ThreadExample {

    private final int threadPoolSize;
    private final int maxWaitTimeSeconds;

    public ThreadExample(final int threadPoolSize, final int maxWaitTimeSeconds) {
        this.threadPoolSize = threadPoolSize;
        this.maxWaitTimeSeconds = maxWaitTimeSeconds;
    }

    private void runTest(final Collection<String> testIds) {
        final ExecutorService threadPool = Executors.newFixedThreadPool(threadPoolSize);
        testIds.forEach(testId -> threadPool.execute(() -> longRunningCommand(testId)));

        try {
            threadPool.shutdown();
            threadPool.awaitTermination(10, TimeUnit.MINUTES);
        } catch (final InterruptedException e) {
            throw new RuntimeException("Thread pool did not terminate", e);
        }
    }

    private void longRunningCommand(final String testId) {
        final long waitTime = ThreadLocalRandom.current().nextInt(maxWaitTimeSeconds - 1) + 1;
        Uninterruptibles.sleepUninterruptibly(waitTime, TimeUnit.SECONDS);
        System.out.println(String.format("ID: %s, WaitTime: %d, EndTime: %s", testId, waitTime, LocalTime.now().toString()));
    }

    public static void main(final String[] args) {
        final ThreadExample threadExample = new ThreadExample(2, 10);
        threadExample.runTest(Arrays.asList("abc", "def", "xyz", "foo", "bar"));
    }
}

