"""`StepImplementer` for `schemathesis` print implementation.
 
Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
 
 * static configuration
 * runtime configuration
 * previous step results
 
Configuration Key     | Required? | Default | Description
----------------------|-----------|---------|-----------
`name`                | Yes       | `World` | Name to receive the greeting
 
Result Artifacts
----------------
Results artifacts output by this step.
 
Result Artifact Key | Description
--------------------|------------
`message` | The complete message that was printed
"""
import os
import sys
import sh 
from ploigos_step_runner import StepImplementer, StepResult
 
DEFAULT_CONFIG = {
   'name': 'World'
}
 
REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
   'name'
]
 
 
class Schemathesis(StepImplementer):  # pylint: disable=too-few-public-methods
   """
   StepImplementer for the generate-metadata step for Git.
   """
 
   @staticmethod
   def step_implementer_config_defaults():
       """Getter for the StepImplementer's configuration defaults.
 
       Returns
       -------
       dict
           Default values to use for step configuration values.
 
       Notes
       -----
       These are the lowest precedence configuration values.
 
       """
       return DEFAULT_CONFIG
 
   @staticmethod
   def _required_config_or_result_keys():
       """Getter for step configuration or previous step result artifacts that are required before
       running this step.
 
       See Also
       --------
       _validate_required_config_or_previous_step_result_artifact_keys
 
       Returns
       -------
       array_list
           Array of configuration keys or previous step result artifacts
           that are required before running the step.
       """
       return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS
 
   def _run_step(self):
       """Runs the step implemented by this StepImplementer.
 
       Returns
       -------
       StepResult
           Object containing the dictionary results of this step.
       """
       step_result = StepResult.from_step_implementer(self)
 
       name = self.get_value('name')
       message = f'Schemathesis Hello {name}!'
 
       print(message)
#       auth_header = self.get_value('auth_header')

       schemathesis_success = False
       api_endpoint = self.get_value('deployed-host-urls')[0]
       print(api_endpoint)

## This could be moved to a generic auth runner      
       if self.get_value('auth_username'):
           auth_username = self.get_value('auth_username')
           auth_password = self.get_value('auth_password')
           auth_url = self.get_value('auth_url')
           auth_client_id = self.get_value('auth_client_id')
           auth_client_secret = self.get_value('auth_client_secret')
           auth_token = sh.jq(sh.curl(i
              '-sX','POST',
              f'{auth_url}',
              f"--header", 'Content-Type: application/x-www-form-urlencoded',
              f"--data-urlencode", 'grant_type=password',
              f"--data-urlencode", f'client_id={auth_client_id}',
              f"--data-urlencode", f'client_secret={auth_client_secret}',
              f"--data-urlencode", f'username={auth_username}',
              f"--data-urlencode", f'password={auth_password}'),
              f'-r',
              f'.access_token').strip()
           auth_header = f'Authorization: Bearer {auth_token}'

       try:
           working_directory = self.work_dir_path

           if auth_header:
               print(f'header:{auth_header}')
               scan_res = sh.schemathesis(
                   "run", "--stateful=links", "--checks", "all", f"{api_endpoint}/api/v1/api-docs?group=local",
                   "-H", 
                   f'{auth_header}',
                   "--junit-xml", f'{working_directory}/report-task.xml',
                   "--store-network-log",f'{working_directory}/schema-req-log.txt',
                   _out=sys.stdout,
                   _err=sys.stderr)
           else:
               scan_res = sh.schemathesis(
                   "run", "--stateful=links", "--checks", "all", f"{api_endpoint}/api/v1/api-docs?group=local",
                   "--junit-xml", f'{working_directory}/report-task.xml',
                   "--store-network-log",f'{working_directory}/schema-req-log.txt',
                   _out=sys.stdout,
                   _err=sys.stderr)

           schemathesis_success = True
       except sh.ErrorReturnCode as error: 
           # Error Code Other: unexpected
           step_result.success = False
           step_result.message = "Unexpected error running schemathesis analysis" \
               f" using schemathesis: {error}"

 
       step_result.add_artifact(
           name='schemathesis-result-set',
           value=f'{working_directory}/report-task.xml'
       )

       step_result.add_evidence(
           name='schemathesis-quality-gate-pass',
           value=schemathesis_success
       )

       step_result.add_evidence(
           name='schemathesis-request-responses',
           value=f'{working_directory}/schema-req-log.txt'
       )
 
       return step_result
 
