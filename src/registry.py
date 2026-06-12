"""The Code of Laws — JSON file backend (source of truth) with a best-effort
AgentCore Memory mirror.

laws.json always works and always wins on conflict. The mirror ingests every
codified decree into AgentCore Memory and serves precedent reads when active;
any failure logs a warning and falls back to JSON — it never blocks the demo.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("agora")

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "laws.json"
REGION = "us-west-2"
MEMORY_NAME = "agora_code_of_laws"
ACTOR_ID = "agora-parliament"
SESSION_ID = "code-of-laws"


class MemoryMirror:
    """AgentCore Memory wrapper. Every public method is failure-proof."""

    def __init__(self) -> None:
        self.memory_id: str | None = None
        self.state = "disconnected"
        self._control = None
        self._data = None
        self.connect()

    def connect(self) -> None:
        try:
            import boto3

            self._control = boto3.client("bedrock-agentcore-control", region_name=REGION)
            self._data = boto3.client("bedrock-agentcore", region_name=REGION)
            memories = self._control.list_memories(maxResults=100)["memories"]
            mine = [m for m in memories if m.get("id", "").startswith(MEMORY_NAME)]
            if mine:
                status = mine[0].get("status")
                self.memory_id = mine[0]["id"]
                self.state = "active" if status == "ACTIVE" else f"provisioning ({status})"
            else:
                created = self._control.create_memory(
                    name=MEMORY_NAME,
                    description="AGORA Code of Laws — codified decrees, cross-session precedent",
                    eventExpiryDuration=7,  # days; the sandbox account dies tonight
                )
                self.memory_id = created["memory"]["id"]
                self.state = "provisioning (CREATING)"
        except Exception as exc:  # noqa: BLE001 — memory must never block
            self.state = "unavailable"
            log.warning("AgentCore Memory unavailable, JSON only: %s", exc)

    def _refresh_if_provisioning(self) -> None:
        if self.state.startswith("provisioning") and self.memory_id:
            try:
                status = self._control.get_memory(memoryId=self.memory_id)["memory"]["status"]
                self.state = "active" if status == "ACTIVE" else f"provisioning ({status})"
            except Exception:  # noqa: BLE001
                pass

    def ingest(self, record: dict) -> bool:
        self._refresh_if_provisioning()
        if self.state != "active":
            return False
        slim = {k: record.get(k) for k in ("id", "petition", "bill", "verdict", "opinion", "timestamp")}
        try:
            self._data.create_event(
                memoryId=self.memory_id,
                actorId=ACTOR_ID,
                sessionId=SESSION_ID,
                eventTimestamp=datetime.now(timezone.utc),
                payload=[{"blob": json.dumps(slim, ensure_ascii=False)}],
            )
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("AgentCore Memory ingest failed for %s: %s", record.get("id"), exc)
            return False

    def recall(self, n: int = 3) -> list[dict] | None:
        """Most recent codified laws from Memory, or None if unavailable."""
        self._refresh_if_provisioning()
        if self.state != "active":
            return None
        try:
            events = self._data.list_events(
                memoryId=self.memory_id, actorId=ACTOR_ID, sessionId=SESSION_ID,
                includePayloads=True, maxResults=20,
            )["events"]
            laws = []
            for ev in events:
                for item in ev.get("payload", []):
                    blob = item.get("blob")
                    if blob:
                        laws.append(json.loads(blob))
            laws.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
            return laws[:n]
        except Exception as exc:  # noqa: BLE001
            log.warning("AgentCore Memory recall failed: %s", exc)
            return None


class Registry:
    def __init__(self, path: str | os.PathLike | None = None, mirror: bool = True):
        self.path = Path(path) if path else DEFAULT_PATH
        self._laws: list[dict] = []
        if self.path.exists():
            try:
                self._laws = json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                self._laws = []
        self._memory = MemoryMirror() if mirror else None
        self._mirrored = 0

    @property
    def laws(self) -> list[dict]:
        return list(self._laws)

    def next_id(self) -> str:
        return f"AGORA-2026-{len(self._laws) + 1:03d}"

    def recent(self, n: int = 3) -> list[dict]:
        """Most recent laws first — injected as precedent into deliberation.

        Served from AgentCore Memory when active; laws.json otherwise.
        """
        if self._memory:
            recalled = self._memory.recall(n)
            # Trust the mirror only when it covers everything JSON would serve
            # (it lags while provisioning or after a failed ingest).
            if recalled is not None and len(recalled) >= min(n, len(self._laws)):
                return recalled[:n]
        return self._laws[-n:][::-1]

    def codify(self, **fields) -> dict:
        record = {
            "id": self.next_id(),
            **fields,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self._laws.append(record)
        self._save()
        self._mirror(record)
        return record

    def _save(self) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._laws, indent=2, ensure_ascii=False))
        os.replace(tmp, self.path)

    # --- AgentCore Memory mirror (best-effort, never blocks) ---------------

    def _mirror(self, record: dict) -> None:
        if self._memory and self._memory.ingest(record):
            self._mirrored += 1

    def memory_status(self) -> str:
        if self._memory and self._memory.state == "active":
            return f"laws.json + AgentCore Memory ✓ ({self._memory.memory_id})"
        state = self._memory.state if self._memory else "off"
        return f"laws.json (AgentCore Memory: {state})"
