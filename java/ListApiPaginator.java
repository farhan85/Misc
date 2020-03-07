import java.util.ArrayDeque;
import java.util.Iterator;
import java.util.List;
import java.util.Queue;
import java.util.Spliterators;
import java.util.function.Function;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Returns a stream over all the returned paginated results from a given AWS List* API call,
 * making repeated API calls if necessary.
 *
 * Example usage:
 *
 * <pre>
 * AmazonCloudWatch cloudWatchClient = AmazonCloudWatchClientBuilder.standard()
 *                                                                  .withCredentials(...);
 *                                                                  .withRegion(...);
 *                                                                  .build();
 * paginator = new ListApiPaginator<>(new ListMetricsRequest().withNamespace(...)::withNextToken,
 *                                    cloudWatchClient::listMetrics,
 *                                    ListMetricsResult::getMetrics,
 *                                    ListMetricsResult::getNextToken);
 * List<Metric> metrics = paginator.stream()
 *                                 .collect(Collectors.toList());
 * </pre>
 */
public class ListApiPaginator<ListApiRequest, ListApiResult, Item, Token> {

    private final Function<Token, ListApiRequest> listRequestGenerator;
    private final Function<ListApiRequest, ListApiResult> listApiCall;
    private final Function<ListApiResult, List<Item>> listExtractor;
    private final Function<ListApiResult, Token> tokenExtractor;

    public ListApiPaginator(final Function<Token, ListApiRequest> listRequestGenerator,
                            final Function<ListApiRequest, ListApiResult> listApiCall,
                            final Function<ListApiResult, List<Item>> listExtractor,
                            final Function<ListApiResult, Token> tokenExtractor) {
        this.listRequestGenerator = checkNotNull(listRequestGenerator);
        this.listApiCall = checkNotNull(listApiCall);
        this.listExtractor = checkNotNull(listExtractor);
        this.tokenExtractor = checkNotNull(tokenExtractor);
    }

    public Stream<Item> stream() {
        return StreamSupport.stream(Spliterators.spliteratorUnknownSize(new ListApiCallIterator(), 0), false);
    }

    private class ListApiCallIterator implements Iterator<Item> {

        private Token nextToken;
        private Queue<Item> currentItems;

        private ListApiCallIterator() {
        }

        @Override
        public boolean hasNext() {
            return currentItems == null        // Haven't made the first API call yet
                    || !currentItems.isEmpty() // Still have items from the last API call to return
                    || nextToken != null;      // Still need to make more API calls
        }

        @Override
        public Item next() {
            if (currentItems == null) {
                currentItems = new ArrayDeque<>();
            }
            if (currentItems.isEmpty()) {
                getNextBatch();
            }
            return currentItems.remove();
        }

        private void getNextBatch() {
            final ListApiRequest request = listRequestGenerator.apply(nextToken);
            final ListApiResult result = listApiCall.apply(request);
            nextToken = tokenExtractor.apply(result);
            currentItems.addAll(listExtractor.apply(result));
        }
    }
}

