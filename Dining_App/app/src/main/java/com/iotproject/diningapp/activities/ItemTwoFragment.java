package com.iotproject.diningapp.activities;

import android.content.Intent;
import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.TextView;
import java.net.HttpURLConnection;
import java.io.InputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URL;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedWriter;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.net.URLEncoder;
import java.util.Iterator;

import android.content.SharedPreferences;


import com.iotproject.diningapp.R;

import static android.content.Context.MODE_PRIVATE;

public class ItemTwoFragment extends Fragment {

    public static ItemTwoFragment newInstance() {
        ItemTwoFragment fragment = new ItemTwoFragment();
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_item_two, container, false);
        Button button = (Button) view.findViewById(R.id.btnRecommend);
        final ListView listView = (ListView) view.findViewById(R.id.list_recommend);
        final TextView display = (TextView) view.findViewById(R.id.text);
        button.setOnClickListener(new View.OnClickListener()
        {
            @Override
            public void onClick(View v)
            {
                URL url;
                HttpURLConnection urlConnection = null;
                String jsonString = "";
                try {
//                    url = new URL("http://192.168.56.1:8000/recommend");
                    url = new URL("http://54.175.175.238:8000/recommend");
                    JSONObject postDataParams = new JSONObject();
                    SharedPreferences userDetails = getActivity().getSharedPreferences("userdetails", MODE_PRIVATE);

                    String user = userDetails.getString("Email", "");
                    postDataParams.put("email", user);
                    Log.e("params",postDataParams.toString());

                    urlConnection = (HttpURLConnection) url
                            .openConnection();
                    urlConnection.setReadTimeout(15000);
                    urlConnection.setConnectTimeout(15000);
                    urlConnection.setRequestMethod("POST");
                    urlConnection.setDoOutput(true);
                    urlConnection.setDoInput(true);
                    urlConnection.setRequestProperty("Content-Type","application/json;charset=UTF-8");

                    OutputStream out = urlConnection.getOutputStream();

                    BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(out));
                    writer.write(postDataParams.toString());
                    writer.flush();
                    writer.close();
                    out.close();

                    int responseCode = urlConnection.getResponseCode();
                    if (responseCode == HttpURLConnection.HTTP_OK) {
                        InputStream in = urlConnection.getInputStream();
                        BufferedReader bfReader = new BufferedReader(new InputStreamReader(in, "UTF-8"));
                        String line;
                        while ((line = bfReader.readLine()) != null) {
                            // Append the text to string buffer.
                            jsonString += line;

                        }
                        Log.d("response", jsonString);
                        JSONObject object = new JSONObject(jsonString);
                        Log.d("object", object.toString());
                        JSONArray menuJson = object.getJSONArray("menu");
                        String[] menu = new String[menuJson.length()];
                        for(int i = 0; i < menuJson.length(); i++)
                            menu[i] = menuJson.getString(i);
                        final String recommendation = object.getString("recommendation");
                        Log.d("recommend", recommendation);

                        display.setText("Recommendation is: " + recommendation);
                        bfReader.close();

                        ArrayAdapter<String> arrayAdapter = new ArrayAdapter<String>
                                (getActivity().getApplicationContext(), android.R.layout.simple_list_item_1, menu);

                        // Populate ListView with items from ArrayAdapter
                        listView.setAdapter(arrayAdapter);

                        listView.setOnItemClickListener(new AdapterView.OnItemClickListener() {
                            public void onItemClick(AdapterView<?> parent, View view,
                                                    int position, long id) {
                                String selectedItem = (String) parent.getItemAtPosition(position);
                                SharedPreferences dishDetails = getActivity().getSharedPreferences("dishname", MODE_PRIVATE);
                                SharedPreferences.Editor edit = dishDetails.edit();
                                edit.putString("name", selectedItem);
                                edit.putString("diningHall", recommendation);
                                edit.apply();
                                Intent myIntent = new Intent(view.getContext(), foodRating.class);
                                startActivityForResult(myIntent, 0);

                            }
                        });
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                } finally {
                    if (urlConnection != null) {
                        urlConnection.disconnect();
                    }
                }
            }
        });
        return view;
    }

}