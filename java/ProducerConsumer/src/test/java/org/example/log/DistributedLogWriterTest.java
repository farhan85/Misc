package org.example.log;

import org.mockito.Mock;
import org.mockito.testng.MockitoTestNGListener;
import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Listeners;
import org.testng.annotations.Test;

import java.time.Clock;
import java.time.Instant;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;
import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

@Listeners(MockitoTestNGListener.class)
public class DistributedLogWriterTest {

    private static final String THREAD_ID = "thread_1";
    private static final String TIMESTAMP = "2022-02-01T01:02:03.123456Z";
    private static final Instant INSTANT = Instant.parse(TIMESTAMP);
    private static final String MESSAGE = "test_message";

    @Mock
    private Clock mockClock;
    @Mock
    private BlockingQueue<LogMessage> mockLogQueue;

    private BlockingQueue<LogMessage> logQueue;
    private DistributedLogWriter logWriter;

    @BeforeMethod
    public void setup() {
        logQueue = new ArrayBlockingQueue<>(5);
        logWriter = new DistributedLogWriter(mockClock, THREAD_ID, logQueue);
    }

    @Test
    public void GIVEN_null_parameters_WHEN_calling_constructor_THEN_throw_exception() {
        Assert.assertThrows(NullPointerException.class, () -> new DistributedLogWriter(mockClock, null, logQueue));
        Assert.assertThrows(NullPointerException.class, () -> new DistributedLogWriter(mockClock, THREAD_ID, null));
    }

    @Test
    public void GIVEN_format_string_and_args_WHEN_calling_write_THEN_send_expected_message_to_queue() throws InterruptedException {
        when(mockClock.instant()).thenReturn(INSTANT);
        final LogMessage expected = new LogMessage(THREAD_ID, INSTANT, "message-1");

        logWriter.write("message-%d", 1);
        assertEquals(logQueue.size(), 1);
        assertEquals(logQueue.take(), expected);
    }

    @Test
    public void GIVEN_message_WHEN_calling_write_THEN_send_expected_message_to_queue() throws InterruptedException {
        when(mockClock.instant()).thenReturn(INSTANT);
        final LogMessage expected = new LogMessage(THREAD_ID, INSTANT, MESSAGE);

        logWriter.write(MESSAGE);
        assertEquals(logQueue.size(), 1);
        assertEquals(logQueue.take(), expected);
    }

    @Test
    public void GIVEN_queue_throws_interruptedException_WHEN_calling_write_THEN_do_nothing() throws InterruptedException {
        when(mockClock.instant()).thenReturn(INSTANT);
        doThrow(InterruptedException.class).when(mockLogQueue).put(any(LogMessage.class));
        logWriter = new DistributedLogWriter(mockClock, THREAD_ID, mockLogQueue);

        logWriter.write(MESSAGE);
        assertTrue(logQueue.isEmpty());
    }
}
