package org.example.log;

import com.google.inject.Inject;
import com.google.inject.name.Named;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.BlockingQueue;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Reads log messages from a queue and prints on screen.
 */
public class DistributedLogReader implements Runnable {

    private final BlockingQueue<LogMessage> logQueue;
    private final int batchSize;
    private final int waitTimeMs;

    @Inject
    DistributedLogReader(final BlockingQueue<LogMessage> logQueue,
                         @Named("LogReaderBatchSize") final int batchSize,
                         @Named("LogReaderWaitTimeMs") final int waitTimeMs) {
        this.logQueue = checkNotNull(logQueue);
        this.batchSize = batchSize;
        this.waitTimeMs = waitTimeMs;
    }

    @Override
    public void run() {
        while (!Thread.currentThread().isInterrupted()) {
            nextBatch().forEach(System.out::println);
            sleep();
        }
        flush();
    }

    private List<String> nextBatch() {
        final List<String> batch = new ArrayList<>();
        while (batch.size() < batchSize) {
            final LogMessage next = logQueue.poll();
            if (next == null) {
                break;
            } else {
                batch.add(next.toString());
            }
        }
        return batch;
    }

    private void sleep() {
        try {
            Thread.sleep(waitTimeMs);
        } catch (final InterruptedException e) {
            System.out.printf("LogReader - %s - Got interrupt signal while sleeping\n", Instant.now());
            Thread.currentThread().interrupt();
        }
    }

    public void flush() {
        logQueue.forEach(System.out::println);
    }
}
