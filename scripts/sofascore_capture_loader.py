#!/usr/bin/env python3
"""Load and verify one read-only SofaScore capture directory.

This is the boundary between on-disk raw capture and source-driven ingestion logic.
Every captured payload is re-hashed before use. Required payloads must be present,
league fixtures must include a captured standings snapshot, and no capture may claim
canonical writes or LUFC ID assignment.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from sofascore_dry_run_contract import league_position_requirement


class CaptureLoaderError(RuntimeError):
    """Raised when an on-disk source capture is incomplete, altered or unsafe."""


MANDATORY_CAPTURE_PAYLOADS = (
    "event",
    "lineups",
    "incidents",
    "managers",
    "statistics",
    "average_positions",
    "shotmap",
)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaptureLoaderError(f"missing {label}: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaptureLoaderError(f"invalid {label}: {path}") from exc
    if not isinstance(parsed, dict):
        raise CaptureLoaderError(f"{label} is not a JSON object: {path}")
    return parsed


def _safe_payload_path(capture_dir: Path, filename: Any) -> Path:
    if not isinstance(filename, str) or not filename.strip():
        raise CaptureLoaderError("captured payload has no filename")
    if Path(filename).name != filename or Path(filename).is_absolute():
        raise CaptureLoaderError(f"unsafe captured payload filename: {filename!r}")
    return capture_dir / filename


def _event_object(payload: Mapping[str, Any]) -> dict[str, Any]:
    nested = payload.get("event")
    if isinstance(nested, dict):
        return nested
    return dict(payload)


def load_verified_capture(capture_dir: Path) -> dict[str, Any]:
    capture_dir = Path(capture_dir)
    manifest = _read_json_object(capture_dir / "manifest.json", "capture manifest")

    if manifest.get("provider") != "sofascore":
        raise CaptureLoaderError("capture manifest provider is not sofascore")
    event_id = manifest.get("sofascore_event_id")
    if not isinstance(event_id, int):
        raise CaptureLoaderError("capture manifest has no numeric SofaScore event ID")
    if manifest.get("database_writes") != 0:
        raise CaptureLoaderError("capture manifest reports database writes")
    if manifest.get("canonical_lufc_ids_assigned") is not False:
        raise CaptureLoaderError("capture manifest reports canonical LUFC IDs")

    entries = manifest.get("payloads")
    if not isinstance(entries, Mapping):
        raise CaptureLoaderError("capture manifest has no payload map")

    raw_payloads: dict[str, dict[str, Any]] = {}
    verified_sha256: dict[str, str] = {}
    unavailable: dict[str, Any] = {}

    for name, metadata in entries.items():
        if not isinstance(name, str) or not isinstance(metadata, Mapping):
            raise CaptureLoaderError("capture manifest contains malformed payload metadata")
        status = str(metadata.get("status") or "").strip().casefold()
        if status != "captured":
            unavailable[name] = dict(metadata)
            continue

        payload_path = _safe_payload_path(capture_dir, metadata.get("file"))
        payload = _read_json_object(payload_path, f"captured payload {name}")
        actual_sha256 = _sha256(payload)
        expected_sha256 = metadata.get("sha256")
        if not isinstance(expected_sha256, str) or actual_sha256 != expected_sha256:
            raise CaptureLoaderError(f"captured payload hash mismatch: {name}")
        raw_payloads[name] = payload
        verified_sha256[name] = actual_sha256

    missing = [name for name in MANDATORY_CAPTURE_PAYLOADS if name not in raw_payloads]
    if missing:
        raise CaptureLoaderError(f"required captured payloads are missing: {missing}")

    event = _event_object(raw_payloads["event"])
    if event.get("id") != event_id:
        raise CaptureLoaderError(
            f"event payload ID {event.get('id')!r} does not match manifest event ID {event_id}"
        )

    league_requirement = league_position_requirement(event)
    if league_requirement["status"] == "REQUIRED" and "standings" not in raw_payloads:
        raise CaptureLoaderError("league fixture is missing captured post-match standings")

    return {
        "status": "PASS",
        "provider": "sofascore",
        "sofascore_event_id": event_id,
        "capture_dir": str(capture_dir),
        "raw_payloads": raw_payloads,
        "verified_payload_sha256": verified_sha256,
        "manifest_sha256": _sha256(manifest),
        "unavailable_payloads": unavailable,
        "database_writes": 0,
        "canonical_lufc_ids_assigned": False,
        "promotion_performed": False,
    }
