# Contributing

## Fork and Clone Repo

Fork this repo under your GitHub account. After forking, clone the fork to your
local machine: (replace *your-username*)

```bash
git clone https://github.com/your-username/ploigos-step-runner.git
```

## Set Up Development Environment

> :warning: **If you are running RHEL7 or older versions of Python**: This project will need Python 3.3 or better to run. If you are running on RHEL7, you can invoke `python3` in place of `python` in the following commands.

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

## Adding a New Step Implementer

The easiest way to add a new step implementer is to copy an existing step
implementer. The hello-world step and it's implementers were created bare bones
for developers to copy and create their own implementers.

The source code for step implementers is under
*./src/ploigos_step_runner/step_implementers*. Each module under this directory
contains implementers for a given step. In the case of hello-world,
"hello-world" is the module for the step itself, while "short_greeting" and
"long_greeting" are the modules for the implementers.

To run hello-world (or your step),

1. Create a *psr.yaml* file:

```bash
# Replace step/implementer if testing outside of hello-world
cat > psr.yaml << EOF
hello-world:
  - implementer: ShortGreeting
EOF
```

2. Run PSR:

```bash
psr -s hello-world -c psr.yaml
```

3. Validate the output, both stdout and artifacts sections.

4. Delete the PSR working directory:

```bash
rm -r ./step-runner-working
```

> :warning: This step is important. If you need to rerun hello-world (or any
> step that has been run), you must remove the directory
> `./step-runner-working`. See [Troubleshooting](#troubleshooting).

To execute a different implementer for the hello-world step, replace *psr.yaml*:

```bash
cat > psr.yaml << EOF
hello-world:
  - implementer: LongGreeting
    name: Ryan
EOF
```

This will use the LongGreeting implementer instead of ShortGreeting. Re-run PSR
and validate the output.

It is useful to prototype against a real code base when developing an
implementer. [spring-petclinic](https://github.com/ploigos/spring-petclinic) is
a Java/Maven repo to test with. If you're testing another language or
framework, use an application written for that language.

> :notebook: If you're testing using a different repo, make sure to create a
psr.yaml file in that root of that repo for PSR configurations.

**Make sure to add tests for any new step implementers!**

Once the new step implementer is ready, [create a Pull
Request](https://github.com/ploigos/ploigos-step-runner/compare) to merge your
branch to the upstream project!

## Troubleshooting

> Fatal error calling step (generate-metadata): Can not add duplicate StepResult for step (generate-metadata), sub step (Maven), and environment (None)

This error (and similar duplicate step errors) occurs when a step that was previously run is re-run. PSR expects a given step and sub-step to run only once. In an actual pipeline, this indicates an error. When developing step implementers, it is common to trigger this error when re-running steps to test changes.

To fix this, remove the ./step-runner-working directory:

```bash
rm -r ./step-runner-working
```
