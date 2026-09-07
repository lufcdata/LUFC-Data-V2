#!/usr/bin/env python3
"""Build a fully evidence-driven zero-write ingestion package from a verified capture.

The preferred path now requires only verified raw capture, LUFC-scoped mapping rows,
canonical LUFC context and explicitly attributed secondary evidence. Reconciliation,
identity resolution, canonical diff and promotion-gate inputs are all derived inside
the zero-write pipeline. Prebuilt identity/diff inputs remain supported for controlled
compatibility tests and forensic replays.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

from sofascore_canonical_match_enrichment import (
    build_canonical_match_enrichment,
    merge_match_enrichment_into_canonical_diff,
)
from sofascore_capture_loader import load_verified_capture
from sofascore_evidence_validations import build_evidence_validations
from sofascore_source_canonical_diff import build_source_canonical_diff
from sofascore_source_derived_dry_run import build_source_derived_dry_run
from sofascore_source_driven_ingestion_package import (
    build_fully_evidence_driven_ingestion_package,
)
from sofascore_source_identity_package import build_source_identity_package


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


def _mapping_rows_from_document(document: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = document.get("mappings")
    if not isinstance(rows, list) or not rows:
        raise CaptureToPackageError("identity mappings document must contain a non-empty mappings[]")
    if any(not isinstance(row, Mapping) for row in rows):
        raise CaptureToPackageError("identity mappings document contains a non-object row")
    return list(rows)


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


def _identity_mode(
    *,
    raw_payloads: Mapping[str, Any],
    leeds_team_provider_id: int,
    identity_package: Mapping[str, Any] | None,
    identity_mapping_validation: Mapping[str, Any] | None,
    identity_mappings: Iterable[Mapping[str, Any]] | None,
) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any] | None]:
    if identity_mappings is not None:
        if identity_package is not None or identity_mapping_validation is not None:
            raise CaptureToPackageError(
                "provide either identity_mappings or prebuilt identity package/validation, not both"
            )
        source_identity = build_source_identity_package(
            raw_payloads=raw_payloads,
            leeds_team_provider_id=leeds_team_provider_id,
            mappings=identity_mappings,
        )
        return (
            source_identity["identity_package"],
            source_identity["identity_mapping_validation"],
            source_identity,
        )

    if identity_package is None or identity_mapping_validation is None:
        raise CaptureToPackageError(
            "identity mappings or both prebuilt identity package and validation are required"
        )
    return identity_package, identity_mapping_validation, None


def build_package_from_capture(
    *,
    capture_dir: Path,
    run_id: str,
    importer_git_sha: str,
    leeds_team_provider_id: int,
    canonical_diff: Mapping[str, Any] | None = None,
    identity_package: Mapping[str, Any] | None = None,
    identity_mapping_validation: Mapping[str, Any] | None = None,
    identity_mappings: Iterable[Mapping[str, Any]] | None = None,
    canonical_context: Mapping[str, Any] | None = None,
    secondary_evidence: Mapping[str, Any] | None = None,
    backup: Mapping[str, Any] | None = None,
    rollback_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify raw capture and build one source-derived zero-write ingestion package."""
    capture = load_verified_capture(Path(capture_dir))
    raw_payloads = capture.get("raw_payloads")
    if not isinstance(raw_payloads, Mapping):
        raise CaptureToPackageError("verified capture has no raw payload map")

    effective_identity_package, effective_identity_validation, source_identity = _identity_mode(
        raw_payloads=raw_payloads,
        leeds_team_provider_id=leeds_team_provider_id,
        identity_package=identity_package,
        identity_mapping_validation=identity_mapping_validation,
        identity_mappings=identity_mappings,
    )

    source_bundle: Mapping[str, Any] | None = None
    evidence_bundle: Mapping[str, Any] | None = None
    match_enrichment: Mapping[str, Any] | None = None

    # A missing prebuilt diff selects the preferred source-derived path. Canonical
    # context is mandatory because season/competition/manager-spell IDs are LUFC-owned.
    if canonical_diff is None:
        if canonical_context is None:
            raise CaptureToPackageError(
                "canonical_context is required when canonical diff is source-derived"
            )
        source_bundle = build_source_derived_dry_run(
            raw_payloads=raw_payloads,
            leeds_team_provider_id=leeds_team_provider_id,
        )
        evidence_bundle = build_evidence_validations(
            raw_payloads=raw_payloads,
            leeds_team_provider_id=leeds_team_provider_id,
            secondary_evidence=secondary_evidence,
        )
        effective_diff = build_source_canonical_diff(
            raw_payloads=raw_payloads,
            source_bundle=source_bundle,
            evidence_bundle=evidence_bundle,
            identity_package=effective_identity_package,
            canonical_context=canonical_context,
            leeds_team_provider_id=leeds_team_provider_id,
        )
        match_enrichment = effective_diff.get("match_enrichment") if isinstance(effective_diff, Mapping) else None
    else:
        effective_diff = canonical_diff
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
        identity_package=effective_identity_package,
        canonical_diff=effective_diff,
        identity_mapping_validation=effective_identity_validation,
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
        "source_identity": source_identity,
        "source_derived_canonical_diff": canonical_diff is None,
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
    parser.add_argument("--identity-mappings", type=Path)
    parser.add_argument("--identity-package", type=Path)
    parser.add_argument("--identity-validation", type=Path)
    parser.add_argument("--canonical-diff", type=Path)
    parser.add_argument("--canonical-context", type=Path)
    parser.add_argument("--secondary-evidence", type=Path)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--rollback-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    try:
        mappings = None
        identity_package = None
        identity_validation = None
        if args.identity_mappings is not None:
            mappings_document = _read_json_object(args.identity_mappings, "identity mappings")
            mappings = _mapping_rows_from_document(mappings_document)
            if args.identity_package is not None or args.identity_validation is not None:
                raise CaptureToPackageError(
                    "--identity-mappings cannot be combined with --identity-package/--identity-validation"
                )
        else:
            if args.identity_package is None or args.identity_validation is None:
                raise CaptureToPackageError(
                    "provide --identity-mappings or both --identity-package and --identity-validation"
                )
            identity_package = _read_json_object(args.identity_package, "identity package")
            identity_validation = _read_json_object(
                args.identity_validation, "identity mapping validation"
            )

        canonical_context = _optional_json_object(
            args.canonical_context, "canonical match context"
        )
        canonical_diff = _optional_json_object(args.canonical_diff, "canonical diff")
        if canonical_diff is None and canonical_context is None:
            raise CaptureToPackageError(
                "--canonical-context is required when --canonical-diff is omitted"
            )

        result = build_package_from_capture(
            capture_dir=args.capture_dir,
            run_id=args.run_id,
            importer_git_sha=args.importer_git_sha,
            leeds_team_provider_id=args.leeds_team_provider_id,
            identity_package=identity_package,
            identity_mapping_validation=identity_validation,
            identity_mappings=mappings,
            canonical_diff=canonical_diff,
            canonical_context=canonical_context,
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
