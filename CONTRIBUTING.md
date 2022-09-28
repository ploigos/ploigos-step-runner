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

You will need to run `source .venvs/psr-dev/bin/activate` to activate the
development environment each time you start working in a new terminal session.

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
implementer. The "example" step and it's implementers were created as examples
for developers to copy and create their own implementers.

The source code for step implementers is under
`./src/ploigos_step_runner/step_implementers/`. Each sub-directory represents a different step.
Each python files under a sub-directory is a step implementer for that step.
For example, `./src/ploigos_step_runner/step_implementers/unit-test/npm_test.py` is a step implementer
for the unit-test step that knows how to use the npm command to run unit tests.

Step implementers under the `./src/ploigos_step_runner/step_implementers/examples/` directory
are associated with the special "examples" step, which is not part of any workflow but is used
to organize and run example code. You can copy these examples as the basis for your own
step implementers.


**To add a new step implementer:**

1. Find example code you want to start with. `hello_shell.py` in the `examples` directory is a good
starting point if your step implementer will run an external command. You could also copy a real
step implementer as a starting point or start from scratch.

2. Copy the example into a new python file under the appropriate sub directory. For example, if you
are writing a step implementer for the package step that will compile intercal code, you should put it
under the `package` directory and name it something like `intercal_package.py`.

3. Create a file for your unit tests. You can copy the unit tests for the example. Put it in the
appropriate sub directory of `./tests/`. The directory structure matches `./src/`. Start the file name
with 'test_', for example 'test_intercal_package.py`. If you like Test Driven Development, you can copy
the structure of the test file and delete all the of old tests, writing new ones as you code.

4. Modify the python code to implement the logic of your step. Continuing the intercal example, you
would have to change the example code that runs the "echo" shell command and make it run the intercal
compiler instead. 

5. Be sure to run the unit tests and linter. **PRs are not merged until the unit tests and lint checks pass
and unit test coverage is 100%**. If you are having trouble writing the unit tests, feel free to open a
draft PR and ask for help!

6. During development, it is often useful to test the step by running the psr command directly. This saves
time because you do not have to run a full pipeline to see if your python code behaves as expected outside
of the unit tests. The next section explains how to do that.

7. Once the new step implementer is ready, [create a Pull Request](https://github.com/ploigos/ploigos-step-runner/compare)
to contribute your code to the upstream project!


## Testing a Step Implementer by Running the psr Command

To run the HelloShell example step implementer:

1. Create a *psr.yaml* file:
```bash
cat > psr.yaml << EOF
step-runner-config:

  examples:
    - implementer: HelloShell
      config:
        greeting-name: Folks
EOF
```

2. Run PSR:
The "examples" step is a special step used to execute example StepImplementers. It takes the place
of a real step like "unit-test" or "create-container-image".
```bash
psr -s examples -c psr.yaml
```

3. Validate the output, both stdout and artifacts sections.

4. Delete the PSR working directory:

```bash
rm -r ./step-runner-working
```

> :warning: This step is important. If you need to re-run hello-world (or any
> step that has been run), you must remove the directory
> `./step-runner-working`. See [Troubleshooting](#troubleshooting).

5. To execute a different implementer for the examples step, replace *psr.yaml*:
```bash
cat > psr.yaml << EOF
step-runner-config:

  examples:
    - implementer: HelloWorld
      config:
        greeting-name: Folks
EOF
```

This will use the simpler HelloWorld implementer instead of HelloShell. Re-run PSR
and validate the output.


## Sample Applications

When developing a step implementer, it is often useful to have a real application
that you can run the psr against. We maintain several specifically for that purpose:
* [spring-petclinic](https://github.com/ploigos/spring-petclinic/) is a Java application that uses Maven.
* [reference-nodejs-npm](https://github.com/ploigos-reference-apps/reference-nodejs-npm) is a NodeJS application that uses NPM.
* [dotnet-app](https://github.com/ploigos/dotnet-app/) is a .NET application.

If you are testing another language or framework, use an application written for that language.

> :notebook: If you're testing using a different repo, make sure to create a
psr.yaml file in that root of that repo for PSR configurations.

## Troubleshooting

> Fatal error calling step (generate-metadata): Can not add duplicate StepResult for step (generate-metadata), sub step (Maven), and environment (None)

This error (and similar duplicate step errors) occurs when a step that was previously run is re-run. PSR expects a given step and sub-step to run only once. In an actual pipeline, this indicates an error. When developing step implementers, it is common to trigger this error when re-running steps to test changes.

To fix this, remove the ./step-runner-working directory:

```bash
rm -r ./step-runner-working
```

