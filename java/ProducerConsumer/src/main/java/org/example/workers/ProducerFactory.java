package org.example.workers;

/**
 * Interface for a Producer factory implemented by Guice.
 */
public interface ProducerFactory<T> {

    Producer<T> create(Integer threadId);
}
