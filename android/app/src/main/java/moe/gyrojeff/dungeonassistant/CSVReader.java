package moe.gyrojeff.dungeonassistant;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class CSVReader {
    public static List<String> readCSVHeader(InputStream inputStream) {
        List<String> header = new ArrayList<>();

        try {
            BufferedReader br = new BufferedReader(new InputStreamReader(inputStream));
            String line = br.readLine();
            String[] row = line.split(",");

            header.addAll(Arrays.asList(row).subList(4, row.length));
        } catch (IOException e) {
            e.printStackTrace();
        }

        return header;
    }

    public static List<Map<String, Double>> readCSV(InputStream inputStream) {
        List<Map<String, Double>> data = new ArrayList<>();

        try {
            BufferedReader br = new BufferedReader(new InputStreamReader(inputStream));
            String line = br.readLine();
            String[] header = line.split(",");
            while ((line = br.readLine()) != null) {
                List<String> fields = new ArrayList<>();

                StringBuilder currentField = new StringBuilder();
                for (int i = 0; i < line.length(); i++) {
                    char c = line.charAt(i);
                    if (c == ',') {
                        fields.add(currentField.toString());
                        currentField.setLength(0); // Reset the StringBuilder
                    } else {
                        currentField.append(c);
                    }
                }

                // Add the last field if there are characters remaining
                if (currentField.length() > 0 || line.endsWith(",")) {
                    fields.add(currentField.toString());
                }

                assert fields.size() == header.length;

                Map<String, Double> row_data = new HashMap<>();
                for (int i = 0; i < header.length; i ++) {
                    // write-time
                    if (i == 3) continue;
                    // no signal, default -100
                    if (fields.get(i).equals("")) {
                        row_data.put(header[i], -100.0);
                    } else {
                        row_data.put(header[i], Double.parseDouble(fields.get(i)));
                    }
                }

                data.add(row_data);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

        return data;
    }
}
