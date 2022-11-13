package org.example.workers;

import com.google.common.util.concurrent.Uninterruptibles;
import com.google.inject.Inject;
import com.google.inject.assistedinject.Assisted;
import com.google.inject.name.Named;
import org.example.log.LogWriter;
import org.example.log.LogWriterFactory;

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * This class produces message to be put on the queue.
 *
 * @param <T> The type of messages to produce.
 */
public class Producer<T> implements Runnable {

    private final int workTimeMsLower;
    private final int workTimeMsUpper;
    private final BlockingQueue<T> messageQueue;
    private final Supplier<T> messageGenerator;
    private final LogWriter logWriter;

    @Inject
    Producer(@Assisted final Integer threadId,
             @Named("ProducerWorkTimeMsLower") final int workTimeMsLower,
             @Named("ProducerWorkTimeMsUpper") final int workTimeMsUpper,
             final BlockingQueue<T> messageQueue,
             final Supplier<T> messageGenerator,
             final LogWriterFactory logWriterFactory) {
        this.workTimeMsLower = workTimeMsLower;
        this.workTimeMsUpper = workTimeMsUpper;
        this.messageQueue = checkNotNull(messageQueue);
        this.messageGenerator = checkNotNull(messageGenerator);
        this.logWriter = checkNotNull(logWriterFactory).create("P" + threadId);
    }

    @Override
    public void run() {
        while (!Thread.currentThread().isInterrupted()) {
            simulateWork();
            final T message = messageGenerator.get();
            sendMessage(message);
        }
        logWriter.write("Shutting down");
    }

    private void simulateWork() {
        final int timeMs = ThreadLocalRandom.current().nextInt(workTimeMsLower, workTimeMsUpper);
        Uninterruptibles.sleepUninterruptibly(timeMs, TimeUnit.MILLISECONDS);
    }

    private void sendMessage(final T message) {
        try {
            messageQueue.put(message);
            logWriter.write("Sent message: %s", message);
        } catch (final InterruptedException e) {
            logWriter.write("Got interrupt signal while waiting to send message: %s", message);
            Thread.currentThread().interrupt();
        }
    }
}
