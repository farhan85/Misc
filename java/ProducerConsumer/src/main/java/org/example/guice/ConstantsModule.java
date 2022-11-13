package org.example.guice;

import com.google.inject.AbstractModule;
import com.google.inject.name.Names;

import java.time.Clock;

public class ConstantsModule extends AbstractModule {

    @Override
    protected void configure() {
        bind(Clock.class).toInstance(Clock.systemUTC());
        bind(Integer.class).annotatedWith(Names.named("NumProducers")).toInstance(4);
        bind(Integer.class).annotatedWith(Names.named("NumConsumers")).toInstance(2);
        bind(Integer.class).annotatedWith(Names.named("ProducerWorkTimeMsLower")).toInstance(1000);
        bind(Integer.class).annotatedWith(Names.named("ProducerWorkTimeMsUpper")).toInstance(5000);
        bind(Integer.class).annotatedWith(Names.named("ConsumerWorkTimeMsLower")).toInstance(5000);
        bind(Integer.class).annotatedWith(Names.named("ConsumerWorkTimeMsUpper")).toInstance(7000);
        bind(Integer.class).annotatedWith(Names.named("MessageQueueSize")).toInstance(3);
        bind(Integer.class).annotatedWith(Names.named("LogQueueSize")).toInstance(50);
        bind(Integer.class).annotatedWith(Names.named("LogReaderBatchSize")).toInstance(5);
        bind(Integer.class).annotatedWith(Names.named("LogReaderWaitTimeMs")).toInstance(1000);
    }
}
