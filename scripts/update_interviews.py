from ddgs import DDGS
from pathlib import Path
from datetime import datetime, timezone
import html
import time


PEOPLE_DIR = Path("people")

AUTO_START = "<!-- AUTO-UPDATE-START -->"
AUTO_END = "<!-- AUTO-UPDATE-END -->"


def get_person_name(path):
    """
    Read the person's name from the first Markdown H1 heading.

    Example:
    # Stephen Wolfram
    """

    text = path.read_text(encoding="utf-8")

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("# "):
            return line[2:].strip()

    return None


def search_interviews(name, max_results=15):
    query = f'"{name}" interview podcast'

    print()
    print("=" * 60)
    print(f"Searching for: {name}")
    print(f"Query: {query}")

    results = list(
        DDGS().text(
            query,
            region="us-en",
            max_results=max_results
        )
    )

    print(f"Found {len(results)} raw results.")

    return results


def select_candidates(name, results, limit=5):
    candidates = []

    preferred_words = [
        "interview",
        "podcast",
        "conversation",
        "episode",
        "talk",
        f"with {name.lower()}"
    ]

    reject_words = [
        "media coverage",
        "interviews of",
        "archive",
        "biography",
        "wikipedia"
    ]

    name_lower = name.lower()

    for result in results:
        title = result.get("title", "")
        url = result.get("href", "")
        snippet = result.get("body", "")

        combined = f"{title} {snippet}".lower()

        # The person's name should actually appear
        if name_lower not in combined:
            continue

        # Reject obvious index/reference pages
        if any(word in combined for word in reject_words):
            continue

        score = 0

        for word in preferred_words:
            if word in combined:
                score += 1

        # Name in title is especially valuable
        if name_lower in title.lower():
            score += 2

        if score > 0 and url:
            candidates.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "score": score
                }
            )

    candidates.sort(
        key=lambda item: item["score"],
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

            lines.extend(
                [
                    f"#### {i}. {title}",
                    "",
                    snippet,
                    "",
                    f"[Open source]({url})",
                    ""
                ]
            )

    lines.extend(
        [
            f"_Last checked: {checked}_",
            "",
            AUTO_END
        ]
    )

    return "\n".join(lines)


def update_person_file(path):
    name = get_person_name(path)

    if not name:
        print(f"SKIPPING {path}: no H1 person name found.")
        return

    text = path.read_text(encoding="utf-8")

    if AUTO_START not in text or AUTO_END not in text:
        print(
            f"SKIPPING {name}: "
            "AUTO-UPDATE markers not found."
        )
        return

    try:
        results = search_interviews(name)

        candidates = select_candidates(
            name,
            results
        )

        print(
            f"Selected {len(candidates)} "
            f"candidates for {name}:"
        )

        for i, candidate in enumerate(
            candidates,
            start=1
        ):
            print(
                f"{i}. {candidate['title']} "
                f"(score {candidate['score']})"
            )

        new_section = build_markdown(candidates)

        before = text.split(
            AUTO_START,
            1
        )[0]

        after = text.split(
            AUTO_END,
            1
        )[1]

        path.write_text(
            before + new_section + after,
            encoding="utf-8"
        )

        print(f"Updated: {path}")

    except Exception as error:
        print(
            f"ERROR updating {name}: {error}"
        )


def main():

    files = sorted(
        PEOPLE_DIR.glob("*.md")
    )

    if not files:
        raise RuntimeError(
            "No Markdown files found in people/"
        )

    print(
        f"Found {len(files)} people files."
    )

    for i, path in enumerate(files, start=1):

        print()
        print(
            f"Processing {i}/{len(files)}: "
            f"{path}"
        )

        update_person_file(path)

        # Be polite to the search service.
        # Do not hammer it with requests.
        if i < len(files):
            time.sleep(2)

    print()
    print("Finished updating all people.")


if __name__ == "__main__":
    main()
