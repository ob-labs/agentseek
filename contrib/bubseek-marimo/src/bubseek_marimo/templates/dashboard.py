# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo"]
# ///

"""Bubseek Marimo dashboard — async console backed by persisted chat events."""

# marimo.App (for directory scanner)
import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    import os
    from pathlib import Path
    from urllib import error as urlerror
    from urllib import parse as urlparse
    from urllib import request as urlrequest

    import marimo as mo

    api_base = f"http://127.0.0.1:{os.environ.get('BUB_MARIMO_PORT', '2718')}"
    insights_dir = Path(__file__).resolve().parent
    get_session, set_session = mo.state(
        {
            "session_id": None,
            "status": "idle",
            "active_turn_id": None,
            "last_event_id": 0,
            "updated_at": None,
            "last_error": None,
        },
        allow_self_loops=True,
    )
    get_events, set_events = mo.state([], allow_self_loops=True)
    get_pending_submission, set_pending_submission = mo.state(
        {"nonce": 0, "content": ""},
        allow_self_loops=True,
    )
    get_last_processed_submission_nonce, set_last_processed_submission_nonce = mo.state(
        0,
        allow_self_loops=True,
    )

    def update_session(**changes):
        _snapshot = dict(get_session())
        _snapshot.update(changes)
        set_session(_snapshot)

    def append_events(items):
        _current = list(get_events())
        _seen = {item["event_id"] for item in _current if "event_id" in item}
        _additions = [item for item in items if item.get("event_id") not in _seen]
        if _additions:
            set_events(_current + _additions)

    return (
        api_base,
        append_events,
        get_events,
        get_last_processed_submission_nonce,
        get_pending_submission,
        get_session,
        insights_dir,
        json,
        mo,
        set_last_processed_submission_nonce,
        set_pending_submission,
        set_events,
        set_session,
        update_session,
        urlerror,
        urlparse,
        urlrequest,
    )


@app.cell
def _(mo):
    refresh = mo.ui.refresh(default_interval=2, label="Auto-sync while running")
    return (refresh,)


@app.cell
def _(get_session, mo):
    _session = get_session()
    chips = [
        f"**Session**  `{_session['session_id'] or 'not-started'}`",
        f"**Status**  `{_session['status']}`",
        f"**Turn**  `{_session['active_turn_id'] or '-'}`",
        f"**Last Event**  `{_session['last_event_id']}`",
    ]
    if _session.get("last_error"):
        chips.append(f"**Error**  `{_session['last_error']}`")
    status_strip = mo.md(" | ".join(chips))
    return (status_strip,)


@app.cell
def _(get_events, mo):
    _events = get_events()
    if not _events:
        transcript = mo.md(
            """
> No transcript yet.
>
> Start a session below. Each user turn is persisted immediately, and assistant output arrives through event sync.
"""
        )
    else:
        cards = []
        for _event in _events:
            role = _event.get("role", "system")
            kind = _event.get("kind", "message")
            title = {
                "user": "You",
                "assistant": "Agent",
                "system": "System",
            }.get(role, role.title())
            accent = {
                "user": "#1f2937",
                "assistant": "#0f766e",
                "system": "#7c3aed",
            }.get(role, "#334155")
            if kind == "error":
                accent = "#b45309"
            meta = f"`#{_event.get('event_id', '?')}` · `{kind}` · `{_event.get('created_at', '')}`"
            cards.append(
                mo.md(
                    f"""
<div style="border-left: 4px solid {accent}; padding: 0.9rem 1rem; border-radius: 12px; background: #ffffff; box-shadow: 0 1px 0 rgba(15, 23, 42, 0.03);">
  <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: {accent}; font-weight: 700;">{title}</div>
  <div style="margin-top: 0.2rem; color: #60707a; font-size: 0.82rem;">{meta}</div>
  <div style="margin-top: 0.6rem; color: #13262a; line-height: 1.6; white-space: pre-wrap;">{_event.get("content", "")}</div>
</div>
"""
                )
            )
        transcript = mo.vstack(cards, gap=0.7)
    return (transcript,)


@app.cell
def _(get_pending_submission, mo, set_pending_submission):
    def _capture_submission(value):
        _pending = get_pending_submission()
        set_pending_submission({
            "nonce": _pending["nonce"] + 1,
            "content": (value or "").strip(),
        })

    composer = mo.ui.text_area(
        placeholder="Ask Bub to investigate, generate an insight notebook, or run a command prefixed with ','.",
        label="Agent Input",
        rows=4,
        full_width=True,
    ).form(
        submit_button_label="Queue Turn",
        clear_on_submit=True,
        bordered=True,
        on_change=_capture_submission,
    )
    return (composer,)


@app.cell
def _(mo):
    sync_button = mo.ui.run_button(label="Sync Transcript")
    return (sync_button,)


