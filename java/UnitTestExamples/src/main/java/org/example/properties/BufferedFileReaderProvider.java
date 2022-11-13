package org.example.properties;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.function.Function;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Factory class for creating BufferedReader objects to read from a file.
 *
 * <p>
 * It's okay to not have a unit test for this class. This class creates FileReader instances which
 * will fail if the given file doesn't exist. This class has a single responsibility, which is not
 * about business logic. It's only encapsulating an I/O operation and can be injected/mocked into
 * other classes.
 * </p>
 *
 * <p>
 * When mocking this class for unit tests, a {@code StringReader} can be used instead:
 * </p>
 * <pre>{@code
 *     String contents = "...";
 *     Function<Path, BufferedReader> testReaderProvider = path -> new BufferedReader(new StringReader(contents));
 * }</pre>
 */
public class BufferedFileReaderProvider implements Function<Path, BufferedReader> {

    BufferedFileReaderProvider() {
    }

    @Override
    public BufferedReader apply(final Path filePath) {
        checkNotNull(filePath);
        try {
            return Files.newBufferedReader(filePath);
        } catch (final IOException e) {
            throw new RuntimeException(e);
        }
    }
}
