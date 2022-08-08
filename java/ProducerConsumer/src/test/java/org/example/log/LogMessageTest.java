package org.example.log;

import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import java.time.Instant;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertFalse;
import static org.testng.Assert.assertThrows;
import static org.testng.AssertJUnit.assertTrue;

public class LogMessageTest {

    private static final String THREAD_ID = "thread_1";
    private static final String TIMESTAMP = "2022-02-01T01:02:03.123456Z";
    private static final Instant INSTANT = Instant.parse(TIMESTAMP);
    private static final String MESSAGE = "test_message";

    private LogMessage logMessage;

    @BeforeMethod
    public void setup() {
        logMessage = new LogMessage(THREAD_ID, INSTANT, MESSAGE);
    }

    @Test
    public void GIVEN_null_parameters_WHEN_calling_constructor_THEN_throw_exception() {
        assertThrows(NullPointerException.class, () -> new LogMessage(null, INSTANT, MESSAGE));
        assertThrows(NullPointerException.class, () -> new LogMessage(THREAD_ID, null, MESSAGE));
        assertThrows(NullPointerException.class, () -> new LogMessage(THREAD_ID, INSTANT, null));
    }

    @Test
    public void GIVEN_logMessage_WHEN_calling_getters_THEN_return_expected_values() {
        assertEquals(logMessage.threadId(), THREAD_ID);
        assertEquals(logMessage.timestamp(), INSTANT);
        assertEquals(logMessage.message(), MESSAGE);
    }

    @Test
    public void GIVEN_threadId_timestamp_message_WHEN_calling_toString_THEN_return_expected_string() {
        final String expectedString = String.format("%s - %s - %s", THREAD_ID, INSTANT, MESSAGE);
        assertEquals(logMessage.toString(), expectedString);
    }

    @Test
    public void GIVEN_two_logMessages_different_timestamps_WHEN_calling_compareTo_THEN_comparison_is_based_on_timestamp() {
        final LogMessage logMessage2 = new LogMessage(THREAD_ID, INSTANT.plusSeconds(5), MESSAGE);
        assertEquals(logMessage.compareTo(logMessage2), -1);
    }

    @Test
    public void GIVEN_equal_logMessages_WHEN_calling_equals_THEN_return_true() {
        final LogMessage logMessage2 = new LogMessage(THREAD_ID, INSTANT, MESSAGE);
        assertTrue(logMessage.equals(logMessage));
        assertTrue(logMessage.equals(logMessage2));
    }

    @Test
    public void GIVEN_equal_logMessages_WHEN_calling_hashCode_THEN_return_equal_values() {
        final LogMessage logMessage2 = new LogMessage(THREAD_ID, INSTANT, MESSAGE);
        assertEquals(logMessage.hashCode(), logMessage2.hashCode());
    }

    @Test
    public void GIVEN_different_logMessages_WHEN_calling_equals_THEN_return_false() {
        assertFalse(logMessage.equals(null));
        assertFalse(logMessage.equals(new Object()));
        assertFalse(logMessage.equals(new LogMessage("thread_2", INSTANT, MESSAGE)));
        assertFalse(logMessage.equals(new LogMessage(THREAD_ID, INSTANT.plusSeconds(5), MESSAGE)));
        assertFalse(logMessage.equals(new LogMessage(THREAD_ID, INSTANT, "different_message")));
    }

    @Test
    public void GIVEN_different_logMessages_WHEN_calling_hashCode_THEN_return_different_values() {
        final LogMessage logMessage2 = new LogMessage("thread_2", INSTANT, MESSAGE);
        final LogMessage logMessage3 = new LogMessage(THREAD_ID, INSTANT.plusSeconds(5), MESSAGE);
        final LogMessage logMessage4 = new LogMessage(THREAD_ID, INSTANT, "different_message");
        assertNotEquals(logMessage.hashCode(), logMessage2.hashCode());
        assertNotEquals(logMessage.hashCode(), logMessage3.hashCode());
        assertNotEquals(logMessage.hashCode(), logMessage4.hashCode());
    }
}
