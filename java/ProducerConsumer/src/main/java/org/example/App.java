package org.example;

import com.google.inject.Guice;
import com.google.inject.Injector;
import org.example.app.ProducerConsumerSim;
import org.example.guice.ConstantsModule;
import org.example.guice.ThreadModule;

/**
 * Hello world!
 */
public class App {

    public static void main(final String[] args) {
        final Injector injector = Guice.createInjector(new ConstantsModule(), new ThreadModule());
        final ProducerConsumerSim app = injector.getInstance(ProducerConsumerSim.class);
        app.run();
    }
}
