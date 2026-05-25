# Polarized-Emotional-Communities-Around-AI-Job-Replacement-and-Who-Are-the-Influential-Users-



# SMNA Assignment 2
## Do Polarized Emotional Communities Form Around AI Job Replacement Discussions on YouTube, and Who Are the Influential Users Shaping These Communities?

**Course:** COSC 2671 / COSC 3047 — Social Media and Network Analysis  
**Data Sources:** YouTube (Data API v3) + Bluesky (AT Protocol)  
**Language:** Python 3.9+

---

## Project Structure

```
smna_assignment2/
│
├── SMNA_Assignment2_Main.ipynb     ← Main notebook (run this)
├── requirements.txt
├── colab_setup.py                  ← Colab helper reference
│
├── data_collection/
│   ├── youtube_collector.py        ← YouTube Data API v3 client
│   └── bluesky_collector.py        ← Bluesky AT Protocol client
│
├── nlp_analysis/
│   ├── preprocessor.py             ← Text cleaning & lemmatisation
│   ├── sentiment.py                ← VADER sentiment analysis
│   └── topic_modeller.py           ← LDA topic modelling
│
├── network_analysis/
│   ├── graph_builder.py            ← YouTube/Bluesky graph construction
│   ├── centrality.py               ← All centrality measures (PG requirement)
│   ├── community_detector.py       ← Louvain community detection
│   ├── community_sentiment.py      ← Sentiment per community
│   ├── influence_roles.py          ← Bridge/Hub/Authority role classifier
│   ├── visualiser.py               ← Network visualisation
│   └── stats.py                    ← Network summary statistics
│
├── sample_data/
│   ├── youtube_comments.csv        ← 35 realistic sample comments (no API needed)
│   ├── youtube_videos.csv          ← 2 sample videos
│   └── bluesky_posts.csv           ← 20 realistic sample posts
│
└── outputs/                        ← All generated figures and CSVs saved here
```

---

## Quick Start: Running on Sample Data (No API Key Required)

The `sample_data/` folder contains realistic pre-collected data.  
If the CSV files already exist in `sample_data/`, the notebook **skips the API calls** and loads cached data automatically.

---

## Option A: VS Code (Local)

### Prerequisites
- Python 3.9 or higher
- VS Code with the **Jupyter** extension installed

### Step-by-step

**1. Install dependencies**
```bash
cd smna_assignment2
pip install -r requirements.txt
```

**2. (Optional) Set API keys**

If you want to collect fresh data, set environment variables before opening VS Code:

*macOS/Linux:*
```bash
export YOUTUBE_API_KEY="your_actual_key_here"
export BSKY_HANDLE="yourhandle.bsky.social"   # optional
export BSKY_APP_PASS="your-app-password"       # optional
```

*Windows PowerShell:*
```powershell
$env:YOUTUBE_API_KEY = "your_actual_key_here"
$env:BSKY_HANDLE     = "yourhandle.bsky.social"
$env:BSKY_APP_PASS   = "your-app-password"
```

You can also edit the keys directly in **Cell 1** of the notebook (Config section) — but do not commit keys to any repository.

**3. Open and run**
```bash
code .
```
- Open `SMNA_Assignment2_Main.ipynb`
- Select your Python interpreter (top right of notebook)
- Click **Run All** or run cells sequentially with `Shift+Enter`

**4. Outputs**
All figures (PNG) and data CSVs are saved to the `outputs/` folder automatically.

---

## Option B: Google Colab

### Step 1 — Upload the zip to Google Drive
Upload `smna_assignment2.zip` to your Google Drive (e.g. `My Drive/smna_assignment2.zip`).

### Step 2 — Open a new Colab notebook and run this setup

Paste and run each block as a separate cell:

```python
# Cell 1 — Install extra packages (not pre-installed in Colab)
!pip install vaderSentiment python-louvain textblob google-api-python-client --quiet
```

```python
# Cell 2 — Mount your Google Drive
from google.colab import drive
drive.mount('/content/drive')
```

