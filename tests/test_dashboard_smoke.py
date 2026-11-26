"""Smoke tests verifying every Streamlit page renders and interactive flows work."""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_all_seven_pages_render_without_exceptions() -> None:
    pages = sorted((PROJECT_ROOT / "dashboard" / "pages").glob("*.py"))
    assert len(pages) == 7

    for page_path in pages:
        at = AppTest.from_file(str(page_path), default_timeout=60)
        at.run()
        assert not at.exception, f"{page_path.name} raised: {at.exception}"


def test_prediction_page_interactive_submit() -> None:
    page_path = PROJECT_ROOT / "dashboard" / "pages" / "4_Duration_Prediction.py"
    at = AppTest.from_file(str(page_path), default_timeout=60)
    at.run()
    assert not at.exception

    # Click the Predict Duration button inside the form
    at.button[0].click().run()
    assert not at.exception
    markdown_text = "\n".join(m.value for m in at.markdown)
    assert "Estimated Scheduled Leg Duration" in markdown_text


def test_train_search_page_interactive_od_search() -> None:
    page_path = PROJECT_ROOT / "dashboard" / "pages" / "2_Train_Search.py"
    at = AppTest.from_file(str(page_path), default_timeout=60)
    at.run()
    assert not at.exception

    # Click Find Direct Trains (SWV -> MAO default)
    at.button[0].click().run()
    assert not at.exception
    success_msgs = [s.value for s in at.success]
    assert any("direct train connection" in msg for msg in success_msgs)
