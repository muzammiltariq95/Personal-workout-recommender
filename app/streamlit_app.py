import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ----------------------
# Page Config (must be the first Streamlit command)
# ----------------------
st.set_page_config(page_title="Workout Recommender", page_icon="💪", layout="centered")

# ----------------------
# Import Local Modules
# ----------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
from app.youtube import YouTubeError, fetch_youtube_video, youtube_search_url  # noqa: E402
from models.recommender import filter_mask, recommend_workouts  # noqa: E402

DATA_PATH = ROOT_DIR / "data" / "cleaned_gym_exercise_data.csv"
DISPLAY_COLUMNS = ["Title", "Type", "Level", "BodyPart", "Equipment"]
LEVEL_COLORS = {"Beginner": "green", "Intermediate": "orange", "Expert": "red"}
CARD_STATE_PREFIXES = ("done_", "video_")


# ----------------------
# Load API Key and Data
# ----------------------
def get_youtube_api_key():
    """Return the YouTube API key, or None if it isn't configured."""
    try:
        return st.secrets["api"]["youtube_key"]
    except Exception:
        return os.environ.get("YOUTUBE_API_KEY")


@st.cache_data
def load_data(path):
    return pd.read_csv(path)


YOUTUBE_API_KEY = get_youtube_api_key()
df = load_data(DATA_PATH)

# ----------------------
# Filters
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


def describe_filters(filters):
    parts = [
        ", ".join(value) if isinstance(value, list) else value
        for value in filters.values()
        if value
    ]
    return " · ".join(parts) if parts else "No filters"


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


# ----------------------
# Plan Actions (button callbacks run before the page is redrawn)
# ----------------------
def reset_card_state():
    for key in list(st.session_state):
        if key.startswith(CARD_STATE_PREFIXES):
            del st.session_state[key]


def build_plan(filters, requested):
    reset_card_state()
    st.session_state["plan"] = {"filters": filters, "requested": requested}
    st.session_state["results"] = recommend_workouts(df, **filters, n=requested)


def generate_plan():
    build_plan(selected_filters(), st.session_state["num_recommendations"])


def shuffle_plan():
    plan = st.session_state["plan"]
    build_plan(plan["filters"], plan["requested"])


def swap_exercise(idx):
    """Replace one exercise with another that matches the plan's filters."""
    results = st.session_state["results"]
    pool = df[filter_mask(df, **st.session_state["plan"]["filters"])].drop(index=results.index)
    if pool.empty:
        st.toast("No other exercises match these filters. Loosen a filter to get more options.", icon="🤷")
        return
    replacement = pool.sample(1)
    position = results.index.get_loc(idx)
    st.session_state["results"] = pd.concat([results.iloc[:position], replacement, results.iloc[position + 1:]])
    for prefix in CARD_STATE_PREFIXES:
        st.session_state.pop(f"{prefix}{idx}", None)


# ----------------------
# Export
# ----------------------
def plan_to_markdown(results, filters):
    lines = ["# My Workout", "", f"_{describe_filters(filters)}_", ""]
    for number, (_, row) in enumerate(results.iterrows(), start=1):
        tags = " · ".join(str(row[c]) for c in ["BodyPart", "Equipment", "Level"] if pd.notnull(row[c]))
        lines.append(f"{number}. **{row['Title']}** ({tags})")
        if pd.notnull(row["Desc"]):
            lines.append(f"   {row['Desc']}")
        lines.append("")
    return "\n".join(lines)


# ----------------------
# Exercise Card
# ----------------------
def render_video(title):
    try:
        with st.spinner("Finding a video..."):
            videos = fetch_youtube_video(title, YOUTUBE_API_KEY)
    except YouTubeError as exc:
        st.warning(str(exc))
        st.link_button("Search on YouTube instead", youtube_search_url(title))
        return
    if videos:
        st.video(videos[0][1])
    else:
        st.caption("No video found.")
        st.link_button("Search on YouTube", youtube_search_url(title))


