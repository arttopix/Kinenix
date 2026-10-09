"""Issue #63: every flow.md example in docs/ compiles, uses real actions and parameters, and drops no lines.

People and AI assistants copy these examples, so a wrong parameter name in the docs ends up in real flows.
"""
import re
from pathlib import Path

import pytest

from kinenix.engine.markdown import markdown_issues, markdown_to_flow
from kinenix.engine.validation import validate_flow

DOCS = Path(__file__).resolve().parents[2] / "docs"
_FENCE = re.compile(r"^(?P<fence>`{3,})markdown[ \t]*\n(?P<body>.*?)^(?P=fence)[ \t]*$", re.S | re.M)
_STEP = re.compile(r"^###\s+.*\(\s*`?[a-z_]+\.[a-z_]+`?\s*\)\s*$", re.M)


def _examples():
    for doc in sorted(DOCS.glob("*.md")):
        text = doc.read_text(encoding="utf-8")
        for match in _FENCE.finditer(text):
            body = match.group("body")
            if not _STEP.search(body) or "(`[" in body:
                continue  # not a flow example, or a syntax template with placeholders such as `[action.name]`
            line = text.count("\n", 0, match.start()) + 1
            yield pytest.param(body, id=f"{doc.name}:{line}")


@pytest.mark.parametrize("body", list(_examples()))
def test_doc_example_compiles_and_validates(body):
    source = body if body.lstrip().startswith("# ") else "# Example\n\n## Steps\n\n" + body
    flow = markdown_to_flow(source)
    assert flow.steps, "the example has no steps"
    problems = markdown_issues(source) + validate_flow(flow)
    assert problems == []


def test_examples_are_found():
    assert len(list(_examples())) > 40
