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

import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.testng.Assert.assertTrue;

@Listeners(MockitoTestNGListener.class)
public class ConsumerTest {

    private static final int THREAD_ID = 1;
    private static final String THREAD_ID_STR = "C1";

    // Pick values for the simulated work time so that it
    // runs only once before the unit tests wait time is over.
    private static final int WORK_TIME_LOWER = 80;
    private static final int WORK_TIME_UPPER = 90;
    private static final int THREAD_WAIT_TIME = 100;

    @Mock
    private LogWriterFactory mockLogWriterFactory;
    @Mock
    private LogWriter mockLogWriter;
    @Mock
    private BlockingQueue<String> mockMessageQueue;

    private BlockingQueue<String> messageQueue;
    private Consumer<String> consumer;
    private ExecutorService threadPool;

    @BeforeMethod
    public void setup() {
        when(mockLogWriterFactory.create(THREAD_ID_STR)).thenReturn(mockLogWriter);
        messageQueue = new ArrayBlockingQueue<>(5);
        consumer = new Consumer<>(THREAD_ID, messageQueue, WORK_TIME_LOWER, WORK_TIME_UPPER, mockLogWriterFactory);
        threadPool = Executors.newSingleThreadExecutor();
    }

    @Test
    public void GIVEN_message_in_queue_WHEN_running_THEN_consumer_logs_message() throws InterruptedException {
        messageQueue.put("test-message");

        threadPool.execute(consumer);
        Uninterruptibles.sleepUninterruptibly(THREAD_WAIT_TIME, TimeUnit.MILLISECONDS);

        assertTrue(messageQueue.isEmpty());
        verify(mockLogWriter).write("Consumed message: %s", "test-message");

        threadPool.shutdownNow();
        Uninterruptibles.sleepUninterruptibly(THREAD_WAIT_TIME, TimeUnit.MILLISECONDS);
        verify(mockLogWriter).write("Shutting down");
    }

    @Test
    public void GIVEN_queue_throws_interruptedException_WHEN_calling_take_THEN_stop() throws InterruptedException {
        doThrow(InterruptedException.class).when(mockMessageQueue).take();
        consumer = new Consumer<>(THREAD_ID, mockMessageQueue, WORK_TIME_LOWER, WORK_TIME_UPPER, mockLogWriterFactory);
        messageQueue.put("test-message");

        threadPool.execute(consumer);
        Uninterruptibles.sleepUninterruptibly(THREAD_WAIT_TIME, TimeUnit.MILLISECONDS);

        verify(mockLogWriter).write("Got interrupt signal while waiting for new message");
        verify(mockLogWriter).write("Shutting down");
    }
}
