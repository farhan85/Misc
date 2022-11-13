package org.example.app;

import com.google.inject.Provider;
import org.mockito.Mock;
import org.mockito.testng.MockitoTestNGListener;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Listeners;
import org.testng.annotations.Test;

import java.util.Properties;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@Listeners(MockitoTestNGListener.class)
public class ConfigPropertiesDisplayTest {

    @Mock
    private Provider<Properties> mockPropertiesProvider;
    @Mock
    private Properties mockProperties;

    private ConfigPropertiesDisplay configPropertiesProvider;

    @BeforeMethod
    public void setup() {
        when(mockPropertiesProvider.get()).thenReturn(mockProperties);
        configPropertiesProvider = new ConfigPropertiesDisplay(mockPropertiesProvider);
    }

    @Test
    public void GIVEN_configPropertiesProvider_WHEN_calling_run_THEN_verify_properties_used() {
        configPropertiesProvider.run();
        verify(mockPropertiesProvider).get();
        verify(mockProperties).getProperty("name");
    }
}
