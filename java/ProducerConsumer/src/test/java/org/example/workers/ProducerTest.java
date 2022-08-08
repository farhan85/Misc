package org.example.workers;

import com.google.common.util.concurrent.Uninterruptibles;
import org.example.log.LogWriter;
import org.example.log.LogWriterFactory;
import org.mockito.Mock;
import org.mockito.testng.MockitoTestNGListener;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Listeners;
import org.testng.annotations.Test;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertFalse;

@Listeners(MockitoTestNGListener.class)
public class ProducerTest {

    private static final int THREAD_ID = 1;
    private static final String THREAD_ID_STR = "P1";
    private static final String TEST_MESSAGE = "test-message";

    // Pick values for the simulated work time so that it
    // runs only once before the unit tests wait time is over.
    private static final int WORK_TIME_LOWER = 80;
    private static final int WORK_TIME_UPPER = 90;
    private static final int THREAD_WAIT_TIME = 100;

    @Mock
    private BlockingQueue<String> mockMessageQueue;
    @Mock
    private LogWriterFactory mockLogWriterFactory;
    @Mock
    private LogWriter mockLogWriter;

    private Supplier<String> messageGenerator;
    private BlockingQueue<String> messageQueue;
    private Producer<String> producer;
    private ExecutorService threadPool;

    @BeforeMethod
    public void setup() {
        messageGenerator = () -> TEST_MESSAGE;
        when(mockLogWriterFactory.create(THREAD_ID_STR)).thenReturn(mockLogWriter);
        messageQueue = new ArrayBlockingQueue<>(5);
        producer = new Producer<>(THREAD_ID, WORK_TIME_LOWER, WORK_TIME_UPPER, messageQueue, messageGenerator, mockLogWriterFactory);
        threadPool = Executors.newSingleThreadExecutor();
    }

    @Test
    public void GIVEN_producer_WHEN_running_THEN_puts_message_in_queue() throws InterruptedException {
        threadPool.execute(producer);
        Uninterruptibles.sleepUninterruptibly(THREAD_WAIT_TIME, TimeUnit.MILLISECONDS);

        assertFalse(messageQueue.isEmpty());
        assertEquals(messageQueue.take(), TEST_MESSAGE);
        verify(mockLogWriter).write("Sent message: %s", TEST_MESSAGE);

        threadPool.shutdownNow();
        Uninterruptibles.sleepUninterruptibly(THREAD_WAIT_TIME, TimeUnit.MILLISECONDS);
        verify(mockLogWriter).write("Shutting down");
    }

    @Test
    public void GIVEN_queue_throws_interruptedException_WHEN_running_THEN_stop() throws InterruptedException {
        doThrow(InterruptedException.class).when(mockMessageQueue).put(anyString());
        producer = new Producer<>(THREAD_ID, WORK_TIME_LOWER, WORK_TIME_UPPER, mockMessageQueue, messageGenerator, mockLogWriterFactory);

        threadPool.execute(producer);
        Uninterruptibles.sleepUninterruptibly(THREAD_WAIT_TIME, TimeUnit.MILLISECONDS);

        verify(mockMessageQueue).put(TEST_MESSAGE);
        verify(mockLogWriter).write("Got interrupt signal while waiting to send message: %s", TEST_MESSAGE);
        verify(mockLogWriter).write("Shutting down");
    }
}
