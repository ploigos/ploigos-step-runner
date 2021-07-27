"""
Creates a generic npm package.json file
"""

import sh
import os
# from ploigos_step_runner.step_implementer import StepImplementer


def generate_package_json(working_dir, author, author_email, license):
    print(isinstance(working_dir, str))
    try:
        os.chdir(working_dir)
        # set initial values for package.json and create file
        sh.npm("set", "init.author.name", author)
        sh.npm("set", "init.author.email", author_email)
        sh.npm("set", "init.license", license)
        sh.npm("init", "--yes")
    except:
        Exception
    package_json_path = working_dir + '/package.json'
    with open(package_json_path, 'r') as file:
        print(file)

    return package_json_path
