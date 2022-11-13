package org.example.guice;

import com.google.inject.AbstractModule;
import com.google.inject.Provides;
import com.google.inject.TypeLiteral;
import com.google.inject.name.Named;
import com.google.inject.name.Names;
import org.example.properties.BufferedFileReaderProvider;
import org.example.properties.PropertiesFileReader;

import java.io.BufferedReader;
import java.nio.file.Path;
import java.util.Properties;
import java.util.function.Function;

public class PropertiesModule extends AbstractModule {

    private final TypeLiteral<Function<Path, BufferedReader>> READER_PROVIDER_TYPE = new TypeLiteral<>() {};
    private final TypeLiteral<Function<Path, Properties>> PROPERTIES_PROVIDER_TYPE = new TypeLiteral<>() {};

    @Override
    protected void configure() {
        bind(READER_PROVIDER_TYPE).to(BufferedFileReaderProvider.class);
        bind(PROPERTIES_PROVIDER_TYPE).to(PropertiesFileReader.class);
        bind(Path.class).annotatedWith(Names.named("ConfigPropertyFile")).toInstance(Path.of("src/main/resources/config.properties"));
    }


    @Provides
    @Named("ConfigProperties")
    public Properties provideConfigPropertiesFactory(final Function<Path, Properties> propertiesFileReader, @Named("ConfigPropertyFile") final Path configFile) {
        return propertiesFileReader.apply(configFile);
    }
}
