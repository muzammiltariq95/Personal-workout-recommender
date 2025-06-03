import pandas as pd
from models.recommender import recommend_workouts

# Load your cleaned dataset
df = pd.read_csv('data/cleaned_gym_exercise_data.csv')

# Example test input
results = recommend_workouts(
    df,
    workout_type='Strength',
    level='Intermediate',
    bodypart='Legs',
    equipment='Dumbbell',
    n=5
)

# Show the result
print("\nRecommended Workouts:\n")
print(results[['Title', 'Type', 'Level', 'BodyPart', 'Equipment']])
