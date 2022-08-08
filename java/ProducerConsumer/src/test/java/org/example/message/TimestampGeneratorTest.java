package org.example.message;

import org.mockito.Mock;
import org.mockito.testng.MockitoTestNGListener;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Listeners;
import org.testng.annotations.Test;

import java.time.Clock;
import java.time.Instant;

import static org.mockito.Mockito.when;
import static org.testng.Assert.assertEquals;

@Listeners(MockitoTestNGListener.class)
public class TimestampGeneratorTest {

    private static final Instant INSTANT = Instant.parse("2022-02-01T01:02:03.123456Z");

    @Mock
    private Clock mockClock;

    private TimestampGenerator timestampGenerator;

    @BeforeMethod
    public void setup() {
        timestampGenerator = new TimestampGenerator(mockClock);
    }

    @Test(expectedExceptions = NullPointerException.class)
    public void GIVEN_null_parameters_WHEN_calling_constructor_THEN_throw_exception() {
        new TimestampGenerator(null);
    }

    @Test
    public void GIVEN_sequenceGenerator_WHEN_calling_get_THEN_return_timestamp_in_messages() {
        when(mockClock.instant()).thenReturn(INSTANT);
        assertEquals(timestampGenerator.get(), "01:02:03.123456Z");
    }
}