```python
# Cell 3 — Unzip the project
import zipfile, os

zip_path   = '/content/drive/MyDrive/smna_assignment2.zip'  # adjust if needed
extract_to = '/content/smna_assignment2'

with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(extract_to)

os.chdir(extract_to)
print("Working directory:", os.getcwd())
print(os.listdir('.'))
```

```python
# Cell 4 — Set API keys (skip if using sample data only)
import os
os.environ['YOUTUBE_API_KEY'] = 'YOUR_KEY_HERE'  # replace with your key
os.environ['BSKY_HANDLE']     = ''
os.environ['BSKY_APP_PASS']   = ''
```

### Step 3 — Open the main notebook in Colab

```python
# Cell 5 — Open the notebook programmatically
# In Colab: File → Open notebook → Google Drive → navigate to the .ipynb
# OR run it directly:
```

Go to **File → Open notebook → Google Drive** and navigate to  
`smna_assignment2/SMNA_Assignment2_Main.ipynb`

Run all cells from top to bottom.

> **Tip:** In Colab, outputs are saved to `/content/smna_assignment2/outputs/`.  
> Download them via the Files panel on the left, or save to Drive by adjusting `OUTPUT_DIR`.

---

## Getting a YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **YouTube Data API v3**
4. Create credentials → **API Key**
5. Copy the key into Cell 1 of the notebook

> Free tier: 10,000 units/day. Searching uses ~100 units/call; comment pages use ~1 unit.

---

## Getting Bluesky App Password (Optional)

1. Log in to [bsky.app](https://bsky.app)
2. Go to **Settings → App Passwords → Add App Password**
3. Enter `smna-research` as the name, click Create
4. Copy the generated password — you won't see it again

> Bluesky's public API works without authentication for read-only searches.  
> The app password only enables higher rate limits.

---

## Analysis Pipeline Summary

| Step | What It Does |
|------|-------------|
| **Data Collection** | Fetches YouTube comment threads and Bluesky posts matching AI-job queries |
| **Preprocessing** | Cleans, tokenises, removes stopwords, lemmatises text |
| **Sentiment (VADER)** | Scores each comment/post as Positive / Neutral / Negative |
| **Topic Modelling (LDA)** | Identifies 5 latent topics across each platform |
| **Graph Construction** | Builds directed weighted reply graphs (nodes=users, edges=replies/mentions) |
| **Centrality** | Computes in-degree, betweenness, PageRank, eigenvector, HITS hub/authority |
| **Community Detection** | Louvain algorithm on undirected projection; computes modularity Q |
| **Community Sentiment** | Merges community membership with sentiment to detect polarised clusters |
| **Influence Roles** | Classifies users as Bridge / Hub / Authority / Peripheral |
| **Cross-platform** | Compares sentiment × topic heatmaps across YouTube and Bluesky |

---

## Research Question & Success Criteria

**Research Question:**  
Do polarized emotional communities form around AI job replacement discussions on YouTube, and who are the influential users shaping these communities?

**Success Criteria:**
1. At least 2 distinct communities detected with significantly different mean sentiment scores
2.  Identifiable Bridge users (high betweenness) connecting otherwise separate communities
3. Topic modelling reveals distinct frames (fear vs optimism vs policy) across communities
4. Cross-platform comparison shows whether YouTube and Bluesky communities differ in polarisation level

---

## Academic Integrity

- All code is original work using standard open-source libraries
- External packages (NetworkX, VADER, scikit-learn) are acknowledged
- No API keys or private credentials are to be committed to repositories
- Sample data is synthetic but representative; real data is collected via official APIs under platform ToS

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: community` | `pip install python-louvain` |
| `ModuleNotFoundError: vaderSentiment` | `pip install vaderSentiment` |
| YouTube API 403 error | Comments disabled on that video — normal, the collector skips it |
| Bluesky returns 0 posts | Public API rate limit; wait 30s and retry, or add app-password |
| Graph has 0 nodes | Sample data has no reply chains — use the included sample CSVs |
| LDA warning "too few documents" | Need at least `n_topics × 2` non-empty texts |

---

*Last updated: May 2026*
