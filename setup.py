import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tssc",
    author="Red Hat Services",
    description="Trusted Software Supply Chain (TSSC) python library.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rhtconsulting/tssc-python-package",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    use_scm_version=True,
    setup_requires=['setuptools_scm']
)
