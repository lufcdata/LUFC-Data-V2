#!/usr/bin/env python3
"""Build a fully evidence-driven zero-write ingestion package from a verified capture.

This runner joins the on-disk capture verifier to the fully evidence-driven ingestion
orchestrator. It never performs database access or canonical promotion. Identity mapping,
canonical diff, secondary evidence and optional backup/rollback attestations are explicit
JSON inputs; source payloads always come from the verified capture directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from sofascore_canonical_match_enrichment import (
    build_canonical_match_enrichment,
    merge_match_enrichment_into_canonical_diff,
)
from sofascore_capture_loader import load_verified_capture
from sofascore_evidence_validations import build_evidence_validations
from sofascore_source_derived_dry_run import build_source_derived_dry_run
from sofascore_source_driven_ingestion_package import (
    build_fully_evidence_driven_ingestion_package,
)


class CaptureToPackageError(RuntimeError):
    """Raised when an input file or package output is malformed or unsafe."""


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaptureToPackageError(f"missing {label}: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaptureToPackageError(f"invalid {label}: {path}") from exc
    if not isinstance(parsed, dict):
        raise CaptureToPackageError(f"{label} must be a JSON object")
    return parsed


def _optional_json_object(path: Path | None, label: str) -> dict[str, Any] | None:
    return None if path is None else _read_json_object(path, label)


def _require_zero_write(result: Mapping[str, Any]) -> None:
    if result.get("database_writes") != 0:
        raise CaptureToPackageError("ingestion result reports database writes")
    if result.get("canonical_promotion_performed") is not False:
        raise CaptureToPackageError("ingestion result reports canonical promotion")
    package = result.get("package")
    if not isinstance(package, Mapping):
        raise CaptureToPackageError("ingestion result has no package")
    if package.get("database_writes") != 0:
        raise CaptureToPackageError("ingestion package reports database writes")
    if package.get("canonical_promotion_performed") is not False:
        raise CaptureToPackageError("ingestion package reports canonical promotion")


def build_package_from_capture(
    *,
    capture_dir: Path,
    run_id: str,
    importer_git_sha: str,
    leeds_team_provider_id: int,
    identity_package: Mapping[str, Any],
    identity_mapping_validation: Mapping[str, Any],
    canonical_diff: Mapping[str, Any],
    canonical_context: Mapping[str, Any] | None = None,
    secondary_evidence: Mapping[str, Any] | None = None,
    backup: Mapping[str, Any] | None = None,
    rollback_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify raw capture, enrich safe match fields, then build the zero-write package."""
    capture = load_verified_capture(Path(capture_dir))
    raw_payloads = capture.get("raw_payloads")
    if not isinstance(raw_payloads, Mapping):
        raise CaptureToPackageError("verified capture has no raw payload map")

    effective_diff: Mapping[str, Any] = canonical_diff
    match_enrichment: Mapping[str, Any] | None = None
    if canonical_context is not None:
        source_bundle = build_source_derived_dry_run(
            raw_payloads=raw_payloads,
            leeds_team_provider_id=leeds_team_provider_id,
        )
        evidence_bundle = build_evidence_validations(
            raw_payloads=raw_payloads,
            leeds_team_provider_id=leeds_team_provider_id,
            secondary_evidence=secondary_evidence,
        )
        match_enrichment = build_canonical_match_enrichment(
            source_bundle=source_bundle,
            evidence_bundle=evidence_bundle,
            canonical_context=canonical_context,
        )
        effective_diff = merge_match_enrichment_into_canonical_diff(
            canonical_diff=canonical_diff,
            enrichment=match_enrichment,
        )

    result = build_fully_evidence_driven_ingestion_package(
        run_id=run_id,
        importer_git_sha=importer_git_sha,
        raw_payloads=raw_payloads,
        leeds_team_provider_id=leeds_team_provider_id,
        identity_package=identity_package,
        canonical_diff=effective_diff,
        identity_mapping_validation=identity_mapping_validation,
        secondary_evidence=secondary_evidence,
        backup=backup,
        rollback_manifest=rollback_manifest,
    )
    _require_zero_write(result)

    return {
        "status": result["status"],
        "capture_verification": {
            "status": capture["status"],
            "sofascore_event_id": capture["sofascore_event_id"],
            "manifest_sha256": capture["manifest_sha256"],
            "verified_payload_sha256": capture["verified_payload_sha256"],
            "unavailable_payloads": capture["unavailable_payloads"],
        },
        "canonical_match_enrichment": match_enrichment,
        "ingestion": result,
        "database_writes": 0,
        "canonical_promotion_performed": False,
    }


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a zero-write LUFC ingestion package from a verified SofaScore capture."
    )
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--importer-git-sha", required=True)
    parser.add_argument("--leeds-team-provider-id", type=int, default=34)
    parser.add_argument("--identity-package", type=Path, required=True)
    parser.add_argument("--identity-validation", type=Path, required=True)
    parser.add_argument("--canonical-diff", type=Path, required=True)
    parser.add_argument("--canonical-context", type=Path)
    parser.add_argument("--secondary-evidence", type=Path)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--rollback-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    try:
        result = build_package_from_capture(
            capture_dir=args.capture_dir,
            run_id=args.run_id,
            importer_git_sha=args.importer_git_sha,
            leeds_team_provider_id=args.leeds_team_provider_id,
            identity_package=_read_json_object(args.identity_package, "identity package"),
            identity_mapping_validation=_read_json_object(
                args.identity_validation, "identity mapping validation"
            ),
            canonical_diff=_read_json_object(args.canonical_diff, "canonical diff"),
            canonical_context=_optional_json_object(
                args.canonical_context, "canonical match context"
            ),
            secondary_evidence=_optional_json_object(
                args.secondary_evidence, "secondary evidence"
            ),
            backup=_optional_json_object(args.backup, "backup attestation"),
            rollback_manifest=_optional_json_object(
                args.rollback_manifest, "rollback manifest"
            ),
        )
        _write_json(args.output, result)
    except (CaptureToPackageError, RuntimeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1

    print(f"ZERO-WRITE INGESTION PACKAGE: {result['status']}")
    print(f"Output: {args.output}")
    print("Supabase/database writes: 0")
    print("Canonical promotion performed: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
