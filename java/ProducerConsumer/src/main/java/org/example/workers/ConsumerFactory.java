package org.example.workers;

/**
 * Interface for a Consumer factory implemented by Guice.
 */
public interface ConsumerFactory<T> {

    Consumer<T> create(Integer threadId);
}
