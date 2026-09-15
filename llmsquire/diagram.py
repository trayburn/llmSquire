"""Self-contained HTML sequence diagrams for recorded LLM interactions.

The diagram shows a clean visual overview with three vertical lifelines
(Learner/Koan, LLM, Tools). Arrows between lifelines represent API calls,
responses, tool calls, and tool results. Clicking any arrow opens a detail
panel showing the exact payload, context window, timing, and token counts.

All CSS and JS is inline — no external dependencies. Opens in any browser.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
import json
from pathlib import Path
import re
from typing import Any, Iterable, Sequence

from llmsquire.llm_client import InteractionRecord


def _json(value: Any) -> str:
    """Serialize an API payload faithfully while tolerating unusual values."""
    return json.dumps(value, indent=2, ensure_ascii=False, default=str, sort_keys=True)


def _infer_tool_executions(record: InteractionRecord, next_record: InteractionRecord | None) -> list[dict]:
    """Reconstruct tool executions from consecutive trace entries.

    When a student uses llm.ask() manually (not converse()), the trace
    records the tool_calls in the response but does NOT populate
    tool_executions — the student executed the tools themselves and
    sent the results back in the next ask() call.

    We infer what happened by matching tool_call IDs from the response
    against 'tool' role messages in the next request's messages array.
    """
    if record.tool_executions:
        return record.tool_executions

    tool_calls = record.response.get("tool_calls", [])
    if not tool_calls:
        return []

    if next_record is None:
        # No next record — the tool was called but we never saw the result
        # sent back. Still show the tool call arrows, just without result content.
        return [
            {"name": tc.get("name", "unknown"), "arguments": tc.get("arguments", ""),
             "result": "(result sent in next API call)", "execution_ms": 0.0,
             "tool_call_id": tc.get("id", "")}
            for tc in tool_calls
        ]

    # Build a map of tool_call_id → tool result from the next request's messages
    next_messages = next_record.request.get("messages", [])
    if not isinstance(next_messages, list):
        next_messages = []
    tool_results: dict[str, str] = {}
    for msg in next_messages:
        if isinstance(msg, dict) and msg.get("role") == "tool":
            tc_id = msg.get("tool_call_id", "")
            tool_results[tc_id] = msg.get("content", "")

    executions = []
    for tc in tool_calls:
        tc_id = tc.get("id", "")
        name = tc.get("name", "unknown")
        args = tc.get("arguments", "")
        # Try to parse arguments as JSON for cleaner display
        if isinstance(args, str):
            try:
                import json as _json
                args = _json.loads(args)
            except (ValueError, TypeError):
                pass
        result = tool_results.get(tc_id, "(result not found in next request)")
        executions.append({
            "name": name,
            "arguments": args,
            "result": result,
            "execution_ms": 0.0,
            "tool_call_id": tc_id,
        })
    return executions


def _extract_skill(messages: list) -> str | None:
    """Extract the system prompt (skill) from messages, if present."""
    if not isinstance(messages, list):
        return None
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "system":
            content = msg.get("content", "")
            if content:
                # Truncate for the badge display
                snippet = content.strip().split("\n")[0][:60]
                return snippet
    return None


def render(trace: Sequence[InteractionRecord]) -> str:
    """Return a complete, offline HTML sequence diagram for *trace*.

    The diagram has two parts:
    1. A visual overview with three vertical lifelines and arrows between them
    2. An interactive detail panel that opens when you click any arrow

    Tool calls are captured from two sources:
    - record.tool_executions (populated by converse())
    - inferred from consecutive ask() calls (manual tool loops)
    """
    if not trace:
        return _skeleton('<p class="empty">No LLM interactions were recorded for this exercise.</p>', "", "")

    # Build the arrow entries and detail panels
    arrows_html: list[str] = []
    details_html: list[str] = []
    cumulative_tokens = 0
    previous_timestamp: float | None = None
    detail_id = 0

    trace_list = list(trace)
    for index, record in enumerate(trace_list, start=1):
        elapsed = "first step"
        if previous_timestamp is not None:
            elapsed_ms = (record.timestamp - previous_timestamp) * 1000
            elapsed = f"{elapsed_ms:.1f} ms since previous step"
        previous_timestamp = record.timestamp
        cumulative_tokens += record.input_tokens + record.output_tokens

        messages = record.request.get("messages", [])
        message_count = len(messages) if isinstance(messages, list) else 0

        # Detect skill (system prompt) in this request
        skill_snippet = _extract_skill(messages)

        # --- API call arrow (Learner → LLM) ---
        detail_id += 1
        call_id = f"detail-{detail_id}"
        skill_badge = ""
        if skill_snippet:
            skill_badge = f' <span class="skill-badge" title="{escape(skill_snippet)}">🛡 Skill</span>'
        arrows_html.append(
            f'<div class="arrow-row arrow-learner-llm" data-detail="{call_id}">'
            f'<div class="arrow-label">API call · round {index}{skill_badge}</div>'
            f'<div class="arrow-line arrow-right" data-detail="{call_id}"></div>'
            f'<div class="arrow-meta">{elapsed}</div>'
            f'</div>'
        )
        # Build sections for the detail panel, adding skill info if present
        call_sections: list[tuple[str, Any]] = [("Exact request payload", record.request)]
        if skill_snippet:
            call_sections.append(("Skill / System prompt", skill_snippet))
        call_sections.append(
            (f"Context window · {message_count} message{'s' if message_count != 1 else ''}", messages),
        )
        details_html.append(_detail_panel(
            call_id,
            f"API call · round {index}",
            f"Learner / Koan → LLM · {elapsed}",
            call_sections,
        ))

        # --- API response arrow (LLM → Learner) ---
        # The response comes FIRST — it contains the tool_call REQUEST.
        # The harness can only execute the tool AFTER seeing this response.
        detail_id += 1
        resp_id = f"detail-{detail_id}"
        latency = record.latency_ms
        token_info = f"{record.input_tokens} in · {record.output_tokens} out · {cumulative_tokens} cumulative"
        arrows_html.append(
            f'<div class="arrow-row arrow-llm-learner" data-detail="{resp_id}">'
            f'<div class="arrow-label">API response · round {index}</div>'
            f'<div class="arrow-line arrow-left arrow-green" data-detail="{resp_id}"></div>'
            f'<div class="arrow-meta">{latency:.1f} ms · {token_info}</div>'
            f'</div>'
        )
        details_html.append(_detail_panel(
            resp_id,
            f"API response · round {index}",
            f"LLM → Learner / Koan · {latency:.1f} ms latency · {token_info}",
            [("Exact response payload", record.response)],
        ))

        # --- Tool executions (after response, before next API call) ---
        # The LLM requested tool calls in its response. The HARNESS executes
        # them and sends results back in the next API call.
        next_record = trace_list[index] if index < len(trace_list) else None
        executions = _infer_tool_executions(record, next_record)

        for execution in executions:
            name = str(execution.get("name", "unknown tool"))
            args = execution.get("arguments", {})
            result = execution.get("result", "")
            duration = float(execution.get("execution_ms", 0) or 0)
            tc_id = execution.get("tool_call_id", "")

            duration_label = f"{duration:.1f} ms execution" if duration > 0 else "executed by harness"

            # Tool execution arrow (Harness → Tools) — full width, bypassing LLM.
            # The LLM REQUESTS the tool call, but the HARNESS executes it.
            # The arrow spans from Learner/Harness to Tools, not from LLM to Tools.
            detail_id += 1
            tc_dom_id = f"detail-{detail_id}"
            arrows_html.append(
                f'<div class="arrow-row arrow-harness-tools" data-detail="{tc_dom_id}">'
                f'<div class="arrow-label">Harness executes · {escape(name)}</div>'
                f'<div class="arrow-line arrow-right arrow-purple" data-detail="{tc_dom_id}"></div>'
                f'<div class="arrow-meta">{duration_label}</div>'
                f'</div>'
            )
            details_html.append(_detail_panel(
                tc_dom_id,
                f"Harness executes tool · {name}",
                f"Koan / Harness → Tools · {duration_label}",
                [("Arguments", args)],
            ))

            # Tool result arrow (Tools → Harness) — full width, bypassing LLM.
            detail_id += 1
            tr_dom_id = f"detail-{detail_id}"
            arrows_html.append(
                f'<div class="arrow-row arrow-tools-harness" data-detail="{tr_dom_id}">'
                f'<div class="arrow-label">Tool result · {escape(name)}</div>'
                f'<div class="arrow-line arrow-left arrow-green" data-detail="{tr_dom_id}"></div>'
                f'<div class="arrow-meta">{duration_label}</div>'
                f'</div>'
            )
            details_html.append(_detail_panel(
                tr_dom_id,
                f"Tool result · {name}",
                f"Tools → Koan / Harness · {duration_label}",
                [("Return value", result)],
            ))

    arrows = "\n".join(arrows_html)
    details = "\n".join(details_html)
    return _skeleton("", arrows, details)


def _detail_panel(detail_id: str, title: str, annotation: str, sections: list[tuple[str, Any]]) -> str:
    """Build a hidden detail panel that shows when its arrow is clicked."""
    payload_parts = []
    for i, (section_title, value) in enumerate(sections):
        is_context = "context" in section_title.lower()
        detail_tag = "details" if is_context else "div"
        summary_tag = f"<summary>{escape(section_title)}</summary>" if is_context else f"<h4>{escape(section_title)}</h4>"
        payload_parts.append(
            f'<{detail_tag} class="payload-section{" context" if is_context else ""}">'
            f'{summary_tag}'
            f'<pre class="json">{escape(_json(value))}</pre>'
            f'</{detail_tag}>'
        )
    payloads = "".join(payload_parts)
    return (
        f'<div class="detail-panel" id="{detail_id}" style="display:none;">'
        f'<div class="detail-header">'
        f'<h3>{escape(title)}</h3>'
        f'<p class="annotation">{escape(annotation)}</p>'
        f'<button class="close-btn" onclick="closeDetail()">✕</button>'
        f'</div>'
        f'{payloads}'
        f'</div>'
    )


def _skeleton(empty_html: str, arrows_html: str, details_html: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>llmSquire conversation trace</title>
<style>
:root {{ color-scheme: dark; --bg:#10141d; --panel:#19202d; --border:#344155; --text:#e8edf7; --muted:#9aa9c1; --blue:#68b5ff; --purple:#b792ff; --green:#63d9a5; --orange:#ffc36b; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:14px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
main {{ max-width:960px; margin:auto; padding:28px 18px 56px; }}
h1 {{ margin:0 0 6px; font-size:24px; }}
.subtitle {{ color:var(--muted); margin:0 0 24px; }}

/* Lifelines — three vertical lines that span the full diagram height */
.diagram {{ position:relative; margin:20px 0 32px; }}
.lifeline-headers {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:0; margin-bottom:0; }}
.lifeline-header {{
  text-align:center; border:1px solid var(--border); background:var(--panel);
  border-radius:8px 8px 0 0; padding:10px 8px; font-weight:bold; font-size:13px;
}}
.lifeline-header.left {{ border-right:none; border-radius:8px 0 0 0; }}
.lifeline-header.center {{ border-left:none; border-right:none; }}
.lifeline-header.right {{ border-left:none; border-radius:0 8px 0 0; }}

/* The three vertical dashed lines */
.lifelines-container {{ position:relative; padding-top:8px; }}
.lifeline-line {{
  position:absolute; top:0; bottom:0; width:0; border-left:2px dashed var(--border);
}}
.lifeline-line.left {{ left:16.67%; }}
.lifeline-line.center {{ left:50%; }}
.lifeline-line.right {{ left:83.33%; }}

/* Arrow rows use one flex-column layout. Their children are positioned in
   explicit 33.33% lanes, matching the lifelines at 16.67%, 50%, and 83.33%. */
.arrow-row {{
  position:relative; display:flex; flex-direction:column; align-items:flex-start;
  min-height:52px; padding:8px 0; cursor:pointer;
}}
.arrow-row:hover {{ background:rgba(104,181,255,0.06); }}

/* The arrow line itself. The lane classes below place it between endpoints. */
.arrow-line {{
  position:relative; height:3px; border-radius:2px; margin:0;
  transition:opacity 0.15s;
}}
.arrow-row:hover .arrow-line {{ opacity:0.7; }}

/* Right-pointing arrows (Learner→LLM, Harness→Tools) */
.arrow-right {{
  background:var(--blue);
}}
.arrow-right::after {{
  content:""; position:absolute; right:-8px; top:-6px;
  border-left:10px solid var(--blue); border-top:7px solid transparent; border-bottom:7px solid transparent;
}}

/* Left-pointing arrows (LLM→Learner, Tools→Harness) */
.arrow-left {{
  background:var(--green);
}}
.arrow-left::before {{
  content:""; position:absolute; left:-8px; top:-6px;
  border-right:10px solid var(--green); border-top:7px solid transparent; border-bottom:7px solid transparent;
}}

/* Purple arrows for tool calls */
.arrow-purple {{ background:var(--purple); }}
.arrow-purple::after {{ border-left-color:var(--purple) !important; }}
.arrow-purple::before {{ border-right-color:var(--purple) !important; }}

/* Green arrows for responses and tool results */
.arrow-green {{ background:var(--green); }}
.arrow-green::after {{ border-left-color:var(--green) !important; }}
.arrow-green::before {{ border-right-color:var(--green) !important; }}

/* Each lane includes its label, line, and metadata, all centered on the
   same pair of lifelines. */
.arrow-learner-llm > .arrow-label,
.arrow-learner-llm > .arrow-line,
.arrow-learner-llm > .arrow-meta,
.arrow-llm-learner > .arrow-label,
.arrow-llm-learner > .arrow-line,
.arrow-llm-learner > .arrow-meta {{ left:16.67%; width:33.33%; }}

/* Tool arrows span the FULL width — from Harness (left) to Tools (right).
   They pass through the LLM lane but do not touch it. This visually
   teaches that the harness mediates between LLM and Tools. */
.arrow-harness-tools > .arrow-label,
.arrow-harness-tools > .arrow-line,
.arrow-harness-tools > .arrow-meta,
.arrow-tools-harness > .arrow-label,
.arrow-tools-harness > .arrow-line,
.arrow-tools-harness > .arrow-meta {{ left:16.67%; width:66.67%; }}

/* Labels above arrows */
.arrow-label {{
  text-align:center; font-size:12px; font-weight:bold; color:var(--text);
  position:relative; z-index:2; background:var(--bg);
  margin:0; padding:2px 10px 4px; border-radius:4px;
}}
.arrow-row .arrow-label {{
  background:var(--bg); padding:2px 12px 4px; border-radius:4px; margin-bottom:0;
}}
.arrow-meta {{
  position:relative; font-size:11px; color:var(--muted); margin-top:2px; text-align:center;
}}

/* Detail panel — slides in from the right */
.detail-panel {{
  border:1px solid var(--border); border-left:4px solid var(--blue);
  border-radius:8px; background:var(--panel); padding:16px; margin:12px 0;
  animation:fadeIn 0.15s ease;
}}
@keyframes fadeIn {{ from {{ opacity:0; transform:translateY(-4px); }} to {{ opacity:1; transform:translateY(0); }} }}
.detail-header {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; position:relative; }}
.detail-header h3 {{ margin:0 0 4px; font-size:16px; }}
.detail-header .annotation {{ color:var(--muted); margin:0; font-size:12px; }}
.close-btn {{
  background:none; border:1px solid var(--border); color:var(--muted);
  border-radius:4px; padding:2px 8px; cursor:pointer; font-size:14px; position:absolute; top:0; right:0;
}}
.close-btn:hover {{ color:var(--text); border-color:var(--text); }}
.payload-section {{ margin-top:12px; }}
.payload-section h4 {{ color:var(--orange); font-size:12px; margin:0 0 6px; }}
.payload-section summary {{ cursor:pointer; color:var(--orange); font-size:12px; }}
.payload-section summary:hover {{ color:var(--text); }}
pre.json {{
  margin:6px 0 0; white-space:pre-wrap; overflow-wrap:anywhere;
  background:#0c1018; border:1px solid #263246; border-radius:5px; padding:10px;
  color:#d9e7ff; font-size:12px; max-height:500px; overflow-y:auto;
}}
.empty {{ border:1px dashed var(--border); border-radius:7px; padding:18px; color:var(--muted); text-align:center; }}
.hint {{ color:var(--muted); font-size:12px; text-align:center; margin:8px 0 0; }}
.skill-badge {{ display:inline-block; background:rgba(255,195,107,0.15); color:var(--orange); border:1px solid rgba(255,195,107,0.3); border-radius:4px; padding:1px 6px; font-size:10px; font-weight:normal; margin-left:6px; cursor:help; }}

@media (max-width:650px) {{
  .lifeline-header {{ font-size:10px; padding:6px 4px; }}
  .arrow-label {{ font-size:11px; }}
}}
</style>
</head>
<body><main>
<h1>LLM conversation sequence</h1>
<p class="subtitle">Exact API payloads, context growth, timing, and token use. Click any arrow for details.</p>
{empty_html}
<div class="diagram">
  <div class="lifeline-headers">
    <div class="lifeline-header left">Learner / Koan / Harness</div>
    <div class="lifeline-header center">LLM</div>
    <div class="lifeline-header right">Tools</div>
  </div>
  <div class="lifelines-container">
    <div class="lifeline-line left"></div>
    <div class="lifeline-line center"></div>
    <div class="lifeline-line right"></div>
    {arrows_html}
  </div>
</div>
<p class="hint">Click any arrow above to see the exact payload, context window, and token counts.</p>
<div class="details-container">
{details_html}
</div>
</main>
<script>
(function() {{
  // Click an arrow row to show its detail panel
  var rows = document.querySelectorAll('.arrow-row');
  var panels = document.querySelectorAll('.detail-panel');
  var detailsContainer = document.querySelector('.details-container');

  rows.forEach(function(row) {{
    row.addEventListener('click', function() {{
      var detailId = row.getAttribute('data-detail');
      // Hide all panels
      panels.forEach(function(p) {{ p.style.display = 'none'; }});
      // Show the clicked one
      var panel = document.getElementById(detailId);
      if (panel) {{
        panel.style.display = 'block';
        panel.scrollIntoView({{ behavior:'smooth', block:'nearest' }});
      }}
    }});
  }});

  // Close button
  window.closeDetail = function() {{
    panels.forEach(function(p) {{ p.style.display = 'none'; }});
  }};

  // Keyboard: Escape closes any open panel
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') closeDetail();
  }});
}})();
</script>
</body></html>"""


def write_diagram(
    trace: Sequence[InteractionRecord],
    koan_name: str,
    test_name: str,
    output_dir: str | Path = "diagrams",
) -> Path:
    """Write a timestamped diagram file and return its path."""
    def filename_part(value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
        return normalized or "unnamed"

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = directory / f"{filename_part(koan_name)}_{filename_part(test_name)}_{timestamp}.html"
    path.write_text(render(trace), encoding="utf-8")
    return path


# Friendly aliases
generate_html = render
render_sequence_diagram = render