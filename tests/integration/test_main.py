"""Integration tests for CLI parsing, statistics, and failure reporting."""

import sys
from unittest.mock import call, patch

import pytest
import requests

import main as speed_meter

URL = "https://example.com/file.bin"


@pytest.mark.parametrize(
    ("downloads", "expected_output"),
    [
        (
            [(2.0, 1048576)],
            "Average time: 2.000s\n"
            "Total downloaded bytes: 1048576\n"
            "Download speed in MiB/s: 0.500\n",
        ),
        (
            [(0.25, 1048576), (0.75, 3145728), (0.5, 0)],
            "Average time: 0.500s\n"
            "Total downloaded bytes: 4194304\n"
            "Download speed in MiB/s: 2.667\n",
        ),
        (
            [(0.5, 0), (1.5, 0)],
            "Average time: 1.000s\n"
            "Total downloaded bytes: 0\n"
            "Download speed in MiB/s: 0.000\n",
        ),
    ],
)
def test_main_prints_aggregate_statistics(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    downloads: list[tuple[float, int]],
    expected_output: str,
) -> None:
    """Calculate throughput from total bytes and total elapsed time."""
    monkeypatch.setattr(sys, "argv", ["main.py", URL, str(len(downloads))])

    with patch.object(
        speed_meter, "download_once", side_effect=downloads
    ) as download:
        result = speed_meter.main()

    assert result == 0
    assert download.call_args_list == [call(url=URL)] * len(downloads)
    captured = capsys.readouterr()
    assert captured.out == expected_output
    assert captured.err == ""


def test_main_uses_default_number_of_requests(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Perform ten downloads when the optional count is omitted."""
    monkeypatch.setattr(sys, "argv", ["main.py", URL])

    with patch.object(
        speed_meter, "download_once", return_value=(0.5, 524288)
    ) as download:
        result = speed_meter.main()

    assert result == 0
    assert download.call_args_list == [call(url=URL)] * 10
    captured = capsys.readouterr()
    assert captured.out == (
        "Average time: 0.500s\n"
        "Total downloaded bytes: 5242880\n"
        "Download speed in MiB/s: 1.000\n"
    )
    assert captured.err == ""


@pytest.mark.parametrize("successful_requests", [0, 1])
@pytest.mark.parametrize(
    "error",
    [
        requests.exceptions.ConnectionError("Connection refused"),
        requests.exceptions.Timeout("Request timed out"),
        requests.exceptions.HTTPError("503 Service Unavailable"),
        requests.exceptions.ChunkedEncodingError("Incomplete response"),
    ],
)
def test_main_stops_after_download_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    successful_requests: int,
    error: requests.exceptions.RequestException,
) -> None:
    """Report a failed download and stop without printing partial totals."""
    monkeypatch.setattr(sys, "argv", ["main.py", URL, "3"])
    results: list[tuple[float, int] | requests.exceptions.RequestException] = [
        (0.5, 1048576)
    ] * successful_requests
    results.append(error)

    with patch.object(
        speed_meter, "download_once", side_effect=results
    ) as download:
        result = speed_meter.main()

    assert result == 1
    assert download.call_args_list == [call(url=URL)] * (
        successful_requests + 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"Download failed: {error}\n"


@pytest.mark.parametrize("arguments", [[], [URL, "0"], ["invalid-url"]])
def test_main_does_not_download_with_invalid_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
) -> None:
    """Reject invalid command-line arguments before making HTTP requests."""
    monkeypatch.setattr(sys, "argv", ["main.py", *arguments])

    with patch.object(speed_meter, "download_once") as download:
        with pytest.raises(SystemExit) as captured_exit:
            speed_meter.main()

    assert captured_exit.value.code == 2
    download.assert_not_called()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error:" in captured.err
