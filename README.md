[![Publish Release](https://github.com/rhtconsulting/tssc-python-package/workflows/Publish%20Release/badge.svg)](https://github.com/rhtconsulting/tssc-python-package/actions?query=workflow%3A%22Publish+Release%22)
[![Publish Dev](https://github.com/rhtconsulting/tssc-python-package/workflows/Publish%20Dev/badge.svg?branch=main)](https://github.com/rhtconsulting/tssc-python-package/actions?query=workflow%3A%22Publish+Dev%22+branch%3Amain)
<br />
[![Publish GitHub Pages](https://github.com/rhtconsulting/tssc-python-package/workflows/Publish%20GitHub%20Pages/badge.svg?branch=main)](https://github.com/rhtconsulting/tssc-python-package/actions?query=workflow%3A%22Publish+GitHub+Pages%22+branch%3Amain)
<br />
[![codecov](https://codecov.io/gh/rhtconsulting/tssc-python-package/branch/main/graph/badge.svg)](https://codecov.io/gh/rhtconsulting/tssc-python-package)
<br />
[![License](https://img.shields.io/github/license/rhtconsulting/tssc-python-package?color=informational)](LICENSE)

# tssc-python-package
Trusted Software Supply Chain (TSSC) implemented as a Python library.

## Documentation

- [Python Package Documentation](https://rhtconsulting.github.io/tssc-python-package/)
- [Trusted Software Supply Chain (TSSC) Overview](https://rhtconsulting.github.io/tsc-docs/)

## Install

Latest Release
```bash
not yet released
```

Latest Development Release
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple tssc
```

## Development

> :warning: **If you are running RHEL7 or older versions of Python**: This project will need Python 3.3 or better to run. If you are running on RHEL7, you can invoke `python3` in place of `python` in the following commands.

### Set Up Development Environment
```bash
cd tssc-python-package
python -m venv .venvs/tssc-dev
source .venvs/tssc-dev/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[tests]'
```

### Run Tests
```bash
python -m pytest --cov=tssc --cov-report term-missing tests
```

Or to run for just a particular implementer, and include the sections of code that you didn't cover

```bash
python3 -m pytest --cov=tssc --cov-report term-missing tests/step_implementers/package/test_maven_package.py
```

### Run linter
```bash
python -m pylint --rcfile=setup.cfg tssc
```

### Generate the Documentation Locally
If you are updating the python documentation and want to generate locally this is how you do it.

```bash
pip install pdoc3
pdoc3 --html --output-dir pdoc3-html tssc/
```
