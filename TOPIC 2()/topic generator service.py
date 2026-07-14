"""
Topic Generator Service
-------------------------
Scenario 1 (part 2): takes the themes extracted by the event_analyzer
service plus the user's interests, and generates 2-3 natural,
context-aware conversation starters.

Supports two interchangeable backends:
  - "gpt2"   (default): local Hugging Face GPT-2 Small text-generation
              pipeline -- matches the official project spec, runs fully
              offline once the model is downloaded, no API key needed.
  - "gemini": Google Gemini API -- higher-quality generations, but
              requires a GEMINI_API_KEY and network access.

The backend can be chosen per-request (see ConversationStarterRequest.backend)
or via the GENERATION_BACKEND environment variable. Defaults to "gpt2".
"""

import os
import re
from functools import lru_cache
from typing import List, Optional

from transformers import pipeline as hf_pipeline

from app.schemas import ConversationStarter

GPT2_MODEL_NAME = "gpt2"  # GPT-2 Small
GEMINI_MODEL_NAME = "gemini-1.5-flash"

_gemini_configured = False


# ---------------------------------------------------------------------------
# GPT-2 backend (default)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_gpt2_generator():
    """
    Lazily load the GPT-2 Small text-generation pipeline once and cache it.
    """
    return hf_pipeline("text-generation", model=GPT2_MODEL_NAME)


def _build_gpt2_prompt(event_description: str, themes: List[str], interests: List[str]) -> str:
    themes_str = ", ".join(themes) if themes else "networking"
    interests_str = ", ".join(interests) if interests else "general topics"
    return (
        f"Networking event: {event_description}. Key themes: {themes_str}. "
        f"Attendee interests: {interests_str}. "
        f"A great conversation starter to open with is:"
    )


def _clean_gpt2_continuation(full_text: str, prompt: str) -> str:
    """Strip the prompt back off GPT-2's output and trim to a single line."""
    continuation = full_text[len(prompt):].strip()
    # GPT-2 tends to ramble on -- keep just the first sentence-like chunk.
    continuation = continuation.split("\n")[0].strip()
    for stop_char in [". ", "? ", "! "]:
        if stop_char in continuation:
            continuation = continuation.split(stop_char)[0] + stop_char.strip()
            break
    return continuation.strip(' "')


def _generate_with_gpt2(
    event_description: str, themes: List[str], interests: List[str], num_starters: int
) -> List[str]:
    generator = _get_gpt2_generator()
    prompt = _build_gpt2_prompt(event_description, themes, interests)

    outputs = generator(
        prompt,
        max_new_tokens=40,
        num_return_sequences=num_starters,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=0.9,
        pad_token_id=generator.tokenizer.eos_token_id,
    )

    starters = []
    for output in outputs:
        cleaned = _clean_gpt2_continuation(output["generated_text"], prompt)
        if cleaned:
            starters.append(cleaned)

    return starters


# ---------------------------------------------------------------------------
# Gemini backend (optional)
# ---------------------------------------------------------------------------

def _configure_gemini() -> None:
    """Configure the Gemini SDK with the API key from the environment."""
    global _gemini_configured
    if _gemini_configured:
        return

    import google.generativeai as genai  # imported lazily so GPT-2-only setups don't need this package

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file "
            "(see .env.example) to use the 'gemini' backend."
        )
    genai.configure(api_key=api_key)
    _gemini_configured = True


def _build_gemini_prompt(event_description: str, themes: List[str], interests: List[str], num_starters: int) -> str:
    themes_str = ", ".join(themes) if themes else "general networking"
    interests_str = ", ".join(interests) if interests else "no specific interests provided"

    return (
        f"You are a networking coach helping someone prepare for an event.\n"
        f"Event description: \"{event_description}\"\n"
        f"Key themes detected: {themes_str}\n"
        f"Attendee's personal interests: {interests_str}\n\n"
        f"Generate exactly {num_starters} short, natural conversation starters "
        f"(1-2 sentences each) this person could use to open a conversation "
        f"with another attendee. Make them specific to the themes and "
        f"interests above, friendly, and non-generic. "
        f"Return them as a numbered list, one starter per line, "
        f"with no extra commentary before or after the list."
    )


def _parse_numbered_list(raw_text: str) -> List[str]:
    """Turn Gemini's numbered-list output into a clean list of strings."""
    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    cleaned = []
    for line in lines:
        stripped = re.sub(r"^[\d]+[\.\)]\s*|^[-*]\s*", "", line).strip()
        if stripped:
            cleaned.append(stripped)
    return cleaned


def _generate_with_gemini(
    event_description: str, themes: List[str], interests: List[str], num_starters: int
) -> List[str]:
    import google.generativeai as genai

    _configure_gemini()

    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    prompt = _build_gemini_prompt(event_description, themes, interests, num_starters)
    response = model.generate_content(prompt)

    return _parse_numbered_list(response.text)[:num_starters]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_starters(
    event_description: str,
    themes: List[str],
    interests: List[str],
    num_starters: int = 3,
    backend: Optional[str] = None,
) -> List[ConversationStarter]:
    """
    Generate `num_starters` conversation starters using the requested
    backend ("gpt2" or "gemini"). Defaults to GPT-2, falling back to the
    GENERATION_BACKEND environment variable if `backend` isn't passed in.
    """
    backend = (backend or os.getenv("GENERATION_BACKEND", "gpt2")).lower()

    if backend == "gemini":
        starter_texts = _generate_with_gemini(event_description, themes, interests, num_starters)
    elif backend == "gpt2":
        starter_texts = _generate_with_gpt2(event_description, themes, interests, num_starters)
    else:
        raise ValueError(f"Unknown backend '{backend}'. Use 'gpt2' or 'gemini'.")

    starters = []
    for i, text in enumerate(starter_texts[:num_starters]):
        theme = themes[i % len(themes)] if themes else None
        starters.append(ConversationStarter(text=text, based_on_theme=theme))

    return starters
