"""
Creates a generic npm package.json file
"""

import sh
import os
from ploigos_step_runner.step_implementer import StepImplementer


def generate_package_json(working_dir):
    try:
        os.chdir(working_dir)
        sh.npm("init", "--yes")
    except:
        Exception
    package_json_path = working_dir + '/package.json'
    with open(package_json_path, 'r') as file:
        print(file)

