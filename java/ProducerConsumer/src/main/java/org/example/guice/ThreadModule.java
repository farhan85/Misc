package org.example.guice;

import com.google.inject.AbstractModule;
import com.google.inject.Provides;
import com.google.inject.Singleton;
import com.google.inject.TypeLiteral;
import com.google.inject.assistedinject.FactoryModuleBuilder;
import com.google.inject.name.Named;
import org.example.log.DistributedLogWriter;
import org.example.log.LogMessage;
import org.example.log.LogWriter;
import org.example.log.LogWriterFactory;
import org.example.message.SequenceGenerator;
import org.example.workers.ConsumerFactory;
import org.example.workers.ProducerFactory;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.PriorityBlockingQueue;
import java.util.function.Supplier;

public class ThreadModule extends AbstractModule {

    private final TypeLiteral<Supplier<String>> MESSAGE_SUPPLIER_TYPE = new TypeLiteral<>() {};
    private final TypeLiteral<ProducerFactory<String>> STRING_PRODUCER_FACTORY_TYPE = new TypeLiteral<>() {};
    private final TypeLiteral<ConsumerFactory<String>> STRING_CONSUMER_FACTORY_TYPE = new TypeLiteral<>() {};

    @Override
    protected void configure() {
        bind(MESSAGE_SUPPLIER_TYPE)
                .to(SequenceGenerator.class)
                .in(Singleton.class);
        install(new FactoryModuleBuilder().build(STRING_PRODUCER_FACTORY_TYPE));
        install(new FactoryModuleBuilder().build(STRING_CONSUMER_FACTORY_TYPE));
        install(new FactoryModuleBuilder()
                .implement(LogWriter.class, DistributedLogWriter.class)
                .build(LogWriterFactory.class));
    }

    @Provides
    @Singleton
    public BlockingQueue<String> provideQueue(@Named("MessageQueueSize") final int queueSize) {
        return new ArrayBlockingQueue<>(queueSize);
    }

    @Provides
    @Singleton
    public BlockingQueue<LogMessage> provideLogQueue(@Named("LogQueueSize") final int queueSize) {
        return new PriorityBlockingQueue<>(queueSize);
    }

    @Provides
    public ExecutorService provideProducerPool(@Named("NumProducers") final int numProducers,
                                               @Named("NumConsumers") final int numConsumers) {
        // Capacity required for threads: Producers + Consumers + LogReader
        return Executors.newFixedThreadPool(numProducers + numConsumers + 1);
    }
}
