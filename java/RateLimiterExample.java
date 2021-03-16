import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.stream.IntStream;
import com.google.common.util.concurrent.RateLimiter;

public class RateLimiterExample {

    private static final DateTimeFormatter DATE_TIME_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd hh:mm:ss")
            .withZone(ZoneId.systemDefault());

    public static void main(final String[] args) throws InterruptedException {
        final RateLimiter rateLimiter = RateLimiter.create(3);
        final ExecutorService executor = Executors.newFixedThreadPool(15);

        IntStream.range(1, 16)
                .forEach(i -> executor.execute(() -> {
                    rateLimiter.acquire();
                    System.out.println(String.format("%s - Thread %d executing", DATE_TIME_FORMATTER.format(Instant.now()), i));
                }));

        executor.shutdown();
        executor.awaitTermination(1, TimeUnit.MINUTES);
    }
}
