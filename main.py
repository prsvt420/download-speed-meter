import argparse
import sys
import time
from urllib.parse import urlsplit

import requests
import validators

DEFAULT_NUMBER_OF_REQUESTS: int = 10
CHUNK_SIZE: int = 64 * 1024
BYTES_PER_MIB: int = 1024**2


def parse_args() -> argparse.Namespace:
    """Parse and validate command-line arguments."""
    argument_parser: argparse.ArgumentParser = create_argument_parser()
    return argument_parser.parse_args()


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    argument_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=(
            "Measure download speed by sending sequential HTTP GET "
            "requests to the specified URL and downloading the complete "
            "response body for each request. Report the average request "
            "duration in seconds, the total response body size in bytes, "
            "and the overall download speed in MiB/s "
            "(1 MiB = 1,048,576 bytes)."
        )
    )

    argument_parser.add_argument(
        "url",
        type=validate_url,
        help=(
            "URL of the resource to download, including the http:// "
            "or https:// scheme. A large static file, such as an image, "
            "is suitable for measuring download speed."
        ),
    )

    argument_parser.add_argument(
        "number_of_requests",
        nargs="?",
        type=validate_number_of_requests,
        help=(
            "Number of sequential requests to perform. Must be a positive "
            "integer. Defaults to %(default)s."
        ),
        default=DEFAULT_NUMBER_OF_REQUESTS,
    )

    return argument_parser


def validate_url(url: str) -> str:
    """Validate an HTTP or HTTPS URL."""
    if not validators.url(url) or urlsplit(url=url).scheme not in (
        "http",
        "https",
    ):
        raise argparse.ArgumentTypeError(
            "Invalid URL. Provide a valid HTTP or HTTPS URL, "
            "for example: https://example.com/image.jpg"
        )

    return url


def validate_number_of_requests(number_of_requests: str) -> int:
    """Validate a number of requests."""
    try:
        number_of_requests: int = int(number_of_requests)  # type: ignore
    except ValueError:
        raise argparse.ArgumentTypeError(
            "The number of requests must be an integer."
        ) from None

    if number_of_requests < 1:  # type: ignore
        raise argparse.ArgumentTypeError(
            "The number of requests must be greater than zero."
        )

    return number_of_requests  # type: ignore


def download_once(*, url: str) -> tuple[float | int, int]:
    """Download the response body and return elapsed seconds and bytes."""
    bytes: int = 0
    start_time: float | int = time.perf_counter()

    with requests.get(url, timeout=10, stream=True) as response:
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            bytes += len(chunk)

    end_time: float | int = time.perf_counter()

    elapsed_time: float | int = end_time - start_time

    return elapsed_time, bytes


def main() -> int:
    """Run sequential downloads and print aggregate statistics."""
    total_time: float | int = 0.0
    total_bytes: int = 0

    args: argparse.Namespace = parse_args()
    url: str = args.url
    number_of_requests: int = args.number_of_requests

    try:
        for _ in range(number_of_requests):
            elapsed_time, bytes = download_once(url=url)
            total_time += elapsed_time
            total_bytes += bytes
    except requests.exceptions.RequestException as error:
        print(f"Download failed: {error}", file=sys.stderr)
        return 1

    average_time: float | int = total_time / number_of_requests
    download_speed: float | int = total_bytes / total_time / BYTES_PER_MIB

    print(f"Average time: {average_time:.3f}s")
    print(f"Total downloaded bytes: {total_bytes}")
    print(f"Download speed in MiB/s: {download_speed:.3f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
