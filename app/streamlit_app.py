import streamlit as st
import requests
import pandas as pd
import sys
import os

# ----------------------
# 📁 Import Local Module
# ----------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.recommender import recommend_workouts

# ----------------------
# 🔐 Load API Key
# ----------------------
YOUTUBE_API_KEY = st.secrets["api"]["youtube_key"]

# ----------------------
# 📊 Load Data
# ----------------------
df = pd.read_csv('data/cleaned_gym_exercise_data.csv')

# ----------------------
# 💪 App Header
# ----------------------
st.set_page_config(page_title="Workout Recommender", layout="centered")
st.title("Personal Workout Recommender")
st.markdown("""
Welcome to your AI-powered workout buddy!  
Just tell us your fitness level, available equipment, and target body area — and we’ll recommend workouts tailored to you.
---
""")

# ----------------------
# 🎛️ User Inputs
# ----------------------
col1, col2 = st.columns(2)
with col1:
    workout_type = st.selectbox("Type of Workout", options=["Any"] + sorted(df['Type'].dropna().unique()))
    level = st.selectbox("Your Fitness Level", options=["Any"] + sorted(df['Level'].dropna().unique()))
with col2:
    bodypart = st.selectbox("Target Body Part", options=["Any"] + sorted(df['BodyPart'].dropna().unique()))
    equipment = st.selectbox("Equipment Available", options=["Any"] + sorted(df['Equipment'].dropna().unique()))

num_recommendations = st.slider("Number of Recommendations", 1, 10, 5)

# ----------------------
# 🔍 YouTube API Helper
# ----------------------
def fetch_youtube_video(query, max_results=1):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query + " workout",
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params)
    results = response.json()

    videos = []
    for item in results.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        videos.append((title, f"https://www.youtube.com/watch?v={video_id}"))
    return videos

# ----------------------
# 🧠 Logic to Convert 'Any' to None
# ----------------------
def none_if_any(value):
    return None if value == "Any" else value

# ----------------------
# 🚀 Recommender Button
# ----------------------
if st.button("Get My Workout Plan"):
    results = recommend_workouts(
    df,
    type_filter=none_if_any(workout_type),
    body_part_filter=none_if_any(bodypart),
    equipment_filter=none_if_any(equipment),
    level_filter=none_if_any(level),
    n=num_recommendations
    )

    st.success(f"Here are {num_recommendations} workouts tailored to your needs 💥")

    st.dataframe(results[['Title', 'Type', 'Level', 'BodyPart', 'Equipment']])

    st.markdown("### 🎥 Video Previews")
    for _, row in results.iterrows():
        st.markdown(f"**{row['Title']}**")
        videos = fetch_youtube_video(row["Title"])
        if videos:
            st.video(videos[0][1])
        else:
            st.write("No video found.")

    if 'Desc' in results.columns:
        with st.expander("📝 View Descriptions"):
            for _, row in results.iterrows():
                desc = row['Desc'] if pd.notnull(row['Desc']) else 'No description available'
                st.markdown(f"**{row['Title']}**: {desc}")
