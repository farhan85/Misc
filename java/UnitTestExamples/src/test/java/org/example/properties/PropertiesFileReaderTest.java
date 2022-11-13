package org.example.properties;

import org.mockito.Mock;
import org.mockito.testng.MockitoTestNGListener;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Listeners;
import org.testng.annotations.Test;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.StringReader;
import java.nio.file.Path;
import java.util.Properties;
import java.util.function.Function;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.testng.Assert.assertEquals;

@Listeners(MockitoTestNGListener.class)
public class PropertiesFileReaderTest {

    private static final Path FILEPATH = Path.of("test-file-name");
    private static final String PROPERTIES_FILE_CONTENTS = "" +
            "key1=value1\n" +
            "key2=value2";

    @Mock
    private Function<Path, BufferedReader> mockReaderProvider;

    private PropertiesFileReader propertiesFileReader;

    @BeforeMethod
    public void setup() {
        when(mockReaderProvider.apply(FILEPATH)).thenReturn(new BufferedReader(new StringReader(PROPERTIES_FILE_CONTENTS)));
        propertiesFileReader = new PropertiesFileReader(mockReaderProvider);
    }

    @Test
    public void GIVEN_filePath_WHEN_calling_apply_THEN_return_properties() {
        final Properties properties = propertiesFileReader.apply(FILEPATH);
        assertEquals(properties.getProperty("key1"), "value1");
        assertEquals(properties.getProperty("key2"), "value2");
    }

    @Test(expectedExceptions = RuntimeException.class)
    public void GIVEN_fileReader_throws_IOException_WHEN_calling_apply_THEN_throw_RuntimeException() throws IOException {
        final BufferedReader mockReader = mock(BufferedReader.class);
        when(mockReaderProvider.apply(FILEPATH)).thenReturn(mockReader);
        doThrow(IOException.class).when(mockReader).read(any(char[].class));

        propertiesFileReader.apply(FILEPATH);
    }
}
