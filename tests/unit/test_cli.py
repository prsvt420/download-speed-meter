"""Unit tests for argument validation and command-line parsing."""

import argparse
import sys

import pytest

import main


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/file.bin",
        "https://example.com/file.bin",
        "https://example.com:8443/files/file.bin?download=1#content",
    ],
)
def test_validate_url_preserves_valid_http_urls(url: str) -> None:
    """Return valid HTTP and HTTPS URLs without modifying them."""
    assert main.validate_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "",
        "example.com/file.bin",
        "https://",
        "https://invalid host/file.bin",
        "ftp://example.com/file.bin",
    ],
)
def test_validate_url_rejects_invalid_urls(url: str) -> None:
    """Reject malformed URLs and otherwise valid unsupported schemes."""
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid URL"):
        main.validate_url(url)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1", 1), ("10", 10), ("1000000", 1000000), ("+2", 2)],
)
def test_validate_number_accepts_positive_integers(
    value: str, expected: int
) -> None:
    """Convert positive integer arguments into request counts."""
    assert main.validate_number_of_requests(value) == expected


@pytest.mark.parametrize("value", ["0", "-1", "-100"])
def test_validate_number_rejects_nonpositive_integers(value: str) -> None:
    """Reject request counts which cannot produce a measurement."""
    with pytest.raises(argparse.ArgumentTypeError, match="greater than zero"):
        main.validate_number_of_requests(value)


@pytest.mark.parametrize("value", ["", "abc", "1.5", "1e2"])
def test_validate_number_rejects_nonintegers(value: str) -> None:
    """Report a useful argument error for noninteger request counts."""
    with pytest.raises(argparse.ArgumentTypeError, match="must be an integer"):
        main.validate_number_of_requests(value)


@pytest.mark.parametrize("count", [None, "1", "3"])
def test_argument_parser_uses_default_or_explicit_count(
    count: str | None,
) -> None:
    """Parse a URL with an optional request count."""
    argv = ["https://example.com/file.bin"]
    if count is not None:
        argv.append(count)

    args = main.create_argument_parser().parse_args(argv)

    assert args.url == argv[0]
    assert args.number_of_requests == (
        main.DEFAULT_NUMBER_OF_REQUESTS if count is None else int(count)
    )


@pytest.mark.parametrize("count", [None, "2"])
def test_parse_args_reads_command_line(
    monkeypatch: pytest.MonkeyPatch, count: str | None
) -> None:
    """Read the real argument list using the public parsing entry point."""
    argv = ["main.py", "https://example.com/file.bin"]
    if count is not None:
        argv.append(count)
    monkeypatch.setattr(sys, "argv", argv)

    args = main.parse_args()

    assert args.url == argv[1]
    assert args.number_of_requests == (
        main.DEFAULT_NUMBER_OF_REQUESTS if count is None else int(count)
    )


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "the following arguments are required: url"),
        (["invalid"], "Invalid URL"),
        (["ftp://example.com/file.bin"], "Invalid URL"),
        (["https://example.com/file.bin", "0"], "greater than zero"),
        (["https://example.com/file.bin", "many"], "must be an integer"),
        (["https://example.com/file.bin", "1", "extra"], "unrecognized"),
    ],
)
def test_parse_args_reports_invalid_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    message: str,
) -> None:
    """Write argument errors to stderr and exit with argparse's error code."""
    monkeypatch.setattr(sys, "argv", ["main.py", *argv])

    with pytest.raises(SystemExit) as error:
        main.parse_args()

    captured = capsys.readouterr()
    assert error.value.code == 2
    assert captured.out == ""
    assert message in captured.err


def test_parse_args_prints_help(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Describe the units, required URL, and default count in CLI help."""
    monkeypatch.setattr(sys, "argv", ["main.py", "--help"])

    with pytest.raises(SystemExit) as error:
        main.parse_args()

    captured = capsys.readouterr()
    assert error.value.code == 0
    assert "MiB/s" in captured.out
    assert "http://" in captured.out
    assert f"Defaults to {main.DEFAULT_NUMBER_OF_REQUESTS}" in captured.out
    assert captured.err == ""
