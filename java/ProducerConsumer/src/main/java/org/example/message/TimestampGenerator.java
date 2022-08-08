package org.example.message;

import com.google.inject.Inject;

import java.time.Clock;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.function.Supplier;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Generates Strings of timestamps.
 *
 * Can be used by the Producer class to generate strings.
 */
public class TimestampGenerator implements Supplier<String> {

    private static final DateTimeFormatter DATE_TIME_FORMATTER = DateTimeFormatter.ISO_OFFSET_TIME
            .withZone(ZoneId.of("UTC"));

    private final Clock clock;

    @Inject
    TimestampGenerator(final Clock clock) {
        this.clock = checkNotNull(clock);
    }

    @Override
    public String get() {
        return DATE_TIME_FORMATTER.format(clock.instant());
    }
}
