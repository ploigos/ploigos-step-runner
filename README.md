[![Publish Release](https://github.com/ploigos/ploigos-step-runner/workflows/Publish%20Release/badge.svg)](https://github.com/ploigos/ploigos-step-runner/actions?query=workflow%3A%22Publish+Release%22)
[![Publish Dev](https://github.com/ploigos/ploigos-step-runner/workflows/Publish%20Dev/badge.svg?branch=main)](https://github.com/ploigos/ploigos-step-runner/actions?query=workflow%3A%22Publish+Dev%22+branch%3Amain)
<br />
[![Publish GitHub Pages](https://github.com/ploigos/ploigos-step-runner/workflows/Publish%20GitHub%20Pages/badge.svg?branch=main)](https://github.com/ploigos/ploigos-step-runner/actions?query=workflow%3A%22Publish+GitHub+Pages%22+branch%3Amain)
<br />
[![codecov](https://codecov.io/gh/ploigos/ploigos-step-runner/branch/main/graph/badge.svg)](https://codecov.io/gh/ploigos/ploigos-step-runner)
<br />
[![License](https://img.shields.io/github/license/ploigos/ploigos-step-runner?color=informational)](LICENSE)

# ploigos-step-runner
Ploigos Step Runner (PSR) implemented as a Python library.

## Documentation

- [Python Package Documentation](https://ploigos.github.io/ploigos-step-runner/)
- [Trusted Software Supply Chain (TSSC) Overview](https://rhtconsulting.github.io/tsc-docs/)
  * **NOTE** Old docs before Ploigos re-name/re-brandh. will be re-written and moved to Ploigos.

## Install

Latest Release
```bash
not yet released
```

Latest Development Release
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple ploigos-step-runner
```

## Development

> :warning: **If you are running RHEL7 or older versions of Python**: This project will need Python 3.3 or better to run. If you are running on RHEL7, you can invoke `python3` in place of `python` in the following commands.

### Set Up Development Environment
```bash
cd ploigos-step-runner
python -m venv .venvs/psr-dev
source .venvs/psr-dev/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[tests]'
```

### Run Tests
```bash
tox -e test
```

Or to run for just a particular implementer, and include the sections of code that you didn't cover

```bash
python3 -m pytest --cov=psr --cov-report term-missing tests/step_implementers/package/test_maven_package.py
```

### Run linter
```bash
tox -e lint
```

### Run linter and all tests (a good idea before a commit)
```bash
tox
```

### Generate the Documentation Locally
If you are updating the python documentation and want to generate locally this is how you do it.

```bash
tox -e docs
```
