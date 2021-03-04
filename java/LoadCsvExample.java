import com.opencsv.CSVReader;
import com.opencsv.bean.CsvBindByName;
import com.opencsv.bean.CsvToBeanBuilder;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

public class LoadCsvExample {

    public static void main(final String[] args) throws IOException {
        final Path filePath = Paths.get("path/to/file/employees.csv");

        try (final BufferedReader reader = Files.newBufferedReader(filePath);
             final CSVReader csvReader = new CSVReader(reader)) {

            final List<Employee> employees = new CsvToBeanBuilder<Employee>(csvReader)
                    .withType(Employee.class)
                    .build()
                    .parse(); // Use .iterator() if the CSV file is too big

            System.out.println(employees);
        }
    }

    public static class Employee {

        @CsvBindByName
        private String firstName;

        @CsvBindByName
        private String lastName;

        @Override
        public String toString() {
            return firstName + " " + lastName;
        }
    }
}

