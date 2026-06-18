#!/usr/bin/env python3
"""quiz.py — draw FastAPI-for-AI interview questions from the bundled references.

Parses references/ch*.md (questions are `### Q<n>. ...` headings, the answer is
the prose until the next heading) and exposes them non-interactively so an agent
running a mock interview can pull questions and reveal answers on demand.

Stdlib only. Run with `python3 quiz.py ...` (or `uv run quiz.py ...`).

Exit codes:
  0  success
  1  invalid arguments
  2  references not found / unparseable
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REFS_DIR = Path(__file__).resolve().parent.parent / "references"
_Q_RE = re.compile(r"^### Q(\d+)\.\s*(.+?)\s*$")
_HEADING_RE = re.compile(r"^#{1,3}\s")


@dataclass
class Question:
    id: str
    chapter: str
    topic: str
    question: str
    answer: str


def load_questions() -> list[Question]:
    if not REFS_DIR.is_dir():
        print(f"error: references dir not found: {REFS_DIR}", file=sys.stderr)
        raise SystemExit(2)

    questions: list[Question] = []
    for path in sorted(REFS_DIR.glob("ch*.md")):
        chapter = path.stem.split("-")[0]  # e.g. "ch09"
        topic = path.stem
        lines = path.read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            m = _Q_RE.match(lines[i])
            if not m:
                i += 1
                continue
            number, qtext = m.group(1), m.group(2)
            body: list[str] = []
            i += 1
            while i < len(lines) and not _HEADING_RE.match(lines[i]):
                body.append(lines[i])
                i += 1
            answer = "\n".join(body).strip()
            questions.append(
                Question(
                    id=f"{chapter}-q{number}",
                    chapter=chapter,
                    topic=topic,
                    question=qtext,
                    answer=answer,
                )
            )
    if not questions:
        print(f"error: no questions parsed from {REFS_DIR}", file=sys.stderr)
        raise SystemExit(2)
    return questions


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="quiz.py",
        description="Draw FastAPI-for-AI interview questions from the references.",
        epilog=(
            "Examples:\n"
            "  python3 quiz.py --list\n"
            "  python3 quiz.py --random 5\n"
            "  python3 quiz.py --topic ch09 --random 3 --with-answers\n"
            "  python3 quiz.py --answer ch09-q4\n"
            "  python3 quiz.py --random 3 --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--list", action="store_true", help="List every question id + text.")
    p.add_argument("--topics", action="store_true", help="List available chapters + counts.")
    p.add_argument("--count", action="store_true", help="Print the total question count.")
    p.add_argument("--random", type=int, metavar="N", help="Draw N random questions.")
    p.add_argument("--topic", metavar="chNN", help="Restrict to one chapter, e.g. ch09.")
    p.add_argument("--answer", metavar="ID", help="Print one question + answer by id.")
    p.add_argument("--with-answers", action="store_true", help="Include answers with --random/--list.")
    p.add_argument("--seed", type=int, help="Seed the RNG for reproducible draws.")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return p


def _emit(items: list[Question], *, with_answers: bool, as_json: bool) -> None:
    if as_json:
        payload = [
            {k: v for k, v in asdict(q).items() if with_answers or k != "answer"}
            for q in items
        ]
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return
    for q in items:
        print(f"[{q.id}] {q.question}")
        if with_answers:
            print()
            print(q.answer)
            print()


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    questions = load_questions()

    if args.topic:
        questions = [q for q in questions if q.chapter == args.topic]
        if not questions:
            print(f"error: no questions for topic '{args.topic}'", file=sys.stderr)
            return 1

    if args.count:
        print(len(questions))
        return 0

    if args.topics:
        chapters: dict[str, int] = {}
        for q in load_questions():
            chapters[q.chapter] = chapters.get(q.chapter, 0) + 1
        if args.json:
            json.dump(chapters, sys.stdout, indent=2)
            sys.stdout.write("\n")
        else:
            for chapter in sorted(chapters):
                print(f"{chapter}\t{chapters[chapter]} questions")
        return 0

    if args.answer:
        match = [q for q in load_questions() if q.id == args.answer]
        if not match:
            print(f"error: no question with id '{args.answer}'", file=sys.stderr)
            return 1
        _emit(match, with_answers=True, as_json=args.json)
        return 0

    if args.list:
        _emit(questions, with_answers=args.with_answers, as_json=args.json)
        return 0

    # Default action is a random draw (5 if --random not given).
    n = args.random if args.random is not None else 5
    if n <= 0:
        print("error: --random N must be positive", file=sys.stderr)
        return 1
    if args.seed is not None:
        random.seed(args.seed)
    picks = random.sample(questions, min(n, len(questions)))
    _emit(picks, with_answers=args.with_answers, as_json=args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
