package com.amazon.bigmac.metrics.io;

import org.apache.commons.io.FileUtils;

import java.io.IOException;
import java.nio.file.*;
import java.nio.file.attribute.FileAttribute;

/**
 * A convenience class for managing temporary files within a try-with-resources block.
 *
 * <p>
 *     Use case:<br/>
 *     <code>
 *         try (CloseableTempFile closeableTempFile = new CloseableTempFile("test", ".txt")) {
 *             Path tempFile = closeableTempFile.getFile();
 *             // use the temp file
 *         }
 *     </code>
 * </p>
 */
public class CloseableTempFile implements AutoCloseable {

    private final Path file;

    public CloseableTempFile(String prefix, String suffix, FileAttribute<?>... attributes) throws IOException {
        this.file = Files.createTempFile(prefix, suffix, attributes);
    }

    public Path getFile() {
        return file;
    }

    @Override
    public void close() throws Exception {
        // Closing a temp file will actually delete it. The reasoning is that
        // when you close a temp file you have no use for it anymore.
        delete();
    }

    /**
     * Deletes the file.
     *
     * This method is provided for convenience. There's no need to call this when an object of
     * this class is used within a try-with-resources block.
     */
    public void delete() {
        FileUtils.deleteQuietly(file.toFile());
    }
}
