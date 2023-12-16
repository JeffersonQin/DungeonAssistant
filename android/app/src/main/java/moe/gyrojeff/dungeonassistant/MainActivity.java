package moe.gyrojeff.dungeonassistant;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.content.res.Resources;
import android.net.wifi.ScanResult;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.os.Handler;
import android.widget.TextView;
import android.widget.Toast;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class MainActivity extends AppCompatActivity {


    private MapImageView mapImageView;
    private TextView positionTextView;
    private WifiManager wm;

    private Context context;

    private List<String> macAddresses;
    private List<Map<String, Double>> signalDataset;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mapImageView = findViewById(R.id.mapImageView);
        positionTextView = findViewById(R.id.positionTextView);

        wm = (WifiManager) getApplicationContext().getSystemService(WIFI_SERVICE);
        wm.startScan();

        context = this;

        Resources resources = getResources();

        macAddresses = CSVReader.readCSVHeader(resources.openRawResource(R.raw.dataset));
        Toast.makeText(getApplicationContext(), "" + macAddresses.size(), Toast.LENGTH_SHORT).show();


        signalDataset = CSVReader.readCSV(resources.openRawResource(R.raw.dataset));

        startUpdatingPosition();
    }

    private void startUpdatingPosition() {
        // Create a Handler to update the position every second
        Handler handler = new Handler();
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                // Update the position of the red point
                wm.startScan();

                if (ActivityCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                    return;
                }
                List<ScanResult> scanResults = wm.getScanResults();

                Map<String, Double> X = new HashMap<>();

                for (ScanResult sr : scanResults) {
                    if (macAddresses.contains(sr.BSSID)) {
                        X.put(sr.BSSID, (double) sr.level);
                    }
                }

                // calculate the nearest neighbour
                double nearest_X = 0;
                double nearest_Y = 0;

                double smallest_error = 1e18;

                for (Map<String, Double> positionSignal : signalDataset) {
                    double accumulated_error = 0;
                    for (String mac : macAddresses) {
                        if (X.containsKey(mac)) {
                            accumulated_error += Math.pow(X.get(mac) - positionSignal.get(mac), 2);
                        } else {
                            accumulated_error += Math.pow(-100 - positionSignal.get(mac), 2);
                        }
                    }
                    if (accumulated_error < smallest_error) {
                        smallest_error = accumulated_error;
                        nearest_X = positionSignal.get("1");
                        nearest_Y = positionSignal.get("3");
                    }
                }
                // Define the desired date format
                SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
                // Get the current time
                Date currentTime = new Date();
                positionTextView.setText("Refresh: " + dateFormat.format(currentTime) + "\nX:" + nearest_X + "\nY:" + nearest_Y);

                // Update the position in the customImageView
                float minX = -812, maxX = 294, minY = -1009, maxY = 7;
                float scale = 10;

                mapImageView.updatePosition((float) ((nearest_Y * scale - minY) / (maxY - minY)), (float) ((nearest_X * scale - minX) / (maxX - minX)));

                // Schedule the next update after 1 second
                handler.postDelayed(this, 1000);
            }
        }, 1000);
    }
}