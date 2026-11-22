"""Parse JUnit XML test reports, including from untrusted zip artifacts.

Artifacts come from arbitrary public repositories, so every input is treated as
hostile: DOCTYPE/ENTITY declarations are rejected (XML bomb / XXE), and zip
extraction is capped by entry count and uncompressed size (zip bomb).
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile

from testsel.shared.models import TestResult

MAX_XML_BYTES = 50 * 1024 * 1024  # per XML file, uncompressed
MAX_TOTAL_BYTES = 200 * 1024 * 1024  # per zip, uncompressed
MAX_ENTRIES = 500

# When one test id appears several times in a run (parametrization collisions,
# retries inside one report), keep the most severe outcome.
_SEVERITY = {"skip": 0, "pass": 1, "fail": 2, "error": 3}


class UnsafeArchiveError(ValueError):
    pass


def parse_junit_xml(data: bytes) -> list[TestResult]:
    head = data[:4096].upper()
    if b"<!DOCTYPE" in head or b"<!ENTITY" in data.upper():
        raise UnsafeArchiveError("DOCTYPE/ENTITY declarations are not allowed")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"invalid XML: {exc}") from exc

    results: dict[str, TestResult] = {}
    for case in root.iter("testcase"):
        name = case.get("name")
        if not name:
            continue
        classname = case.get("classname") or ""
        test_id = f"{classname}::{name}" if classname else name

        outcome, error_type = "pass", None
        for child in case:
            tag = child.tag
            if tag in ("failure", "error", "skipped"):
                outcome = {"failure": "fail", "error": "error", "skipped": "skip"}[tag]
                error_type = child.get("type") or None
                break  # first status child wins

        try:
            duration = float(case.get("time")) if case.get("time") else None
        except ValueError:
            duration = None

        result = TestResult(test_id, outcome, duration, error_type)
        prev = results.get(test_id)
        if prev is None or _SEVERITY[outcome] > _SEVERITY[prev.outcome]:
            results[test_id] = result
    return list(results.values())


def extract_results_from_zip(blob: bytes) -> list[TestResult]:
    """Parse every .xml file in a zip artifact; non-JUnit XML files are skipped."""
    merged: dict[str, TestResult] = {}
    total = 0
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_ENTRIES:
            raise UnsafeArchiveError("too many entries in archive")
        for info in infos:
            if info.is_dir() or not info.filename.lower().endswith(".xml"):
                continue
            total += info.file_size
            if info.file_size > MAX_XML_BYTES or total > MAX_TOTAL_BYTES:
                raise UnsafeArchiveError("archive exceeds uncompressed size limit")
            with zf.open(info) as fh:
                data = fh.read(MAX_XML_BYTES + 1)
            if len(data) > MAX_XML_BYTES:  # header lied about size
                raise UnsafeArchiveError("archive entry larger than declared")
            try:
                parsed = parse_junit_xml(data)
            except UnsafeArchiveError:
                raise
            except ValueError:
                continue  # not a parseable report, ignore this file
            for r in parsed:
                prev = merged.get(r.test_id)
                if prev is None or _SEVERITY[r.outcome] > _SEVERITY[prev.outcome]:
                    merged[r.test_id] = r
    return list(merged.values())
