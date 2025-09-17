package com.amazon.bigmac.metrics.io;

import org.junit.Test;

import java.nio.file.*;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;
import static org.hamcrest.Matchers.notNullValue;

/**
 * Unit tests for {@link CloseableTempFile}.
 */
public class CloseableTempFileTest {

    @Test
    public void test_creatingInTryWithResourcesBlock_createsTempFileOnEntryAndDeletesOnExit() throws Exception {
        Path testTempFile;
        try(CloseableTempFile closeableTempFile = new CloseableTempFile("test", ".txt")) {
            testTempFile = closeableTempFile.getFile();

            assertThat(testTempFile, notNullValue());
            assertThat(Files.exists(testTempFile), is(true));
        }

        assertThat(Files.exists(testTempFile), is(false));
    }

    @Test
    public void test_close_deletesTempFile() throws Exception {
        CloseableTempFile closeableTempFile = new CloseableTempFile("test", ".txt");
        closeableTempFile.close();
        assertThat(Files.exists(closeableTempFile.getFile()), is(false));
    }

    @Test
    public void test_delete_deletesTempFile() throws Exception {
        CloseableTempFile closeableTempFile = new CloseableTempFile("test", ".txt");
        closeableTempFile.delete();
        assertThat(Files.exists(closeableTempFile.getFile()), is(false));
    }
}
