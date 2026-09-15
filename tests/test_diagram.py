"""Behavior tests for the standalone sequence-diagram renderer."""
import re

from llmsquire.diagram import render, write_diagram
from llmsquire.llm_client import InteractionRecord


def _record(**overrides):
    values = {
        "request": {
            "model": "test-model",
            "temperature": 0.0,
            "messages": [{"role": "user", "content": "Read <important> file"}],
        },
        "response": {
            "content": "I will read it.",
            "tool_calls": [{"id": "call-1", "name": "read_file", "arguments": '{"path":"notes.txt"}'}],
        },
        "timestamp": 1000.0,
        "latency_ms": 125.5,
        "input_tokens": 12,
        "output_tokens": 8,
        "model": "test-model",
        "tool_executions": [{
            "name": "read_file",
            "arguments": {"path": "notes.txt"},
            "result": "classified <contents>",
            "execution_ms": 3.25,
        }],
    }
    values.update(overrides)
    return InteractionRecord(**values)


def test_render_empty_trace_is_complete_dark_html_document():
    html = render([])

    assert "<!doctype html>" in html.lower()
    assert "Learner / Koan / Harness" in html
    assert "LLM" in html
    assert "Tools" in html
    assert "No LLM interactions were recorded" in html
    assert "<style>" in html
    assert "<script>" in html
    assert "https://" not in html


def test_render_shows_payloads_context_timing_tokens_and_tool_round_trip():
    html = render([_record()])

    assert "API call" in html
    assert "API response" in html
    assert "read_file" in html
    assert "Harness executes" in html
    assert "Tool result" in html
    assert "Context window · 1 message" in html
    assert "125.5 ms" in html
    assert "12 in" in html
    assert "8 out" in html
    assert "20 cumulative" in html
    assert "&quot;test-model&quot;" in html
    assert "&lt;important&gt;" in html
    assert "&lt;contents&gt;" in html
    # Every arrow has a direction-specific lane, so it can span the
    # corresponding pair of lifelines rather than being centered by a grid.
    assert not re.search(r"\.arrow-row\s*\{[^}]*display:grid", html)
    for lane in (
        "arrow-learner-llm",
        "arrow-llm-learner",
        "arrow-harness-tools",
        "arrow-tools-harness",
    ):
        assert lane in html


def test_render_accumulates_tokens_and_reports_elapsed_time_between_round_trips():
    first = _record(timestamp=1000.0, input_tokens=5, output_tokens=7)
    second = _record(
        timestamp=1001.234,
        input_tokens=11,
        output_tokens=13,
        request={"messages": [{"role": "tool", "content": "done"}]},
        response={"content": "finished", "tool_calls": []},
        tool_executions=[],
    )

    html = render([first, second])

    assert "234.0 ms since previous step" in html
    assert "36 cumulative" in html
    assert "Context window · 1 message" in html


def test_write_diagram_creates_timestamped_self_contained_html(tmp_path):
    path = write_diagram([_record()], "about tool calling", "test full loop", tmp_path)

    assert path.parent == tmp_path
    assert re.fullmatch(
        r"about_tool_calling_test_full_loop_\d{8}_\d{6}\.html", path.name
    )
    assert "LLM conversation sequence" in path.read_text(encoding="utf-8")
