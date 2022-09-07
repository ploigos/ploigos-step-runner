[![Publish Release](https://github.com/ploigos/ploigos-step-runner/workflows/Publish%20Release/badge.svg)](https://github.com/ploigos/ploigos-step-runner/actions?query=workflow%3A%22Publish+Release%22)
[![Publish Dev](https://github.com/ploigos/ploigos-step-runner/workflows/Publish%20Dev/badge.svg?branch=main)](https://github.com/ploigos/ploigos-step-runner/actions?query=workflow%3A%22Publish+Dev%22+branch%3Amain)
<br />
[![Publish GitHub Pages](https://github.com/ploigos/ploigos-step-runner/workflows/Publish%20GitHub%20Pages/badge.svg?branch=main)](https://github.com/ploigos/ploigos-step-runner/actions?query=workflow%3A%22Publish+GitHub+Pages%22+branch%3Amain)
<br />
[![codecov](https://codecov.io/gh/ploigos/ploigos-step-runner/branch/main/graph/badge.svg)](https://codecov.io/gh/ploigos/ploigos-step-runner)
<br />
[![License](https://img.shields.io/github/license/ploigos/ploigos-step-runner?color=informational)](LICENSE)

# ploigos-step-runner

Ploigos Step Runner (PSR) is a middleware tool to execute pipeline steps,
independent of your application and pipeline tech stack. PSR runs on workflow
runners like Jenkins, Tekton, GitHub Actions, GitLab CI, or any other workflow
runner that can execute commands.

**PSR is not a pipeline!** It is a CLI tool called in your pipeline by a
workflow runner as a command: `psr -s hello-world -c psr.yml`.

PSR abstracts the implementation of a *step* from a specific product or
solution. A few common steps most pipelines implement are *packaging*, *unit
testing*, and *deploying*. The implementation of these steps differs between a
Java and JavaScript application. With PSR, the same pipeline can be used on
both Java and JS applications. Available PSR steps can be found
[here](https://ploigos.github.io/ploigos-step-runner/#step-configuration).

Each PSR step has one or more *Step Implementers*. A step implementer does two
things:

1. Integrates with a given product or solution
2. Produces output in a standard format that can be used or validated by other
pipeline steps

PSR uses a common file, *psr.yml*, for configuration of all steps in a
pipeline. This file exists in an application source code repo alongside a
pipeline definition file (Jenkinsfile, .gitlab-ci.yml, etc.). PSR abstracts
implementation from the pipeline definition, allowing the same pipeline
definition to be reused for all applications, regardless of the application
language and framework.

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

> What if I want to use a tool that PSR doesn't have an step implementer for?

Each PSR step has a corresponding *step_implementer* Python module under
[src/ploigos_step_runner/step_implementers](src/ploigos_step_runner/step_implementers).
If you need to use a tool that PSR does not have a step implementer for, you
will need to create one. See [CONTRIBUTING.md](CONTRIBUTING.md) for
instructions on creating step implementers.

An AdHoc step implementer is proposed in #131 that would allow for a command or
script to be specified in `psr.yml`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
