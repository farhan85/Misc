package org.example.log;

import java.time.Instant;
import java.util.Objects;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * An object sent to a {@link LogWriter} containing a message to be logged.
 *
 * @param threadId  An identifier of the thread that created this LogMessage.
 * @param timestamp The timestamp at when the LogMessage was created.
 * @param message   The log message.
 */
public record LogMessage(String threadId, Instant timestamp, String message) implements Comparable<LogMessage> {

    public LogMessage {
        checkNotNull(threadId);
        checkNotNull(timestamp);
        checkNotNull(message);
    }

    public String toString() {
        return String.format("%s - %s - %s", threadId, timestamp, message);
    }

    @Override
    public int compareTo(final LogMessage other) {
        return this.timestamp.compareTo(other.timestamp);
    }

    @Override
    public boolean equals(final Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }
        final LogMessage that = (LogMessage) o;
        return Objects.equals(threadId, that.threadId)
                && Objects.equals(timestamp, that.timestamp)
                && Objects.equals(message, that.message);
    }

    @Override
    public int hashCode() {
        return Objects.hash(threadId, timestamp, message);
    }
}
