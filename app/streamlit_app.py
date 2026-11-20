import os
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# ----------------------
# Page Config (must be the first Streamlit command)
# ----------------------
st.set_page_config(page_title="Workout Recommender", layout="centered")

# ----------------------
# Import Local Module
# ----------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
from models.recommender import filter_mask, recommend_workouts  # noqa: E402

DATA_PATH = ROOT_DIR / "data" / "cleaned_gym_exercise_data.csv"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_CACHE_TTL = 60 * 60 * 24 * 7  # one week; each search costs 100 quota units


# ----------------------
# Load API Key
# ----------------------
def get_youtube_api_key():
    """Return the YouTube API key, or None if it isn't configured."""
    try:
        return st.secrets["api"]["youtube_key"]
    except Exception:
        return os.environ.get("YOUTUBE_API_KEY")


YOUTUBE_API_KEY = get_youtube_api_key()


# ----------------------
# Load Data
# ----------------------
@st.cache_data
def load_data(path):
    return pd.read_csv(path)


df = load_data(DATA_PATH)

# ----------------------
# App Header
# ----------------------
st.title("Personal Workout Recommender")
st.markdown("""
Welcome to your AI-powered workout guide.
Looking for a good workout to do today? I've got you covered!
Just give me the details below and I'll have it ready.
""")

# ----------------------
# User Inputs
# ----------------------
# Each filter: session_state key -> (DataFrame column, recommender keyword argument)
FILTERS = {
    "workout_type": ("Type", "type_filter"),
    "level": ("Level", "level_filter"),
    "bodypart": ("BodyPart", "body_part_filter"),
    "equipment": ("Equipment", "equipment_filter"),
}


def none_if_any(value):
    """Convert the 'Any' option (or an empty multiselect) to None."""
    return None if value in ("Any", None, []) else value


def selected_filters(exclude=None):
    """Recommender kwargs for the current widget values, optionally leaving one filter out.

    Widget values are read from session_state, which Streamlit updates *before*
    the rerun starts, so this is accurate even for widgets drawn later on the page.
    """
    return {
        kwarg: none_if_any(st.session_state.get(key))
        for key, (_, kwarg) in FILTERS.items()
        if key != exclude
    }


def facet_counts(key):
    """How many exercises each option of ``key`` would match, given the other filters."""
    column = FILTERS[key][0]
    subset = df[filter_mask(df, **selected_filters(exclude=key))]
    return subset[column].value_counts(), len(subset)


def options_for(key):
    return sorted(df[FILTERS[key][0]].dropna().unique())


def filter_selectbox(label, key):
    counts, total = facet_counts(key)
    return st.selectbox(
        label,
        options=["Any"] + options_for(key),
        format_func=lambda v: f"Any ({total})" if v == "Any" else f"{v} ({counts.get(v, 0)})",
        key=key,
    )


col1, col2 = st.columns(2)
with col1:
    filter_selectbox("Type of Workout", "workout_type")
    filter_selectbox("Your Fitness Level", "level")
with col2:
    filter_selectbox("Target Body Part", "bodypart")
    equipment_counts, _ = facet_counts("equipment")
    st.multiselect(
        "Equipment Available",
        options=options_for("equipment"),
        format_func=lambda v: f"{v} ({equipment_counts.get(v, 0)})",
        placeholder="Any equipment",
        help="Pick everything you have access to. Leave empty for any equipment.",
        key="equipment",
    )

st.caption(f"**{filter_mask(df, **selected_filters()).sum()}** exercises match your filters.")

num_recommendations = st.slider("Number of Recommendations", 1, 10, 5)


# ----------------------
# YouTube API Helper
# ----------------------
class YouTubeError(Exception):
    pass


@st.cache_data(ttl=VIDEO_CACHE_TTL, show_spinner=False)
def fetch_youtube_video(query, max_results=1):
    """Search YouTube for ``query``. Raises YouTubeError on failure.

    Only successful responses are cached (Streamlit doesn't cache exceptions),
    so a transient error or exhausted quota won't stick around.
    """
    params = {
        "part": "snippet",
        "q": query + " workout",
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }
    try:
        response = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
    except requests.RequestException as exc:
        raise YouTubeError(f"Could not reach YouTube: {exc.__class__.__name__}") from exc

    if not response.ok:
        try:
            error = response.json().get("error", {})
            reason = (error.get("errors") or [{}])[0].get("reason", "")
            message = error.get("message", response.reason)
        except ValueError:
            reason, message = "", response.reason
        if reason in ("quotaExceeded", "dailyLimitExceeded"):
            raise YouTubeError("The daily YouTube API quota has been used up. Try again tomorrow.")
        raise YouTubeError(f"YouTube API error ({response.status_code}): {message}")

    videos = []
    for item in response.json().get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if video_id:
            title = item.get("snippet", {}).get("title", "")
            videos.append((title, f"https://www.youtube.com/watch?v={video_id}"))
    return videos


# ----------------------
# Recommender Button
# ----------------------
# Results live in session_state so they survive reruns triggered by other widgets.
if st.button("Get My Workout Plan"):
    st.session_state["results"] = recommend_workouts(df, **selected_filters(), n=num_recommendations)
    st.session_state["requested"] = num_recommendations

results = st.session_state.get("results")

if results is not None:
    found = len(results)
    requested = st.session_state.get("requested", found)

    if found == 0:
        st.warning("No workouts match those filters. Try setting one or more of them to **Any**.")
    else:
        noun = "workout" if found == 1 else "workouts"
        if found < requested:
            st.info(
                f"Only {found} {noun} match those filters (you asked for {requested}). "
                "Loosen a filter to see more."
            )
        else:
            st.success(f"Here {'is' if found == 1 else 'are'} {found} {noun} tailored to your needs 💥")

        st.dataframe(results[['Title', 'Type', 'Level', 'BodyPart', 'Equipment']], hide_index=True)

        st.markdown("### 🎥 Video Previews")
        if not YOUTUBE_API_KEY:
            st.info(
                "Video previews are disabled: no YouTube API key configured. "
                "Add `[api] youtube_key` to `.streamlit/secrets.toml` or set `YOUTUBE_API_KEY`."
            )
        else:
            for _, row in results.iterrows():
                st.markdown(f"**{row['Title']}**")
                try:
                    with st.spinner("Finding a video..."):
                        videos = fetch_youtube_video(row["Title"])
                except YouTubeError as exc:
                    st.warning(str(exc))
                    break  # the remaining lookups would fail the same way
                if videos:
                    st.video(videos[0][1])
                else:
                    st.write("No video found.")

        if 'Desc' in results.columns:
            with st.expander("📝 View Descriptions"):
                for _, row in results.iterrows():
                    desc = row['Desc'] if pd.notnull(row['Desc']) else 'No description available'
                    st.markdown(f"**{row['Title']}**: {desc}")
