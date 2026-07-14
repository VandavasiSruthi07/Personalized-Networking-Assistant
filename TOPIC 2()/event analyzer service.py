"""
Event Analyzer Service
-----------------------
Scenario 1 (part 1): given a raw event description like
"AI for Sustainable Cities", extract the key themes (e.g. "AI",
"sustainability") using a local DistilBERT model, then cross-reference
against the user's stated interests.

We use DistilBERT via a zero-shot-classification pipeline. Zero-shot lets us
score the event description against a candidate list of networking/tech
themes without having to fine-tune anything -- perfect for a project like
this where the "labels" (themes) aren't known ahead of time in a fixed
training set.
"""

from functools import lru_cache
from typing import List

from transformers import pipeline

from app.schemas import EventAnalysisResult

# Candidate themes the classifier scores the event description against.
# Feel free to extend this list -- it's the "vocabulary" of themes the
# assistant can recognize.
CANDIDATE_THEMES = [
    "artificial intelligence", "machine learning", "sustainability",
    "climate change", "urban planning", "blockchain", "healthcare",
    "finance", "startups", "entrepreneurship", "cybersecurity",
    "data science", "cloud computing", "product management",
    "marketing", "education technology", "robotics", "biotechnology",
    "renewable energy", "web development",
]

MODEL_NAME = "typeform/distilbert-base-uncased-mnli"


@lru_cache(maxsize=1)
def _get_classifier():
    """
    Lazily load the DistilBERT zero-shot pipeline once and cache it.
    Loading the model is the expensive part, so every request after the
    first reuses this cached pipeline instead of reloading weights.
    """
    return pipeline("zero-shot-classification", model=MODEL_NAME)


def extract_themes(event_description: str, top_k: int = 3, score_threshold: float = 0.15) -> List[str]:
    """
    Run zero-shot classification over CANDIDATE_THEMES and return the
    top_k themes whose confidence score clears score_threshold.
    """
    classifier = _get_classifier()
    result = classifier(event_description, candidate_labels=CANDIDATE_THEMES, multi_label=True)

    themes = [
        label for label, score in zip(result["labels"], result["scores"])
        if score >= score_threshold
    ][:top_k]

    # Guarantee at least one theme so downstream services always have
    # something to work with, even for very short/ambiguous descriptions.
    if not themes:
        themes = [result["labels"][0]]

    return themes


def analyze_event(event_description: str, interests: List[str]) -> EventAnalysisResult:
    """
    Full analyzer pipeline: extract themes, then figure out which of the
    user's stated interests actually line up with the event description
    (simple case-insensitive substring/theme match).
    """
    themes = extract_themes(event_description)

    lowered_description = event_description.lower()
    lowered_themes = [t.lower() for t in themes]

    matched_interests = [
        interest for interest in interests
        if interest.lower() in lowered_description
        or any(interest.lower() in theme or theme in interest.lower() for theme in lowered_themes)
    ]

    return EventAnalysisResult(
        event_description=event_description,
        extracted_themes=themes,
        matched_interests=matched_interests,
    )
