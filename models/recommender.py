import pandas as pd

def recommend_workouts(
    df,
    type_filter=None,
    body_part_filter=None,
    equipment_filter=None,
    level_filter=None,
    n=5
    ):
    filtered_df = df.copy()

    if type_filter:
        filtered_df = filtered_df[filtered_df["Type"] == type_filter]
    if body_part_filter:
        filtered_df = filtered_df[filtered_df["BodyPart"] == body_part_filter]
    if equipment_filter:
        filtered_df = filtered_df[filtered_df["Equipment"] == equipment_filter]
    if level_filter:
        filtered_df = filtered_df[filtered_df["Level"] == level_filter]

    return filtered_df.sample(n=min(n, len(filtered_df)))