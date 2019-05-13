package com.iotproject.diningapp.activities;

import android.content.Intent;
import android.content.SharedPreferences;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ListView;
import android.widget.TextView;
import java.net.HttpURLConnection;
import java.io.InputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;

import com.iotproject.diningapp.R;

import org.json.JSONArray;
import org.json.JSONObject;


public class Information_JJ extends AppCompatActivity {

    TextView serverResp;
    ListView listView;
    URL url;
    HttpURLConnection urlConnection = null;
    SharedPreferences dishDetails;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_information__jj);

        serverResp = (TextView)findViewById(R.id.jj_resp);
        listView = (ListView) findViewById(R.id.list_jj);
        String jsonString = "";

        try {
            url = new URL("http://54.175.175.238:8000/JJ");
//            url = new URL("http://192.168.56.1:8000/JJ");

            urlConnection = (HttpURLConnection) url
                    .openConnection();
            if(urlConnection.getResponseCode() == HttpURLConnection.HTTP_OK){
                InputStream in = urlConnection.getInputStream();
                InputStreamReader responseBodyReader =
                        new InputStreamReader(in, "UTF-8");

                BufferedReader isw = new BufferedReader(responseBodyReader);
                String line;
                while((line = isw.readLine()) != null)
                {
                    // Append the text to string buffer.
                    jsonString += line;
                }
                Log.d("response", jsonString);
                JSONObject object = new JSONObject(jsonString);
                JSONArray menuJson = object.getJSONArray("menu");
                String[] menu = new String[menuJson.length()];
                for(int i = 0; i < menuJson.length(); i++)
                    menu[i] = menuJson.getString(i);
                String tables = object.getString("table_availability");
                Log.d("table", tables);
                int flow_rate = object.getInt("flow_rate");

                serverResp.setText("Flow rate:" + flow_rate + '\n' + "Tables available: " + tables);

                // Create a ArrayAdapter from List
                ArrayAdapter<String> arrayAdapter = new ArrayAdapter<String>
                        (this, android.R.layout.simple_list_item_1, menu);

                // Populate ListView with items from ArrayAdapter
                listView.setAdapter(arrayAdapter);

                listView.setOnItemClickListener(new AdapterView.OnItemClickListener() {
                    public void onItemClick(AdapterView<?> parent, View view,
                                            int position, long id) {
                        String selectedItem = (String) parent.getItemAtPosition(position);
                        dishDetails = getSharedPreferences("dishname", MODE_PRIVATE);
                        SharedPreferences.Editor edit = dishDetails.edit();
                        edit.putString("name", selectedItem);
                        edit.putString("diningHall", "JJ");
                        edit.apply();
                        Intent myIntent = new Intent(view.getContext(), foodRating.class);
                        startActivityForResult(myIntent, 0);

                    }
                });
            }

        } catch (Exception e) {
            Log.d("OOPS", "Error checking internet connection");
        } finally {
            if (urlConnection != null) {
                urlConnection.disconnect();
            }
        }

    }

}