def render_card(number, idx, row):
    done = st.session_state.get(f"done_{idx}", False)
    with st.container(border=True):
        heading = f"{number}. {row['Title']}"
        st.markdown(f"#### ~~{heading}~~" if done else f"#### {heading}")

        with st.container(horizontal=True, gap="small"):
            st.badge(row["BodyPart"], icon=":material/accessibility_new:", color="blue")
            if pd.notnull(row["Equipment"]):
                st.badge(row["Equipment"], icon=":material/fitness_center:", color="gray")
            st.badge(row["Level"], color=LEVEL_COLORS.get(row["Level"], "gray"))
            st.badge(row["Type"], color="violet")

        if pd.notnull(row["Desc"]):
            st.write(row["Desc"])
        else:
            st.caption("No description available.")

        with st.container(horizontal=True, vertical_alignment="center"):
            st.checkbox("Done", key=f"done_{idx}")
            if YOUTUBE_API_KEY:
                st.toggle("🎥 Show video", key=f"video_{idx}")
            else:
                st.link_button("🎥 Find on YouTube", youtube_search_url(row["Title"]))
            st.button(
                "🔀 Swap",
                key=f"swap_{idx}",
                on_click=swap_exercise,
                args=(idx,),
                help="Replace this with another exercise that matches your filters",
            )

        # Videos only load when asked for: each lookup costs YouTube API quota.
        if YOUTUBE_API_KEY and st.session_state.get(f"video_{idx}"):
            render_video(row["Title"])


# ----------------------
# Sidebar: Inputs
# ----------------------
with st.sidebar:
    st.header("🏋️ Build your workout")
    filter_selectbox("Type of Workout", "workout_type")
    filter_selectbox("Your Fitness Level", "level")
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
    st.slider("Number of exercises", 1, 10, 5, key="num_recommendations")

    matching = int(filter_mask(df, **selected_filters()).sum())
    st.caption(f"**{matching}** exercises match your filters.")
    st.button(
        "Generate workout",
        type="primary",
        icon="⚡",
        width="stretch",
        on_click=generate_plan,
        disabled=matching == 0,
    )

# ----------------------
# Main Area
# ----------------------
st.title("💪 Personal Workout Recommender")
st.markdown(
    "Looking for a good workout to do today? I've got you covered! "
    "Set your preferences in the sidebar and I'll put a session together."
)

workout_tab, library_tab = st.tabs(["🏋️ Your Workout", "📚 Exercise Library"])

with workout_tab:
    results = st.session_state.get("results")

    if results is None:
        st.info("👈 Pick your filters in the sidebar, then hit **Generate workout**.")
        col1, col2, col3 = st.columns(3)
        col1.metric("Exercises", f"{len(df):,}")
        col2.metric("Body parts", df["BodyPart"].nunique())
        col3.metric("Equipment types", df["Equipment"].nunique())
    else:
        plan = st.session_state["plan"]
        found, requested = len(results), plan["requested"]
        noun = "exercise" if found == 1 else "exercises"

        if found == 0:
            st.warning("No exercises match those filters. Try setting one or more of them to **Any**.")
        else:
            if found < requested:
                st.info(
                    f"Only {found} {noun} match those filters (you asked for {requested}). "
                    "Loosen a filter to see more."
                )
            st.caption(f"{found} {noun} · {describe_filters(plan['filters'])}")

            done = sum(bool(st.session_state.get(f"done_{idx}")) for idx in results.index)
            st.progress(done / found, text=f"{done} of {found} done")
            if done == found:
                st.success("Workout complete. Nice work! 🎉")

            with st.container(horizontal=True):
                st.button("🔀 Shuffle all", on_click=shuffle_plan, help="Get a fresh set with the same filters")
                st.download_button(
                    "⬇️ Markdown",
                    plan_to_markdown(results, plan["filters"]),
                    file_name="workout.md",
                    mime="text/markdown",
                    on_click="ignore",
                )
                st.download_button(
                    "⬇️ CSV",
                    results[DISPLAY_COLUMNS + ["Desc"]].to_csv(index=False),
                    file_name="workout.csv",
                    mime="text/csv",
                    on_click="ignore",
                )

            for number, (idx, row) in enumerate(results.iterrows(), start=1):
                render_card(number, idx, row)

with library_tab:
    query = st.text_input("Search exercises", placeholder="e.g. lunge, kettlebell swing", key="library_search")
    use_filters = st.toggle("Apply sidebar filters", value=True, key="library_use_filters")

    library = df[filter_mask(df, **selected_filters())] if use_filters else df
    if query:
        library = library[
            library["Title"].str.contains(query, case=False, regex=False)
            | library["Desc"].fillna("").str.contains(query, case=False, regex=False)
        ]

    st.caption(f"{len(library):,} exercises")
    st.dataframe(
        library[DISPLAY_COLUMNS + ["Desc"]].fillna({"Desc": ""}),
        hide_index=True,
        height=520,
        column_config={
            "Title": st.column_config.TextColumn("Exercise", width="medium"),
            "BodyPart": "Body part",
            "Desc": st.column_config.TextColumn("Description", width="large"),
        },
    )
