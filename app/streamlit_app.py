import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import pandas as pd
from models.recommender import recommend_workouts

# --- Load the cleaned data ---
df = pd.read_csv('data/cleaned_gym_exercise_data.csv')

# --- App Title ---
st.title("🏋️‍♂️ Personal Workout Recommender")

st.markdown("Tell us a bit about your fitness goals, and we’ll recommend workouts just for you!")

# --- User Inputs ---
type_options = df['Type'].dropna().unique()
level_options = df['Level'].dropna().unique()
bodypart_options = df['BodyPart'].dropna().unique()
equipment_options = df['Equipment'].dropna().unique()

workout_type = st.selectbox("Type of Workout", options=["Any"] + sorted(type_options))
level = st.selectbox("Your Fitness Level", options=["Any"] + sorted(level_options))
bodypart = st.selectbox("Target Body Part", options=["Any"] + sorted(bodypart_options))
equipment = st.selectbox("Available Equipment", options=["Any"] + sorted(equipment_options))
num_recommendations = st.slider("How many workouts would you like?", 1, 10, 5)

# --- Filter to None if "Any" is selected ---
def none_if_any(value):
    return None if value == "Any" else value

# --- Generate Recommendations ---
if st.button("Get Recommendations"):
    recommendations = recommend_workouts(
        df,
        workout_type=none_if_any(workout_type),
        level=none_if_any(level),
        bodypart=none_if_any(bodypart),
        equipment=none_if_any(equipment),
        n=num_recommendations
    )

    st.subheader("💡 Recommended Workouts")
    st.dataframe(recommendations[['Title', 'Type', 'Level', 'BodyPart', 'Equipment']])