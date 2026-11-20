"""YouTube Data API helpers for exercise video previews."""

from urllib.parse import quote_plus

import requests
import streamlit as st

YOUTUBE_SEARCH_API = "https://www.googleapis.com/youtube/v3/search"
VIDEO_CACHE_TTL = 60 * 60 * 24 * 7  # one week; each API search costs 100 quota units


class YouTubeError(Exception):
    pass


def search_query(exercise_title):
    return f"{exercise_title} workout"


def youtube_search_url(exercise_title):
    """A plain YouTube search link. Needs no API key or quota."""
    return f"https://www.youtube.com/results?search_query={quote_plus(search_query(exercise_title))}"


@st.cache_data(ttl=VIDEO_CACHE_TTL, show_spinner=False)
def fetch_youtube_video(exercise_title, api_key, max_results=1):
    """Search YouTube for an exercise and return a list of ``(title, url)``.

    Raises YouTubeError on failure. Only successful responses are cached
    (Streamlit doesn't cache exceptions), so a transient error or exhausted
    quota won't stick around.
    """
    params = {
        "part": "snippet",
        "q": search_query(exercise_title),
        "type": "video",
        "maxResults": max_results,
        "key": api_key,
    }
    try:
        response = requests.get(YOUTUBE_SEARCH_API, params=params, timeout=10)
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
