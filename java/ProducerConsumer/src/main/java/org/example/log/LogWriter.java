package org.example.log;

/**
 * Interface for objects that can write logs to some destination.
 */
public interface LogWriter {

    void write(final String formatString, final Object... args);

    void write(final String message);
}
