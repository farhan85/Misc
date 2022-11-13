package org.example.log;

import com.google.common.util.concurrent.Uninterruptibles;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import java.time.Instant;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.testng.Assert.assertTrue;

public class DistributedLogReaderTest {

    private static final int BATCH_SIZE = 2;
    private static final int WAIT_TIME_MS = 100;
    private static final int THREAD_WAIT_TIME = 120;
    private static final Instant INSTANT_1 = Instant.parse("2022-02-01T01:00:00Z");
    private static final Instant INSTANT_2 = Instant.parse("2022-02-01T02:00:00Z");
    private static final Instant INSTANT_3 = Instant.parse("2022-02-01T03:00:00Z");
    private static final LogMessage LOG_MESSAGE_1 = new LogMessage("thread-1", INSTANT_1, "message-1");
    private static final LogMessage LOG_MESSAGE_2 = new LogMessage("thread-1", INSTANT_2, "message-2");
    private static final LogMessage LOG_MESSAGE_3 = new LogMessage("thread-1", INSTANT_3, "message-3");

    private BlockingQueue<LogMessage> logQueue;
    private DistributedLogReader logReader;
    private ExecutorService threadPool;

    @BeforeMethod
    public void setup() {
        logQueue = new ArrayBlockingQueue<>(5);
        logReader = new DistributedLogReader(logQueue, BATCH_SIZE, WAIT_TIME_MS);
        threadPool = Executors.newSingleThreadExecutor();
    }

    @Test
    public void GIVEN_message_in_queue_WHEN_running_THEN_logReader_takes_message() throws InterruptedException {
        logQueue.put(LOG_MESSAGE_1);

        threadPool.execute(logReader);
        Uninterruptibles.sleepUninterruptibly(THREAD_WAIT_TIME, TimeUnit.MILLISECONDS);
        threadPool.shutdownNow();

        assertTrue(logQueue.isEmpty());
    }

    @Test
    public void GIVEN_more_messages_in_queue_than_batch_size_WHEN_running_THEN_logReader_takes_message() throws InterruptedException {
        logQueue.put(LOG_MESSAGE_1);
        logQueue.put(LOG_MESSAGE_2);
        logQueue.put(LOG_MESSAGE_3);

        threadPool.execute(logReader);
        Uninterruptibles.sleepUninterruptibly(THREAD_WAIT_TIME, TimeUnit.MILLISECONDS);
        threadPool.shutdownNow();

        assertTrue(logQueue.isEmpty());
    }
}
