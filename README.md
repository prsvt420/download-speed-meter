# Download Speed Meter

A Python command-line utility for measuring download speed from a specified
HTTP or HTTPS URL. It downloads the complete response body several times in
sequence and reports the average request duration, total downloaded bytes,
and overall throughput in MiB/s.

## Features

- HTTP and HTTPS URL validation.
- Configurable number of sequential requests, with a default of 10.
- Streaming downloads in 64 KiB chunks without saving files to disk.
- Average request duration, total downloaded bytes, and throughput statistics.
- Download failure reporting with a nonzero exit code.
- Unit and integration tests with a 100% coverage requirement.
- Formatting, linting, type checking, and tests through pre-commit hooks.
- Commit messages written using Conventional Commits.

## Technologies

- [Python 3.13+](https://www.python.org/)
- [Requests](https://requests.readthedocs.io/en/latest/)
- [uv](https://docs.astral.sh/uv/)
- [pytest](https://docs.pytest.org/en/stable/)
- [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/)
- [mypy](https://mypy-lang.org/)
- [Black](https://black.readthedocs.io/en/stable/)
- [isort](https://isort.readthedocs.io/en/latest/)
- [Flake8](https://flake8.pycqa.org/en/latest/)
- [pre-commit](https://pre-commit.com/)
- [Git](https://git-scm.com/)

## Requirements and installation

- Python 3.13 or newer. The project's `.python-version` selects Python 3.13.
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Git to use the repository's pre-commit hooks.

Clone or download this repository, then run the following from its root:

```sh
uv sync --locked
```

This creates the project environment and installs the locked dependencies.
The `dev` dependency group, including tests and code quality tools, is
[included by default](https://docs.astral.sh/uv/concepts/projects/sync/#syncing-development-dependencies).

## Usage

```text
uv run python main.py URL [number_of_requests]
```

| Argument | Description | Default |
| --- | --- | --- |
| `URL` | Valid HTTP or HTTPS URL of the resource to download | Required |
| `number_of_requests` | Positive integer specifying sequential downloads | `10` |

Replace the example URL below with a real, directly downloadable resource.
A large static file is useful for measuring download speed.

Use the default number of requests:

```sh
uv run python main.py "https://example.com/file.bin"
```

Perform five requests:

```sh
uv run python main.py "https://example.com/file.bin" 5
```

Show command-line help:

```sh
uv run python main.py --help
```

Illustrative output:

```text
Average time: 0.500s
Total downloaded bytes: 10485760
Download speed in MiB/s: 2.000
```

Actual values depend on the resource, server, and network conditions.

## How measurement works

Each request downloads the complete response body before the next request
starts. The timer starts immediately before the HTTP request and stops after
the body has been consumed and the response has been closed.

The reported statistics use the following calculations:

```text
average_time = total_elapsed_seconds / number_of_requests
download_speed = total_downloaded_bytes / total_elapsed_seconds / 1_048_576
```

One MiB is 1,048,576 bytes. The reported speed is in MiB per second.
Throughput is calculated from total bytes and total time across all requests.
Request setup and response processing are included in the measured time.

Byte counts come from the chunks returned by Requests. Compressed responses
may be decoded automatically, so the reported size describes the consumed
response body. See the
[Requests streaming documentation](https://requests.readthedocs.io/en/latest/user/quickstart/#raw-response-content).

Each request uses `timeout=10`. The
[Requests timeout](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts)
applies to connection and read waits; a download that continues receiving
data can take longer than 10 seconds.

## Errors and exit codes

Invalid arguments are rejected before any download starts. If a download
fails, the application writes `Download failed: ...` to standard error and
stops immediately. Partial statistics are omitted.

| Exit code | Meaning |
| --- | --- |
| `0` | Successful measurement or help output |
| `1` | Download failure, including HTTP, connection, or streaming errors |
| `2` | Invalid or missing command-line arguments |

## Project structure

```text
download-speed-meter/
├── main.py                     # CLI, downloads, and statistics
├── pyproject.toml              # Dependencies and tool configuration
├── uv.lock                     # Locked dependency versions
├── .python-version             # Selected Python version
├── .pre-commit-config.yaml     # Commit-time checks
├── scripts/
│   ├── run_mypy.py             # Run mypy for the whole project
│   └── run_pytest.py            # Run pytest when test modules exist
├── tests/
│   ├── unit/
│   │   ├── test_cli.py          # Validation and argument parsing
│   │   └── test_download.py     # Streaming, timing, and resource handling
│   └── integration/
│       ├── test_main.py         # CLI parsing, statistics, and errors
│       └── test_script.py       # Executable script entry point
└── README.md
```

## Testing

The suite contains 55 test cases:

- **39 unit tests** cover argument validation, parsing, streaming downloads,
  byte counts, response cleanup, and download errors.
- **16 integration tests** cover the CLI and application workflow, output,
  failure handling, and execution through the script entry point.

HTTP responses are mocked, so the suite runs without contacting external
servers. Controlled timer values make speed calculations reproducible.

Run the complete suite with coverage:

```sh
uv run pytest
```

Line and branch coverage are enabled. The complete suite currently reaches
100% coverage, and the configured coverage threshold is 100%.

Run a group independently:

```sh
uv run pytest tests/unit --no-cov
uv run pytest tests/integration --no-cov
```

Partial runs disable coverage with `--no-cov` because the 100% threshold
applies to the complete suite.

## Code quality and development workflow

The project uses a line length of 79 characters, Google-style docstrings,
double-quoted strings, and strict mypy checks. Flake8 is extended with
`flake8-bandit`, `flake8-bugbear`, `flake8-docstrings`, `flake8-eradicate`,
`flake8-pyproject`, `flake8-quotes`, and `pep8-naming`.

Install the Git hooks after installing the project dependencies:

```sh
uv run pre-commit install
```

Run all configured hooks manually:

```sh
uv run pre-commit run --all-files
```

The hooks check structured file syntax, whitespace, file endings, merge
conflicts, filename case conflicts, debug statements, and private keys.
They also run Black, isort, Flake8, mypy, and pytest. Formatting hooks may
update files; review their changes before committing.

Individual checks are also available:

```sh
uv run black --check .
uv run isort --check-only .
uv run flake8 .
uv run mypy .
uv run pytest
```

## Commit convention

Commit messages follow
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
The project uses English commit descriptions with the following structure:

```text
type(scope): short description
```

The scope identifies the affected area and is optional. Examples from the
project history:

```text
feat(cli): add download speed measurement
test(cli): cover CLI validation, downloads and error handling
chore(pre-commit): add pytest hook
chore(pyproject): translate project description into English
```

Common types used for contributions:

| Type | Purpose |
| --- | --- |
| `feat` | Add functionality |
| `fix` | Fix a bug |
| `docs` | Update documentation |
| `test` | Add or update tests |
| `refactor` | Restructure code while preserving behavior |
| `style` | Change formatting |
| `chore` | Maintain tooling or project configuration |

Breaking changes use `!` before the colon or a `BREAKING CHANGE:` footer.
Commit message validation is currently manual; the configured pre-commit
hooks run code and test checks.
