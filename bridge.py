import json
import os
from datetime import UTC, datetime
from pathlib import Path

from slack_bolt.async_app import AsyncApp

SUBS_DIR = Path(
    os.environ.get("CLAUDE_SLACK_SUBS_DIR", Path.home() / ".claude-slack" / "subs")
)
FIELDS = (
    "channel",
    "channel_type",
    "user",
    "text",
    "ts",
    "thread_ts",
    "parent_user_id",
    "subtype",
    "bot_id",
)


def to_line(event: dict) -> dict:
    message = {**event, **event.get("message", {})}
    line = {field: message.get(field) for field in FIELDS}
    line["channel"] = event.get("channel")
    line["subtype"] = event.get("subtype")
    return line


def matches(line: dict, match: dict) -> bool:
    return all(line.get(key) == value for key, value in match.items())


def is_active(sub: dict, now: datetime) -> bool:
    expires_at = sub.get("expires_at")
    if expires_at and datetime.fromisoformat(expires_at) <= now:
        return False
    return Path(sub["out"]).parent.is_dir()


def deliver(event: dict, subs_dir: Path = SUBS_DIR, now: datetime | None = None):
    now = now or datetime.now(UTC)
    line = to_line(event)
    for sub_file in subs_dir.glob("*.json"):
        try:
            sub = json.loads(sub_file.read_text())
        except (OSError, ValueError):
            continue
        if not is_active(sub, now):
            sub_file.unlink(missing_ok=True)
            continue
        if matches(line, sub.get("match", {})):
            with open(sub["out"], "a") as out:
                out.write(json.dumps(line) + "\n")


def register(app: AsyncApp) -> None:
    SUBS_DIR.mkdir(parents=True, exist_ok=True)

    @app.event("message")
    async def on_message(event):
        deliver(event)


if __name__ == "__main__":
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    subs = tmp / "subs"
    subs.mkdir()
    now = datetime(2026, 1, 1, tzinfo=UTC)

    def sub(name, **body):
        (subs / f"{name}.json").write_text(json.dumps(body))
        return tmp / f"{name}.jsonl"

    every = sub("every", out=str(tmp / "every.jsonl"))
    thread = sub("thread", out=str(tmp / "thread.jsonl"), match={"thread_ts": "9"})
    sub("expired", out=str(tmp / "x.jsonl"), expires_at="2025-01-01T00:00:00Z")
    sub("orphan", out=str(tmp / "gone" / "o.jsonl"))
    (subs / "half.json").write_text("{")

    deliver({"channel": "C1", "user": "U1", "text": "a", "ts": "1"}, subs, now)
    deliver({"channel": "C1", "user": "U2", "ts": "2", "thread_ts": "9"}, subs, now)
    deliver(
        {"channel": "C1", "subtype": "message_changed", "message": {"text": "b"}},
        subs,
        now,
    )

    lines = [json.loads(x) for x in every.read_text().splitlines()]
    assert [x["ts"] for x in lines[:2]] == ["1", "2"]
    assert lines[2]["text"] == "b" and lines[2]["subtype"] == "message_changed"
    assert [json.loads(x)["ts"] for x in thread.read_text().splitlines()] == ["2"]
    assert not (subs / "expired.json").exists()
    assert not (subs / "orphan.json").exists()
    assert (subs / "half.json").exists()
    print("ok")
