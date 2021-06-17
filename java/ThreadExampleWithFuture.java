import com.google.common.util.concurrent.Uninterruptibles;

import java.time.LocalTime;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

public class ThreadExampleWithFuture {

    private final int threadPoolSize;
    private final int maxWaitTimeSeconds;

    public ThreadExampleWithFuture(final int threadPoolSize, final int maxWaitTimeSeconds) {
        this.threadPoolSize = threadPoolSize;
        this.maxWaitTimeSeconds = maxWaitTimeSeconds;
    }

    private List<String> runTest(final Collection<String> testIds) {
        final ExecutorService threadPool = Executors.newFixedThreadPool(threadPoolSize);
        final List<Callable<String>> waitRequests = testIds.stream()
                .map(this::getLongRunningCommandRunnable)
                .collect(Collectors.toList());
        try {
            final List<Future<String>> waiterResults = threadPool.invokeAll(waitRequests);
            threadPool.shutdown();
            return waiterResults.stream()
                    .map(this::getFutureResult)
                    .filter(Optional::isPresent)
                    .map(Optional::get)
                    .collect(Collectors.toList());

        } catch (final InterruptedException e) {
            threadPool.shutdownNow();
            Thread.currentThread().interrupt();
        }
        return Collections.emptyList();
    }

    private Callable<String> getLongRunningCommandRunnable(final String testId) {
        return () -> longRunningCommand(testId);
    }

    private String longRunningCommand(final String testId) {
        final long waitTime = ThreadLocalRandom.current().nextInt(maxWaitTimeSeconds - 1) + 1;
        Uninterruptibles.sleepUninterruptibly(waitTime, TimeUnit.SECONDS);
        return String.format("ID: %s, WaitTime: %d, EndTime: %s", testId, waitTime, LocalTime.now().toString());
    }

    private Optional<String> getFutureResult(final Future<String> future) {
        try {
            return Optional.of(future.get());
        } catch (final ExecutionException e) {
            System.out.println("Could not get result from Future object");
            e.printStackTrace();
        } catch (final InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return Optional.empty();
    }

    public static void main(final String[] args) {
        final ThreadExampleWithFuture threadExample = new ThreadExampleWithFuture(2, 10);
        final List<String> results = threadExample.runTest(Arrays.asList("abc", "def", "xyz", "foo", "bar"));
        System.out.println(results.stream().collect(Collectors.joining("\n")));
    }
}

