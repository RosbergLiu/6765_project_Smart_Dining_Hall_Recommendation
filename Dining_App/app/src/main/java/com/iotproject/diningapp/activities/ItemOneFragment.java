package com.iotproject.diningapp.activities;

import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import com.iotproject.diningapp.R;

import android.content.Intent;


public class ItemOneFragment extends Fragment {
    public static ItemOneFragment newInstance() {
        ItemOneFragment fragment = new ItemOneFragment();
        return fragment;
    }


    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_item_one, container, false);
        view.findViewById(R.id.appCompatButtonJohnJay).setOnClickListener(mListener);
        view.findViewById(R.id.appCompatButtonJJ).setOnClickListener(mListener);
        view.findViewById(R.id.appCompatButtonFerris).setOnClickListener(mListener);

        return view;
    }

    private final View.OnClickListener mListener = new View.OnClickListener() {
        public void onClick(View view) {
            switch (view.getId()) {
                case R.id.appCompatButtonJohnJay:
                    startActivity(new Intent(getActivity(), Information_John_Jay.class));
                    break;
                case R.id.appCompatButtonJJ:
                    startActivity(new Intent(getActivity(), Information_JJ.class));
                    break;
                case R.id.appCompatButtonFerris:
                    startActivity(new Intent(getActivity(), Information_Ferris.class));
                    break;
            }
        }
    };

}
