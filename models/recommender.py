import pandas as pd

def recommend_workouts(df, workout_type=None, level=None, bodypart=None, equipment=None, n=5):
    filtered = df.copy()

    if workout_type:
        filtered = filtered[filtered['Type'].str.lower() == workout_type.lower()]
    if level:
        filtered = filtered[filtered['Level'].str.lower() == level.lower()]
    if bodypart:
        filtered = filtered[filtered['BodyPart'].str.lower() == bodypart.lower()]
    if equipment:
        filtered = filtered[filtered['Equipment'].fillna('unknown').str.lower().str.contains(equipment.lower())]

    if filtered.empty:
        return df.sample(n)

    return filtered.sample(n)
