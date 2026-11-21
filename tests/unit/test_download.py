"""Unit tests for streaming downloads and their resource handling."""

from collections.abc import Iterator
from unittest.mock import ANY, MagicMock, call, patch

import pytest
import requests

import main as speed_meter

URL = "https://example.com/file.bin"


@pytest.fixture
def http_get() -> Iterator[MagicMock]:
    """Replace HTTP requests with a mock context manager."""
    with patch("main.requests.get") as mocked_get:
        yield mocked_get


@pytest.mark.parametrize(
    ("chunks", "expected_bytes"),
    [
        ([b"abc", b"", b"de"], 5),
        ([b"\x00\xff", b"\x80"], 3),
        ([], 0),
        ([b""], 0),
    ],
)
def test_download_counts_response_bytes(
    http_get: MagicMock, chunks: list[bytes], expected_bytes: int
) -> None:
    """Measure the complete response body and close it afterward."""
    response = http_get.return_value.__enter__.return_value
    response.iter_content.return_value = iter(chunks)

    with patch("main.time.perf_counter", side_effect=[10.0, 12.5]) as timer:
        result = speed_meter.download_once(url=URL)

    assert result == (2.5, expected_bytes)
    assert timer.call_count == 2
    http_get.assert_called_once_with(URL, timeout=10, stream=True)
    response.raise_for_status.assert_called_once_with()
    response.iter_content.assert_called_once_with(chunk_size=64 * 1024)
    assert response.mock_calls == [
        call.raise_for_status(),
        call.iter_content(chunk_size=64 * 1024),
    ]
    http_get.return_value.__exit__.assert_called_once_with(None, None, None)


@pytest.mark.parametrize(
    "error",
    [
        requests.exceptions.ConnectionError("Connection refused"),
        requests.exceptions.Timeout("Request timed out"),
    ],
)
def test_download_propagates_connection_errors(
    http_get: MagicMock, error: requests.exceptions.RequestException
) -> None:
    """Propagate request failures without trying to read a response."""
    http_get.side_effect = error

    with pytest.raises(type(error)) as captured:
        speed_meter.download_once(url=URL)

    assert captured.value is error
    http_get.assert_called_once_with(URL, timeout=10, stream=True)
    http_get.return_value.__enter__.assert_not_called()


def test_download_propagates_http_errors(http_get: MagicMock) -> None:
    """Close an unsuccessful HTTP response without consuming its body."""
    response = http_get.return_value.__enter__.return_value
    error = requests.exceptions.HTTPError("404 Not Found")
    response.raise_for_status.side_effect = error

    with pytest.raises(requests.exceptions.HTTPError) as captured:
        speed_meter.download_once(url=URL)

    assert captured.value is error
    response.iter_content.assert_not_called()
    http_get.return_value.__exit__.assert_called_once_with(
        type(error), error, ANY
    )


def test_download_closes_response_after_stream_error(
    http_get: MagicMock,
) -> None:
    """Close a response when reading fails after a partial download."""
    response = http_get.return_value.__enter__.return_value
    error = requests.exceptions.ChunkedEncodingError("Incomplete response")

    def interrupted_stream() -> Iterator[bytes]:
        """Yield part of the body before simulating a broken connection."""
        yield b"partial body"
        raise error

    response.iter_content.return_value = interrupted_stream()

    with pytest.raises(requests.exceptions.ChunkedEncodingError) as captured:
        speed_meter.download_once(url=URL)

    assert captured.value is error
    response.raise_for_status.assert_called_once_with()
    http_get.return_value.__exit__.assert_called_once_with(
        type(error), error, ANY
    )
