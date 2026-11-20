import pandas as pd


def filter_mask(
    df,
    type_filter=None,
    body_part_filter=None,
    equipment_filter=None,
    level_filter=None,
):
    """Return a boolean Series marking rows that match every filter that is set.

    Filters left as ``None`` (or empty) are ignored. ``equipment_filter`` may be
    a single value or a list of values; a row matches if its equipment is any
    of them.
    """
    mask = pd.Series(True, index=df.index)
    if type_filter:
        mask &= df["Type"] == type_filter
    if body_part_filter:
        mask &= df["BodyPart"] == body_part_filter
    if equipment_filter:
        if isinstance(equipment_filter, str):
            equipment_filter = [equipment_filter]
        mask &= df["Equipment"].isin(equipment_filter)
    if level_filter:
        mask &= df["Level"] == level_filter
    return mask


def recommend_workouts(
    df,
    type_filter=None,
    body_part_filter=None,
    equipment_filter=None,
    level_filter=None,
    n=5,
    random_state=None,
):
    """Return up to ``n`` random exercises matching every filter that is set.

    See ``filter_mask`` for how filters are applied. If fewer than ``n``
    exercises match, all matches are returned (possibly an empty DataFrame).
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")

    filtered_df = df[filter_mask(df, type_filter, body_part_filter, equipment_filter, level_filter)]
    return filtered_df.sample(n=min(n, len(filtered_df)), random_state=random_state)
