# Personal Workout Recommender

[![CI](https://github.com/muzammiltariq95/Personal-workout-recommender/actions/workflows/ci.yml/badge.svg)](https://github.com/muzammiltariq95/Personal-workout-recommender/actions/workflows/ci.yml)
<!-- After deploying (see "Deploying" below), add a live demo badge here:
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR-APP.streamlit.app) -->

<img width="897" height="540" alt="Screenshot 2025-10-12 154016" src="https://github.com/user-attachments/assets/e3e77e27-1dc3-4a54-a145-5bb8583da178" />

This is an AI-powered workout recommendation app built using **Python**, **Pandas**, and **Streamlit**. The app allows users to receive personalized workout suggestions based on their fitness level, equipment availability, and target body area.

## Features

- Filter workouts by Type, Level, Body Part, and Equipment
- Select all the equipment you have access to, not just one item
- Live match counts next to every filter option, so you never pick a combination with no results
- See tailored workout recommendations
- Get real-time **YouTube** video previews for each recommended exercise (cached to save API quota)
- Cleaned and structured gym dataset
- Interactive Streamlit interface

## Tech Stack

- Python
- Pandas
- Streamlit
- YouTube Data API

## Getting Started

### 1. Install dependencies

Requires Python 3.10+.

```bash
git clone https://github.com/muzammiltariq95/Personal-workout-recommender.git
cd Personal-workout-recommender
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add a YouTube API key (optional)

Video previews use the [YouTube Data API v3](https://developers.google.com/youtube/v3/getting-started). Without a key the app still works, but video previews are turned off.

Create `.streamlit/secrets.toml` (it is git-ignored):

```toml
[api]
youtube_key = "YOUR_API_KEY"
```

Or set it as an environment variable:

```bash
export YOUTUBE_API_KEY="YOUR_API_KEY"
```

> Each YouTube search costs 100 units out of the free 10,000 daily quota. Results are cached for a week, so the same exercise is only looked up once.

### 3. Run the app

```bash
streamlit run app/streamlit_app.py
```

The app opens at http://localhost:8501. It can be launched from any directory.

You can also open the repo in a GitHub Codespace or VS Code Dev Container. The included `.devcontainer` installs the dependencies and starts the app automatically.

## Running Tests and Linting

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

Both run automatically on every push and pull request via GitHub Actions (`.github/workflows/ci.yml`).

## Deploying

The app is ready to deploy on [Streamlit Community Cloud](https://share.streamlit.io) for free:

1. Sign in with GitHub and click **Create app**.
2. Choose this repository, branch `main`, and main file path `app/streamlit_app.py`.
3. Under **Advanced settings**, pick Python 3.11 or newer and paste your secrets:
   ```toml
   [api]
   youtube_key = "YOUR_API_KEY"
   ```
4. Deploy. Dependencies are installed from `requirements.txt`.

## Project Structure

```
├── .github/workflows/ci.yml    # Lint + test on every push
├── app/
│   └── streamlit_app.py        # Streamlit UI and YouTube integration
├── models/
│   └── recommender.py          # Recommendation logic
├── data/
│   ├── megaGymDataset.csv            # Raw dataset
│   └── cleaned_gym_exercise_data.csv # Cleaned dataset used by the app
├── notebooks/
│   └── Fitness-recommender system.ipynb  # Data exploration and cleaning
├── test_recommender.py         # Unit tests
├── requirements.txt
├── requirements-dev.txt
└── ruff.toml                   # Lint configuration
```

To regenerate the cleaned dataset, run the notebook from inside the `notebooks/` folder. It reads and writes files in `../data/`.

## Screenshots

<img width="990" height="744" alt="Screenshot 2025-10-12 154208" src="https://github.com/user-attachments/assets/c26b2506-5ff7-489e-b473-2f99a1559522" />
<img width="1100" height="852" alt="Screenshot 2025-10-12 154238" src="https://github.com/user-attachments/assets/5a5504ec-b890-4de5-b228-946c804db38a" />
