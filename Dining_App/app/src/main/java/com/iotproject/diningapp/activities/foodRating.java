package com.iotproject.diningapp.activities;

import android.content.Intent;
import android.os.Bundle;
import android.support.design.widget.Snackbar;
import android.support.v4.widget.NestedScrollView;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.RatingBar;
import android.widget.TextView;
import android.content.SharedPreferences;
import android.support.design.widget.CoordinatorLayout;

import java.io.BufferedWriter;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.JSONObject;

import com.iotproject.diningapp.R;

public class foodRating extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_food_rating);
        final CoordinatorLayout coordLayout;
        coordLayout = (CoordinatorLayout) findViewById(R.id.coordinatorLayout);

        final RatingBar ratingRatingBar = (RatingBar) findViewById(R.id.rating_rating_bar);
        Button submitButton = (Button) findViewById(R.id.submit_button);
        final TextView ratingDisplayTextView = (TextView) findViewById(R.id.rating_display_text_View);

        submitButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                ratingDisplayTextView.setText("Your rating is: " + ratingRatingBar.getRating());

                HttpURLConnection urlConnection = null;

                try {
                    URL url = new URL("http://54.175.175.238:8000/rating");
//                    URL url = new URL("http://192.168.56.1:8000/rating");
                    SharedPreferences dishDetails = getSharedPreferences("dishname", MODE_PRIVATE);
                    SharedPreferences userDetails = getSharedPreferences("userdetails", MODE_PRIVATE);

                    String user = userDetails.getString("Email", "");
                    String dish = dishDetails.getString("name", "");
                    String diningHall = dishDetails.getString("diningHall", "");


                    JSONObject postDataParams = new JSONObject();
                    postDataParams.put("dishname", dish);
                    postDataParams.put("email", user);
                    postDataParams.put("diningHall", diningHall);
                    postDataParams.put("rating", ratingRatingBar.getRating());
                    Log.e("params",postDataParams.toString());

                    urlConnection = (HttpURLConnection) url.openConnection();
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

                    int responseCode=urlConnection.getResponseCode();

                    if (responseCode == HttpURLConnection.HTTP_OK) {
                        // Snack Bar to show success message that record saved successfully
                        ratingDisplayTextView.setText("Your rating is submitted");

                    } else {
                        // Snack Bar to show error message that record already exists
                        Snackbar.make(coordLayout, getString(R.string.error_rating_submit), Snackbar.LENGTH_LONG).show();
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

    }

}
