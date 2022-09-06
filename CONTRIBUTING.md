# Contributing

> :warning: **If you are running RHEL7 or older versions of Python**: This project will need Python 3.3 or better to run. If you are running on RHEL7, you can invoke `python3` in place of `python` in the following commands.

## Set Up Development Environment

```bash
cd ploigos-step-runner
python -m venv .venvs/psr-dev
source .venvs/psr-dev/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[tests]'
```

## Run Tests

> :notebook: Some tests require `mvn` command in your PATH. Install with brew/yum/dnf prior to running tests.

```bash
tox -e test
```

Or to run for just a particular implementer, and include the sections of code that you didn't cover

```bash
python3 -m pytest --cov --cov-report term-missing tests/step_implementers/package/test_maven_package.py
```

## Run linter

```bash
tox -e lint
```

## Run linter and all tests (a good idea before a commit)

```bash
tox
```

## Generate the Documentation Locally

If you are updating the python documentation and want to generate locally this is how you do it.

```bash
tox -e docs
```

## Troubleshooting

> Fatal error calling step (generate-metadata): Can not add duplicate StepResult for step (generate-metadata), sub step (Maven), and environment (None)

This error (and similar duplicate step errors) occurs when a step that was previously run is re-run. PSR expects a given step and sub-step to run only once. In an actual pipeline, this indicates an error. When developing step implementers, it is common to trigger this error when re-running steps to test changes.

To fix this, remove the ./step-runner-working directory:

```bash
rm -r ./step-runner-working
```
