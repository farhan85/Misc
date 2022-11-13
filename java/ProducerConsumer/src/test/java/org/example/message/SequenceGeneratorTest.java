package org.example.message;

import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import static org.testng.Assert.assertEquals;

public class SequenceGeneratorTest {

    private SequenceGenerator sequenceGenerator;

    @BeforeMethod
    public void setup() {
        sequenceGenerator = new SequenceGenerator();
    }

    @Test
    public void GIVEN_sequenceGenerator_WHEN_calling_get_three_times_THEN_return_expected_messages() {
        assertEquals(sequenceGenerator.get(), "msg-1");
        assertEquals(sequenceGenerator.get(), "msg-2");
        assertEquals(sequenceGenerator.get(), "msg-3");
    }
}
