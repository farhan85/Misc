package org.example.log;

import com.google.inject.Inject;
import com.google.inject.assistedinject.Assisted;

import java.time.Clock;
import java.util.concurrent.BlockingQueue;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Allows multiple threads to write logs that needs to be sent to a single destination.
 */
public class DistributedLogWriter implements LogWriter {

    private final Clock clock;
    private final String threadId;
    private final BlockingQueue<LogMessage> logQueue;

    @Inject
    DistributedLogWriter(final Clock clock,
                         @Assisted final String threadId,
                         final BlockingQueue<LogMessage> logQueue) {
        this.clock = checkNotNull(clock);
        this.threadId = checkNotNull(threadId);
        this.logQueue = checkNotNull(logQueue);
    }

    @Override
    public void write(final String formatString, final Object... args) {
        write(String.format(formatString, args));
    }

    @Override
    public void write(final String message) {
        try {
            logQueue.put(new LogMessage(threadId, clock.instant(), message));
        } catch (final InterruptedException ignored) {
        }
    }
}
