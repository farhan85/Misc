import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import org.apache.logging.log4j.Level;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.core.LogEvent;
import org.apache.logging.log4j.core.LoggerContext;
import org.apache.logging.log4j.core.appender.AbstractAppender;
import org.apache.logging.log4j.core.config.Configuration;
import org.apache.logging.log4j.core.config.LoggerConfig;
import org.junit.rules.ExternalResource;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Stream;

import static com.google.common.collect.ImmutableMap.toImmutableMap;

/**
 * JUnit rule for capturing Apache Log4j2 logs to help with testing
 * that the correct logs were written.
 *
 * Note: You must already have Log4j2 set up when running your tests
 * otherwise there's no logs for this class to capture.
 *
 * Example usage:
 * <pre>
 *  @Rule
 *  public LogCapture logCapture = new LogCapture();
 *
 *  // Get the messages written out to the logs
 *  List<String> infologs = logCapture.getLogs(Level.INFO);
 *  assertThat(infoLogs, contains("Computed value for..."));
 * </pre>
 */
public class LogCapture extends ExternalResource {

    private static final String LIST_APPENDER_NAME = "UnitTestAppender";
    private final LoggerConfig loggerConfig;

    public LogCapture(String loggerName) {
        final LoggerContext loggerContext = (LoggerContext) LogManager.getContext(false);
        final Configuration configuration = loggerContext.getConfiguration();
        loggerConfig = configuration.getLoggerConfig(loggerName);
    }

    @Override
    public void before() {
        if (loggerConfig.getAppenders().containsKey(LIST_APPENDER_NAME)) {
            getListAppender().clearLogs();
        }
        loggerConfig.addAppender(new ListAppender(LIST_APPENDER_NAME), Level.ALL, null);
    }

    public List<String> getLogs(final Level level) {
        return getListAppender().getLogs(level);
    }

    private ListAppender getListAppender() {
        return (ListAppender) loggerConfig.getAppenders().get(LIST_APPENDER_NAME);
    }

    /**
     * Log Appender that stores all logs in memory which can be retrieved as a list of Strings.
     */
    private static class ListAppender extends AbstractAppender {

        private final Map<Level, List<String>> logs;

        ListAppender(final String appenderName) {
            super(appenderName, null, null);
            logs = Stream.of(Level.ERROR, Level.WARN, Level.INFO, Level.DEBUG, Level.TRACE)
                    .collect(toImmutableMap(Function.identity(), level -> Lists.newArrayList()));
        }

        @Override
        public void append(final LogEvent logEvent) {
            logs.get(logEvent.getLevel()).add(logEvent.getMessage().getFormattedMessage());
        }

        void clearLogs() {
            logs.values().forEach(List::clear);
        }

        List<String> getLogs(final Level level) {
            return ImmutableList.copyOf(logs.get(level));
        }
    }
}
