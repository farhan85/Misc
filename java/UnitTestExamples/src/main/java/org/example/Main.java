package org.example;

import com.google.inject.Guice;
import com.google.inject.Injector;
import org.example.app.ConfigPropertiesDisplay;
import org.example.guice.PropertiesModule;

/**
 * Runs a ConfigPropertiesDisplay application.
 *
 * Instead of unit testing a class that creates a Guice injector, have this class use
 * the injector to create only one object, and call only one method on this object. That
 * one object should have its own unit tests, and you don't need to write unit tests for
 * this class, which has only one single responsibility - run one method on one object.
 */
public class Main {

    public static void main(final String[] args) {
        final Injector injector = Guice.createInjector(new PropertiesModule());
        final ConfigPropertiesDisplay app = injector.getInstance(ConfigPropertiesDisplay.class);
        app.run();
    }
}
