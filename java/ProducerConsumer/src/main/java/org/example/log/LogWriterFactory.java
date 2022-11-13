package org.example.log;

/**
 * Interface for a LogWriter factory implemented by Guice.
 */
public interface LogWriterFactory {

    LogWriter create(final String threadId);
}
