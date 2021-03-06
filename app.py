#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from logging import PlaceHolder
from optparse import Option
import streamlit as st
st.set_page_config(page_title="Song Recommendation", layout="wide")

import pandas as pd
from sklearn.neighbors import NearestNeighbors
import plotly.express as px
import numpy as np
import streamlit.components.v1 as components
from numpy.linalg import norm
import tekore as tk

add_selectbox = st.sidebar.selectbox(
    "Recommendation System?",
    ("Simple Music Recommendation System","Mood based Music Recommendaion System")
)

def Mood():   
    with st.container():
        @st.cache(allow_output_mutation=True)
        def authorize():
            CLIENT_ID = 'b948d88375364b50888a9954f9369843'
            CLIENT_SECRET = '3ff362ae75a044dc9d38800ab82ca089'
            app_token = tk.request_client_token(CLIENT_ID, CLIENT_SECRET)
            return tk.Spotify(app_token)
        sp =authorize()
        df = pd.read_csv("data/valence_arousal_dataset.csv")
        df["mood_vec"] = df[["valence", "energy"]].values.tolist()
        def recommend(track_id, ref_df, sp, n_recs = 5):
            # Crawl valence and arousal of given track from spotify api
            track_features = sp.track_audio_features(track_id)
            track_moodvec = np.array([track_features.valence, track_features.energy])
            
            # Compute distances to all reference tracks
            ref_df["distances"] = ref_df["mood_vec"].apply(lambda x: norm(track_moodvec-np.array(x)))
            # Sort distances from lowest to highest
            ref_df_sorted = ref_df.sort_values(by = "distances", ascending = True)
            # If the input track is in the reference set, it will have a distance of 0, but should not be recommendet
            ref_df_sorted = ref_df_sorted[ref_df_sorted["id"] != track_id]
            
            # Return n recommendations
            return ref_df_sorted.iloc[:n_recs]
        def page2():
            pagetitle = "Mood Based Song Recommendation Engine"
            st.title(pagetitle)
            title = st.text_input('Spotify Song Link', '')
            if title=="":
                st.write("No input detected")
            else:
                songid=title[31:53]
                recommended=recommend(track_id = songid, ref_df = df, sp = sp, n_recs = 10)
                tracks_per_page = 6
                rec_songid = recommended['id'].tolist()
                tracks = []
                for uri in rec_songid:
                    track = """<iframe style=border-radius:12px src="https://open.spotify.com/embed/track/{}" width="100%" height="80" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>""".format(uri)
                    tracks.append(track)
                for trackid in tracks:
                    components.html(trackid)
        page2()
                





def Simple():   
    with st.container():
        @st.cache(allow_output_mutation=True)
        def load_data():
            df = pd.read_csv("data/filtered_track_df.csv")
            df['genres'] = df.genres.apply(lambda x: [i[1:-1] for i in str(x)[1:-1].split(", ")])
            exploded_track_df = df.explode("genres")
            return exploded_track_df

        genre_names = ['Dance Pop', 'Electronic', 'Electropop', 'Hip Hop', 'Jazz', 'K-pop', 'Latin', 'Pop', 'Pop Rap', 'R&B', 'Rock']
        audio_feats = ["acousticness", "danceability", "energy", "instrumentalness", "valence", "tempo"]

        exploded_track_df = load_data()

        def n_neighbors_uri_audio(genre, start_year, end_year, test_feat):
            genre = genre.lower()
            genre_data = exploded_track_df[(exploded_track_df["genres"]==genre) & (exploded_track_df["release_year"]>=start_year) & (exploded_track_df["release_year"]<=end_year)]
            genre_data = genre_data.sort_values(by='popularity', ascending=False)[:500]

            neigh = NearestNeighbors()
            neigh.fit(genre_data[audio_feats].to_numpy())

            n_neighbors = neigh.kneighbors([test_feat], n_neighbors=len(genre_data), return_distance=False)[0]

            uris = genre_data.iloc[n_neighbors]["uri"].tolist()
            audios = genre_data.iloc[n_neighbors][audio_feats].to_numpy()
            return uris, audios

        def page():
            title = "Song Recommendation Engine"
            st.title(title)

            st.write("First of all, welcome! This is the place where you can customize what you want to listen to based on genre and several key audio features. Try playing around with different settings and listen to the songs recommended by our system!")
            st.markdown("##")

            with st.container():
                col1, col2,col3,col4 = st.columns((2,0.5,0.5,0.5))
                with col3:
                    st.markdown("***Choose your genre:***")
                    genre = st.radio(
                        "",
                        genre_names, index=genre_names.index("Pop"))
                with col1:
                    st.markdown("***Choose features to customize:***")
                    start_year, end_year = st.slider(
                        'Select the year range',
                        1990, 2019, (2015, 2019)
                    )
                    acousticness = st.slider(
                        'Acousticness',
                        0.0, 1.0, 0.5)
                    danceability = st.slider(
                        'Danceability',
                        0.0, 1.0, 0.5)
                    energy = st.slider(
                        'Energy',
                        0.0, 1.0, 0.5)
                    instrumentalness = st.slider(
                        'Instrumentalness',
                        0.0, 1.0, 0.0)
                    valence = st.slider(
                        'Valence',
                        0.0, 1.0, 0.45)
                    tempo = st.slider(
                        'Tempo',
                        0.0, 244.0, 118.0)

            tracks_per_page = 6
            test_feat = [acousticness, danceability, energy, instrumentalness, valence, tempo]
            uris, audios = n_neighbors_uri_audio(genre, start_year, end_year, test_feat)

            tracks = []
            for uri in uris:
                track = """<iframe style=border-radius:12px src="https://open.spotify.com/embed/track/{}" width="100%" height="80" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>""".format(uri)
                tracks.append(track)

            if 'previous_inputs' not in st.session_state:
                st.session_state['previous_inputs'] = [genre, start_year, end_year] + test_feat
            
            current_inputs = [genre, start_year, end_year] + test_feat
            if current_inputs != st.session_state['previous_inputs']:
                if 'start_track_i' in st.session_state:
                    st.session_state['start_track_i'] = 0
                st.session_state['previous_inputs'] = current_inputs

            if 'start_track_i' not in st.session_state:
                st.session_state['start_track_i'] = 0
            
            with st.container():
                col1, col2, col3 = st.columns([2,1,2])
                if st.button("Recommend More Songs"):
                    if st.session_state['start_track_i'] < len(tracks):
                        st.session_state['start_track_i'] += tracks_per_page

                current_tracks = tracks[st.session_state['start_track_i']: st.session_state['start_track_i'] + tracks_per_page]
                current_audios = audios[st.session_state['start_track_i']: st.session_state['start_track_i'] + tracks_per_page]
                if st.session_state['start_track_i'] < len(tracks):
                    for i, (track, audio) in enumerate(zip(current_tracks, current_audios)):
                        if i%2==0:
                            with col1:
                                components.html(
                                    track,
                                )
                                
                    
                        else:
                            with col3:
                                components.html(
                                    track,
                                )
                                

                else:
                    st.write("No songs left to recommend")

        page()

if add_selectbox=="Simple Music Recommendation System":
    Simple()
else:
    Mood()
    