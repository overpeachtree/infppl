from ddgs import DDGS
from pathlib import Path
from datetime import datetime, timezone
import html


PERSON_NAME = "Stephen Wolfram"
PERSON_FILE = Path("people/001-stephen-wolfram.md")

AUTO_START = "<!-- AUTO-UPDATE-START -->"
AUTO_END = "<!-- AUTO-UPDATE-END -->"


def search_interviews(name, max_results=10):
    query = f'"{name}" interview podcast'

    print(f"Searching web for: {query}")

    results = list(
        DDGS().text(
            query,
            region="us-en",
            max_results=max_results
        )
    )

    return results


def select_candidates(results, limit=5):
    candidates = []

    preferred_words = [
        "interview",
        "podcast",
        "conversation",
        "talk",
        "episode",
        "with stephen wolfram"
    ]

    reject_words = [
        "media coverage",
        "interviews of stephen wolfram",
        "archive",
        "biography"
    ]

    for result in results:
        title = result.get("title", "")
        url = result.get("href", "")
        snippet = result.get("body", "")

        combined = f"{title} {snippet}".lower()

        # Reject obvious archive/index pages
        if any(word in combined for word in reject_words):
            continue

        # Give relevant interview-like results a score
        score = sum(
            1 for word in preferred_words
            if word in combined
        )

        if score > 0 and url:
            candidates.append({
                "title": title,
                "url": url,
                "snippet": snippet,
                "score": score
            })

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return candidates[:limit]


def build_markdown(candidates):
    checked = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    lines = [
        AUTO_START,
        "",
        "### Recent Interview / Podcast Candidates",
        ""
    ]

    if not candidates:
        lines.append(
            "No suitable interview or podcast candidates were found."
        )
    else:
        for i, item in enumerate(candidates, start=1):
            title = html.escape(item["title"])
            snippet = html.escape(item["snippet"])
            url = item["url"]

            lines.extend([
                f"#### {i}. {title}",
                "",
                f"{snippet}",
                "",
                f"[Open source]({url})",
                ""
            ])

    lines.extend([
        f"_Last checked: {checked}_",
        "",
        AUTO_END
    ])

    return "\n".join(lines)


def update_markdown_file(new_section):
    text = PERSON_FILE.read_text(encoding="utf-8")

    if AUTO_START not in text or AUTO_END not in text:
        raise RuntimeError(
            "AUTO-UPDATE markers were not found "
            f"in {PERSON_FILE}"
        )

    before = text.split(AUTO_START, 1)[0]
    after = text.split(AUTO_END, 1)[1]

    PERSON_FILE.write_text(
        before + new_section + after,
        encoding="utf-8"
    )


def main():
    results = search_interviews(PERSON_NAME)

    print(f"\nFound {len(results)} raw search results.")

    for i, result in enumerate(results, start=1):
        print(f"\nRAW RESULT {i}")
        print("Title:", result.get("title"))
        print("URL:", result.get("href"))

    candidates = select_candidates(results)

    print(
        f"\nSelected {len(candidates)} "
        "interview/podcast candidates."
    )

    for i, candidate in enumerate(candidates, start=1):
        print(f"{i}. {candidate['title']}")
        print(f"   score = {candidate['score']}")
        print(f"   {candidate['url']}")

    new_section = build_markdown(candidates)

    update_markdown_file(new_section)

    print(
        f"\nSuccessfully updated {PERSON_FILE}"
    )


if __name__ == "__main__":
    main()
