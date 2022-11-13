package org.example.app;

import com.google.inject.Inject;
import com.google.inject.Provider;
import com.google.inject.name.Named;

import java.util.Properties;

import static java.util.Objects.requireNonNull;

/**
 * Example of using Guice to build the objects needed to read the config properties file.
 *
 * Since reading the properties file is an I/O operation, we'll ask Guice for a Provider object
 * which allows us to read the file only when needed.
 */
public class ConfigPropertiesDisplay implements Runnable {

    private final Provider<Properties> propertiesProvider;

    @Inject
    ConfigPropertiesDisplay(@Named("ConfigProperties") final Provider<Properties> propertiesProvider) {
        this.propertiesProvider = requireNonNull(propertiesProvider);
    }

    @Override
    public void run() {
        final Properties properties = propertiesProvider.get();
        System.out.println(properties.getProperty("name"));
    }
}
