import io
import zipfile

import pytest

from testsel.collector.junit import UnsafeArchiveError, extract_results_from_zip, parse_junit_xml

SUITE = b"""<?xml version="1.0"?>
<testsuites>
  <testsuite name="pytest" tests="5">
    <testcase classname="tests.test_a" name="test_ok" time="0.01"/>
    <testcase classname="tests.test_a" name="test_bad" time="0.5">
      <failure type="AssertionError" message="boom">trace</failure>
    </testcase>
    <testcase classname="tests.test_a" name="test_err" time="0.2">
      <error type="RuntimeError">trace</error>
    </testcase>
    <testcase classname="tests.test_b" name="test_skip" time="0.0">
      <skipped message="why"/>
    </testcase>
    <testcase name="no_class" time="abc"/>
  </testsuite>
</testsuites>
"""


def by_id(results):
    return {r.test_id: r for r in results}


def test_parses_all_outcomes():
    r = by_id(parse_junit_xml(SUITE))
    assert r["tests.test_a::test_ok"].outcome == "pass"
    assert r["tests.test_a::test_ok"].duration_s == 0.01
    assert r["tests.test_a::test_bad"].outcome == "fail"
    assert r["tests.test_a::test_bad"].error_type == "AssertionError"
    assert r["tests.test_a::test_err"].outcome == "error"
    assert r["tests.test_b::test_skip"].outcome == "skip"
    assert r["no_class"].outcome == "pass"
    assert r["no_class"].duration_s is None  # unparseable time tolerated


def test_bare_testsuite_root():
    xml = b'<testsuite><testcase classname="c" name="t"/></testsuite>'
    assert [r.test_id for r in parse_junit_xml(xml)] == ["c::t"]


def test_duplicate_ids_keep_most_severe():
    xml = (
        b'<testsuite><testcase classname="c" name="t"/>'
        b'<testcase classname="c" name="t"><failure type="X"/></testcase></testsuite>'
    )
    (r,) = parse_junit_xml(xml)
    assert r.outcome == "fail"


def test_rejects_entity_declarations():
    bomb = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><testsuite>&a;</testsuite>'
    with pytest.raises(UnsafeArchiveError):
        parse_junit_xml(bomb)


def make_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_zip_merges_files_and_skips_non_junit():
    blob = make_zip(
        {
            "reports/a.xml": SUITE,
            "reports/coverage.xml": b"<coverage><packages/></coverage>",
            "reports/notes.txt": b"ignore me",
            "reports/broken.xml": b"<not closed",
        }
    )
    ids = {r.test_id for r in extract_results_from_zip(blob)}
    assert "tests.test_a::test_ok" in ids
    assert len(ids) == 5


def test_zip_too_many_entries(monkeypatch):
    monkeypatch.setattr("testsel.collector.junit.MAX_ENTRIES", 2)
    blob = make_zip({f"{i}.xml": b"<testsuite/>" for i in range(3)})
    with pytest.raises(UnsafeArchiveError):
        extract_results_from_zip(blob)


def test_zip_uncompressed_size_limit(monkeypatch):
    monkeypatch.setattr("testsel.collector.junit.MAX_XML_BYTES", 100)
    blob = make_zip({"big.xml": b"<testsuite>" + b" " * 500 + b"</testsuite>"})
    with pytest.raises(UnsafeArchiveError):
        extract_results_from_zip(blob)
