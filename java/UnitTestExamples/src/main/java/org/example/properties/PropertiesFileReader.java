package org.example.properties;

import com.google.inject.Inject;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Properties;
import java.util.function.Function;

import static java.util.Objects.requireNonNull;

/**
 * Reads a given properties file into a Properties object.
 */
public class PropertiesFileReader implements Function<Path, Properties> {

    private final Function<Path, BufferedReader> readerProvider;

    @Inject
    PropertiesFileReader(final Function<Path, BufferedReader> readerProvider) {
        this.readerProvider = requireNonNull(readerProvider);
    }

    @Override
    public Properties apply(final Path filePath) {
        try (final BufferedReader reader = readerProvider.apply(filePath)) {
            final Properties props = new Properties();
            props.load(reader);
            return props;
        } catch (final IOException e) {
            throw new RuntimeException("Error reading file: " + filePath, e);
        }
    }
}
