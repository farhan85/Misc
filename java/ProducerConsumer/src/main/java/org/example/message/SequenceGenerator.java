package org.example.message;

import com.google.inject.Inject;

import java.util.function.Supplier;

/**
 * Generates Strings containing an increasing sequence of numbers.
 *
 * Can be used by the Producer class to generate strings.
 */
public class SequenceGenerator implements Supplier<String> {

    private int currentNum;

    @Inject
    SequenceGenerator() {
        this.currentNum = 0;
    }

    @Override
    public String get() {
        return String.format("msg-%d", ++currentNum);
    }
}