@app.cell
def _(
    api_base,
    append_events,
    get_last_processed_submission_nonce,
    get_pending_submission,
    get_session,
    json,
    composer,
    set_last_processed_submission_nonce,
    update_session,
    urlerror,
    urlrequest,
):
    _pending = get_pending_submission()
    _content = (_pending["content"] or "").strip()
    _nonce = int(_pending["nonce"])

    if _content and _nonce != get_last_processed_submission_nonce():
        set_last_processed_submission_nonce(_nonce)
        payload = {"content": _content}
        _session = get_session()
        if _session["session_id"]:
            payload["session_id"] = _session["session_id"]

        request = urlrequest.Request(
            f"{api_base}/api/chat/submit",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        try:
            with urlrequest.urlopen(request, timeout=15) as _response:
                _result = json.loads(_response.read().decode("utf-8"))
        except urlerror.HTTPError as exc:
            _body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 409:
                update_session(status="running", last_error=None)
            else:
                update_session(status="failed", last_error=f"HTTP {exc.code}: {_body}")
        except Exception as exc:
            update_session(status="failed", last_error=f"Submit failed: {exc}")
        else:
            _snapshot = _result.get("session") or {}
            update_session(
                session_id=_snapshot.get("session_id"),
                status=_snapshot.get("status", "running"),
                active_turn_id=_result.get("turn_id"),
                last_event_id=_snapshot.get("last_event_id", 0),
                updated_at=_snapshot.get("updated_at"),
                last_error=_snapshot.get("last_error"),
            )
            _event = _result.get("event")
            if isinstance(_event, dict):
                append_events([_event])
    elif _nonce != get_last_processed_submission_nonce():
        set_last_processed_submission_nonce(_nonce)
        update_session(last_error="Submit failed: content is empty")


@app.cell
def _(
    api_base,
    append_events,
    get_session,
    json,
    refresh,
    sync_button,
    update_session,
    urlerror,
    urlparse,
    urlrequest,
):
    _session = get_session()
    _sync_trigger = sync_button.value
    _refresh_tick = refresh.value
    should_sync = bool(_session["session_id"]) and (
        bool(_sync_trigger) or (_session["status"] == "running" and bool(_refresh_tick))
    )

    if should_sync:
        params = urlparse.urlencode({
            "session_id": _session["session_id"],
            "after": _session["last_event_id"],
        })

        try:
            with urlrequest.urlopen(f"{api_base}/api/chat/events?{params}", timeout=10) as _response:
                _result = json.loads(_response.read().decode("utf-8"))
        except urlerror.HTTPError as exc:
            _body = exc.read().decode("utf-8", errors="replace")
            update_session(status="failed", last_error=f"Sync HTTP {exc.code}: {_body}")
        except Exception as exc:
            update_session(status="failed", last_error=f"Sync failed: {exc}")
        else:
            _snapshot = _result.get("session") or {}
            _events = _result.get("events") or []
            append_events(_events)
            update_session(
                session_id=_snapshot.get("session_id", _session["session_id"]),
                status=_snapshot.get("status", _session["status"]),
                active_turn_id=_snapshot.get("active_turn_id"),
                last_event_id=_snapshot.get("last_event_id", _session["last_event_id"]),
                updated_at=_snapshot.get("updated_at"),
                last_error=_snapshot.get("last_error"),
            )

    return


@app.cell
def _(composer, mo, refresh, status_strip, sync_button):
    control_panel = mo.vstack(
        [
            mo.md("## Control"),
            status_strip,
            composer,
            sync_button,
            refresh,
            mo.md(
                "Queued turns run in the background. Use **Sync Transcript** to fetch injected assistant output and status changes."
            ),
        ],
        gap=0.8,
    )
    return (control_panel,)


@app.cell
def _(insights_dir, mo):
    notebooks = sorted(
        [path for path in insights_dir.glob("*.py") if path.name not in {"dashboard.py", "index.py"}],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if notebooks:
        lines = ["## Insights", "", "- [Open index](/?file=index.py)", ""]
        lines.extend(f"- [{path.stem}](/?file={path.name})" for path in notebooks)
    else:
        lines = [
            "## Insights",
            "",
            "- [Open index](/?file=index.py)",
            "",
            "No generated notebooks yet. Ask the agent to create one.",
        ]

    side_panel = mo.vstack(
        [
            mo.md(
                """
## Runtime Model

- marimo cell submits a turn
- channel persists it into the configured tapestore database
- agent runs out-of-band
- outbound messages are injected as events
"""
            ),
            mo.md("\n".join(lines)),
        ],
        gap=0.9,
    )
    return (side_panel,)


@app.cell
def _(control_panel, mo, side_panel, transcript):
    dashboard_hero = mo.md(
        '<div style="padding: 1.2rem 1.3rem; border: 1px solid #d9e6ea; border-radius: 18px; background: '
        'linear-gradient(135deg, #f6fbfb 0%, #edf7f7 45%, #fdfefe 100%);">'
        '<div style="font-size: 0.82rem; letter-spacing: 0.08em; text-transform: uppercase; color: #49757b;">'
        "Bubseek Console"
        "</div>"
        '<div style="font-size: 2rem; font-weight: 700; color: #12343a; margin-top: 0.25rem;">'
        "Async Agent Control Room"
        "</div>"
        '<div style="margin-top: 0.55rem; color: #355a60; line-height: 1.55;">'
        "Submit turns from native marimo cells, let the agent run in the background, and sync transcript events back into the dashboard."
        "</div>"
        "</div>"
    )
    page = mo.vstack(
        [
            dashboard_hero,
            mo.hstack(
                [
                    mo.vstack([control_panel, transcript], gap=1.0),
                    side_panel,
                ],
                widths=[0.68, 0.32],
                align="start",
                gap=1.0,
            ),
        ],
        gap=1.0,
    )
    page  # noqa: B018
    return (page,)


if __name__ == "__main__":
    app.run()
