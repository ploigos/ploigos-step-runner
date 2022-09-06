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
- [Ploigos Overview](https://ploigos.github.io/ploigos-docs/)

## Install

Latest Release

```bash
pip install ploigos-step-runner
```

Latest Development Release

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple ploigos-step-runner
```

## FAQ

> What is a Workflow Runner?

A workflow runner is a Continuous Integration (CI) tool that execute pipelines. Common workflow runners are Jenkins, Tekton, GitHub Actions, and GitLab CI.

> What do I do if I want to use a tool that PSR doesn't have an implementer for?

Each PSR step has a corresponding *step_implementer* Python module under
[src/ploigos_step_runner/step_implementers](src/ploigos_step_runner/step_implementers).
If you need to use a tool that PSR does not have a step implementer for you
will need to create one. See [CONTRIBUTING.md](CONTRIBUTING.md) for
instructions on creating step implementers.

An AdHoc step implementer is proposed in #131 that would allow for a command or
script to be specified in `psr.yml`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
