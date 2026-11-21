"""Integration tests for the executable script entry point."""

import runpy
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
import requests

import main


def test_script_entry_point_runs_download(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Run the script as a command without accessing the network."""
    url = "https://example.com/file.bin"
    response = MagicMock(spec=requests.Response)
    response.__enter__.return_value = response
    response.iter_content.return_value = [b"x" * main.BYTES_PER_MIB]
    get = Mock(return_value=response)
    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(time, "perf_counter", Mock(side_effect=[2.0, 4.0]))
    monkeypatch.setattr(sys, "argv", ["main.py", url, "1"])

    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(Path(main.__file__)), run_name="__main__")

    captured = capsys.readouterr()
    assert error.value.code == 0
    assert captured.out == (
        "Average time: 2.000s\n"
        "Total downloaded bytes: 1048576\n"
        "Download speed in MiB/s: 0.500\n"
    )
    assert captured.err == ""
    get.assert_called_once_with(url, timeout=10, stream=True)
