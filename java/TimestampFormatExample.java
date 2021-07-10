import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;

/**
 * Example of printing timestamps.
 */
public class TimestampFormatExample {

    public static void main(final String[] args) {
        final Clock clock = Clock.systemUTC();
        final DateTimeFormatter dateTimeFormatter = DateTimeFormatter.ISO_OFFSET_DATE_TIME
                .withZone(ZoneId.of("UTC"));
        final DateTimeFormatter dateTimeFormatterLocal = DateTimeFormatter.ofPattern("yyyy-MM-dd hh:mm:ss VV")
                .withZone(ZoneId.systemDefault());
        final DateTimeFormatter dateTimeFormatterAEST = DateTimeFormatter.ofPattern("yyyy-MM-dd hh:mm:ss z")
                .withZone(ZoneId.of("Australia/Sydney"));

        final Instant now = clock.instant();
        System.out.println(dateTimeFormatter.format(now));
        System.out.println(dateTimeFormatterLocal.format(now));
        System.out.println(dateTimeFormatterAEST.format(now));
    }
}
