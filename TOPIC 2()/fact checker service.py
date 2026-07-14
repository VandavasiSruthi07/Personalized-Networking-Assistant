"""
Fact Checker Service
---------------------
Scenario 2: given a quick query like "blockchain in healthcare", look it
up using the `wikipedia` Python wrapper package for a summarized,
reliable reference the user can skim before a conversation.
"""

import wikipedia

from app.schemas import FactCheckResult

SUMMARY_SENTENCES = 3


def fact_check(query: str) -> FactCheckResult:
    """
    Look up `query` on Wikipedia and return a short, reliable summary.
    Returns found=False (with a friendly message) if nothing turns up,
    and gracefully handles disambiguation pages by picking the first
    suggested option.
    """
    try:
        search_results = wikipedia.search(query, results=1)
        if not search_results:
            return FactCheckResult(
                query=query,
                summary="No relevant Wikipedia article was found for this query.",
                found=False,
            )

        title = search_results[0]
        page = wikipedia.page(title, auto_suggest=False)
        summary = wikipedia.summary(title, sentences=SUMMARY_SENTENCES, auto_suggest=False)

        return FactCheckResult(
            query=query,
            summary=summary,
            source_title=page.title,
            source_url=page.url,
            found=True,
        )

    except wikipedia.DisambiguationError as exc:
        # Multiple articles matched -- just take the first suggested option
        # rather than failing outright.
        if not exc.options:
            return FactCheckResult(
                query=query,
                summary="Multiple matching articles were found; please refine your query.",
                found=False,
            )
        try:
            option = exc.options[0]
            page = wikipedia.page(option, auto_suggest=False)
            summary = wikipedia.summary(option, sentences=SUMMARY_SENTENCES, auto_suggest=False)
            return FactCheckResult(
                query=query,
                summary=summary,
                source_title=page.title,
                source_url=page.url,
                found=True,
            )
        except Exception:
            return FactCheckResult(
                query=query,
                summary="Multiple matching articles were found; please refine your query.",
                found=False,
            )

    except wikipedia.PageError:
        return FactCheckResult(
            query=query,
            summary="No relevant Wikipedia article was found for this query.",
            found=False,
        )
