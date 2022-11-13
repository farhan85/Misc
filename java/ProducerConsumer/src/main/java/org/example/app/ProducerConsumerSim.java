package org.example.app;

import com.google.common.util.concurrent.Uninterruptibles;
import com.google.inject.Inject;
import com.google.inject.name.Named;
import org.example.log.DistributedLogReader;
import org.example.workers.ConsumerFactory;
import org.example.workers.ProducerFactory;

import java.time.Duration;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.stream.IntStream;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Simulates the producer-consumer pattern using a blocking queue to control the worker threads.
 */
public class ProducerConsumerSim {

    private static final int SIM_RUN_TIME_S = 10;
    private static final int SHUTDOWN_WAIT_TIME_S = 10;

    private final ProducerFactory<String> producerFactory;
    private final ConsumerFactory<String> consumerFactory;
    private final int numProducers;
    private final int numConsumers;
    private final ExecutorService threadPool;
    private final BlockingQueue<String> messageQueue;
    private final DistributedLogReader logReader;

    @Inject
    ProducerConsumerSim(final ProducerFactory<String> producerFactory,
                        final ConsumerFactory<String> consumerFactory,
                        @Named("NumProducers") final int numProducers,
                        @Named("NumConsumers") final int numConsumers,
                        final ExecutorService threadPool,
                        final BlockingQueue<String> messageQueue,
                        final DistributedLogReader logReader) {
        this.producerFactory = checkNotNull(producerFactory);
        this.consumerFactory = checkNotNull(consumerFactory);
        this.numProducers = numProducers;
        this.numConsumers = numConsumers;
        this.threadPool = checkNotNull(threadPool);
        this.messageQueue = checkNotNull(messageQueue);
        this.logReader = checkNotNull(logReader);
    }

    public void run() {
        IntStream.range(1, numProducers + 1)
                .mapToObj(producerFactory::create)
                .forEach(threadPool::execute);
        IntStream.range(1, numConsumers + 1)
                .mapToObj(consumerFactory::create)
                .forEach(threadPool::execute);
        threadPool.execute(logReader);
        threadPool.shutdown();

        Uninterruptibles.sleepUninterruptibly(Duration.ofSeconds(SIM_RUN_TIME_S));
        stopThreads(threadPool);
        logReader.flush();
        System.out.println("Messages still in queue after shutdown: " + messageQueue.stream().toList());
    }

    private void stopThreads(final ExecutorService threadPool) {
        threadPool.shutdownNow();
        try {
            if (!threadPool.awaitTermination(SHUTDOWN_WAIT_TIME_S, TimeUnit.SECONDS)) {
                throw new RuntimeException("ThreadPool still did not terminate in time");
            }
        } catch (final InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
