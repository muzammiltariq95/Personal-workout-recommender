from pathlib import Path

import pandas as pd
import pytest

from models.recommender import filter_mask, recommend_workouts

DATA_PATH = Path(__file__).resolve().parent / "data" / "cleaned_gym_exercise_data.csv"


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(DATA_PATH)


def test_filters_are_respected(df):
    results = recommend_workouts(
        df,
        type_filter="Strength",
        level_filter="Intermediate",
        body_part_filter="Quadriceps",
        equipment_filter="Dumbbell",
        n=5,
        random_state=0,
    )
    assert len(results) == 5
    assert (results["Type"] == "Strength").all()
    assert (results["Level"] == "Intermediate").all()
    assert (results["BodyPart"] == "Quadriceps").all()
    assert (results["Equipment"] == "Dumbbell").all()


def test_no_filters_returns_n(df):
    assert len(recommend_workouts(df, n=7, random_state=0)) == 7


def test_returns_fewer_when_not_enough_matches(df):
    expert = df[df["Level"] == "Expert"]
    results = recommend_workouts(df, level_filter="Expert", n=len(expert) + 50)
    assert len(results) == len(expert)


def test_no_matches_returns_empty(df):
    results = recommend_workouts(df, body_part_filter="Not a body part", n=5)
    assert results.empty


def test_no_duplicate_rows(df):
    results = recommend_workouts(df, n=10, random_state=1)
    assert results.index.is_unique


def test_random_state_is_reproducible(df):
    a = recommend_workouts(df, n=5, random_state=42)
    b = recommend_workouts(df, n=5, random_state=42)
    assert a.index.equals(b.index)


def test_negative_n_raises(df):
    with pytest.raises(ValueError):
        recommend_workouts(df, n=-1)


def test_equipment_accepts_a_list(df):
    owned = ["Dumbbell", "Bands"]
    results = recommend_workouts(df, equipment_filter=owned, n=10, random_state=0)
    assert len(results) == 10
    assert results["Equipment"].isin(owned).all()


def test_equipment_list_matches_any_of_its_items(df):
    single = filter_mask(df, equipment_filter="Dumbbell").sum()
    both = filter_mask(df, equipment_filter=["Dumbbell", "Bands"]).sum()
    assert both == single + (df["Equipment"] == "Bands").sum()


def test_empty_equipment_list_means_any(df):
    assert filter_mask(df, equipment_filter=[]).all()


def test_filter_mask_combines_filters(df):
    mask = filter_mask(df, type_filter="Strength", level_filter="Beginner")
    expected = (df["Type"] == "Strength") & (df["Level"] == "Beginner")
    assert mask.equals(expected)
