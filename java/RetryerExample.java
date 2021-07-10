import net.jodah.failsafe.Failsafe;
import net.jodah.failsafe.RetryPolicy;

import java.time.Clock;
import java.time.Duration;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;

/**
 * An example of using the Failsafe library for implementing backoff-and-retry.
 */
public class RetryerExample {

    private static final DateTimeFormatter DATE_TIME_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd hh:mm:ss:SSSZ")
            .withZone(ZoneId.systemDefault());

    private static final RetryPolicy<Void> RETRY_POLICY = new RetryPolicy<Void>()
            .handle(RetryableException.class)
            .abortOn(AbortException.class)
            .withBackoff(100L, 60000L, ChronoUnit.MILLIS)
            .withJitter(Duration.ofMillis(50))
            .withMaxAttempts(5);

    private int counter;

    public RetryerExample() {
    }

    public void logMethodCall(final String methodName) {
        System.out.println(String.format("%s - Called %s()", DATE_TIME_FORMATTER.format(Clock.systemUTC().instant()), methodName));
    }

    public void run() {
        counter = 0;
        Failsafe.with(RETRY_POLICY).run(this::testFailOnce);
        Failsafe.with(RETRY_POLICY).run(this::testAlwaysSucceed);

        try {
            Failsafe.with(RETRY_POLICY).run(this::testAlwaysFail);
        } catch (final RetryableException e) {
            System.out.println("Failed all retries: " + e.getMessage());
        }

        counter = 0;
        try {
            Failsafe.with(RETRY_POLICY).run(this::testFailThenAbort);
        } catch (final AbortException e) {
            System.out.println("Aborted retries: " + e.getMessage());
        }
    }

    private void testFailOnce() {
        logMethodCall("testFailOnce");
        if (counter < 1) {
            counter++;
            throw new RetryableException("First attempt before success");
        }
    }

    private void testAlwaysSucceed() {
        logMethodCall("testAlwaysSucceed");
    }

    private void testAlwaysFail() {
        logMethodCall("testAlwaysFail");
        throw new RetryableException("I always fail");
    }

    private void testFailThenAbort() {
        logMethodCall("testAbort");
        if (counter < 1) {
            counter++;
            throw new RetryableException("First attempt before abort");
        }
        throw new AbortException("Abort! Abort!");
    }

    public static void main(final String[] args) {
        new RetryerExample().run();
    }

    private class RetryableException extends RuntimeException {

        RetryableException(final String message) {
            super(message);
        }
    }

    private class AbortException extends RuntimeException {

        AbortException(final String message) {
            super(message);
        }
    }
}
