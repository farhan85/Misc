package org.example.workers;

import com.google.common.util.concurrent.Uninterruptibles;
import com.google.inject.Inject;
import com.google.inject.assistedinject.Assisted;
import com.google.inject.name.Named;
import org.example.log.LogWriter;
import org.example.log.LogWriterFactory;

import java.util.Optional;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * This class consumes the messages found on the queue.
 *
 * @param <T> The type of messages to consume from the queue.
 */
public class Consumer<T> implements Runnable {

    private final BlockingQueue<T> queue;
    private final int workTimeMsLower;
    private final int workTimeMsUpper;
    private final LogWriter logWriter;

    @Inject
    Consumer(@Assisted final Integer threadId,
             final BlockingQueue<T> queue,
             @Named("ConsumerWorkTimeMsLower") final int workTimeMsLower,
             @Named("ConsumerWorkTimeMsUpper") final int workTimeMsUpper,
             final LogWriterFactory logWriterFactory) {
        this.queue = checkNotNull(queue);
        this.workTimeMsLower = workTimeMsLower;
        this.workTimeMsUpper = workTimeMsUpper;
        this.logWriter = checkNotNull(logWriterFactory).create("C" + threadId);
    }

    @Override
    public void run() {
        while (!Thread.currentThread().isInterrupted()) {
            getNextMessage().ifPresent(message -> logWriter.write("Consumed message: %s", message));
            simulateWork();
        }
        logWriter.write("Shutting down");
    }

    private Optional<T> getNextMessage() {
        try {
            return Optional.of(queue.take());
        } catch (final InterruptedException e) {
            logWriter.write("Got interrupt signal while waiting for new message");
            Thread.currentThread().interrupt();
            return Optional.empty();
        }
    }

    private void simulateWork() {
        final int timeMs = ThreadLocalRandom.current().nextInt(workTimeMsLower, workTimeMsUpper);
        Uninterruptibles.sleepUninterruptibly(timeMs, TimeUnit.MILLISECONDS);
    }
}
