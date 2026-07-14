"""
Links
------
Centralized reference for every external URL / API endpoint the app talks
to, so they live in one place instead of being hardcoded inside individual
services. Other modules (fact_checker, topic_generator, etc.) import from
here rather than defining their own URL constants.
"""

# ---------------------------------------------------------------------------
# Wikipedia API (used by app/services/fact_checker.py)
# ---------------------------------------------------------------------------
WIKIPEDIA_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKIPEDIA_ARTICLE_URL = "https://en.wikipedia.org/wiki/{title}"

# ---------------------------------------------------------------------------
# Google Gemini API (used by app/services/topic_generator.py)
# ---------------------------------------------------------------------------
GEMINI_API_KEY_SIGNUP_URL = "https://aistudio.google.com/app/apikey"
GEMINI_DOCS_URL = "https://ai.google.dev/gemini-api/docs"

# ---------------------------------------------------------------------------
# Hugging Face model reference (used by app/services/event_analyzer.py)
# ---------------------------------------------------------------------------
DISTILBERT_MODEL_CARD_URL = "https://huggingface.co/typeform/distilbert-base-uncased-mnli"

# ---------------------------------------------------------------------------
# Project / documentation links
# ---------------------------------------------------------------------------
PROJECT_REPO_URL = "https://github.com/your-org/personalized-networking-assistant"
FASTAPI_DOCS_URL = "https://fastapi.tiangolo.com/"
STREAMLIT_DOCS_URL = "https://docs.streamlit.io/"


def all_external_links() -> dict:
    """
    Handy helper (e.g. for an 'About' page or footer in the Streamlit app)
    that returns every external link the app references, grouped by
    category.
    """
    return {
        "Wikipedia API": {
            "search": WIKIPEDIA_SEARCH_URL,
            "summary": WIKIPEDIA_SUMMARY_URL,
        },
        "Gemini API": {
            "get_api_key": GEMINI_API_KEY_SIGNUP_URL,
            "docs": GEMINI_DOCS_URL,
        },
        "DistilBERT model": {
            "model_card": DISTILBERT_MODEL_CARD_URL,
        },
        "Project": {
            "repository": PROJECT_REPO_URL,
            "fastapi_docs": FASTAPI_DOCS_URL,
            "streamlit_docs": STREAMLIT_DOCS_URL,
        },
    }
