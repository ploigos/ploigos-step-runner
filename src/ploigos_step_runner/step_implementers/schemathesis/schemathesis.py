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

       schemathesis_success = False
       api_endpoint = self.get_value('deployed-host-urls')
       print(api_endpoint)
       auth_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJIM0M5WnhpVjN0QldBX1VnYzU1S3lmS1NUaGdwbzlaM2FoN0ZoQXFYT2VZIn0.eyJleHAiOjE2MzAwMDE2NjAsImlhdCI6MTYzMDAwMTM2MCwianRpIjoiZGUxYmI3NDktMWJjNi00MjY4LTgxOGUtOTU5NmE4YjUzNGQ0IiwiaXNzIjoiaHR0cHM6Ly9rZXljbG9hay1jb25zdWx0YW50MzYwLWRldi5hcHBzLnRzc2Mucmh0LXNldC5jb20vYXV0aC9yZWFsbXMvY29uc3VsdGFudDM2MCIsImF1ZCI6WyJiZWFyZXIiLCJhY2NvdW50Il0sInN1YiI6Ijk5ZDU4ODIzLTI5YjctNGIxZi1hYTU5LTc2MDRmMThlZmVmYiIsInR5cCI6IkJlYXJlciIsImF6cCI6ImNvbnN1bHRhbnQzNjAiLCJzZXNzaW9uX3N0YXRlIjoiMDY1YWEyYjQtZGYzMS00NTk0LWI4ZGEtYWM5OTlkYjAwYzhjIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjQxODAvKiIsImh0dHA6Ly9sb2NhbGhvc3Q6OTA4MC8qIiwiaHR0cHM6Ly9mZWVkYmFjazM2MC1jb25zdWx0YW50MzYwLWRldi5hcHBzLnRzc2Mucmh0LXNldC5jb20iLCJodHRwOi8va2V5Y2xvYWs6OTA4MC8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiY29uc3VsdGFudDM2MCI6eyJyb2xlcyI6WyJ1c2VyIl19LCJiZWFyZXIiOnsicm9sZXMiOlsidXNlciJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJQYW0gTWFuYWdlciIsInByZWZlcnJlZF91c2VybmFtZSI6InBybWFuYWdlciIsImdpdmVuX25hbWUiOiJQYW0iLCJmYW1pbHlfbmFtZSI6Ik1hbmFnZXIiLCJlbWFpbCI6InBybWFuYWdlckByZWRoYXQuY29tIn0.LNY3OJLTO-JLJN_7lW6vQo5x0AYtLBi1_Tq31Ki_n7hmKCMkfei0noLCev_DRcGt1ESjg5dCSrYn0kM9Cxn3Ck-CuRiJMdiN9u9iGMF9Uog_LnFVbMqLpiRiH22UJbgiM6nB1-sZiZdxbIZcBUlG0h6KxOZYoUtEXQmwXConUdjr-p4DhRcTZ7uk36QF8AFsjHUVdYDsbP0UzpMKzla7TIhqnesAqX6BeKv1mrxIgmDC71OYs2gzgE37O47Wh1idFDEH07W5jRjTIGTDmyMkY932M0YwdGtCycTz9HRtTiM5mI0Z6YSwUVw7V0UAxvlE3t5PQ7vs48Kpjp2ZTHfR4Q"

       try:
           sh.schemathesis(
               f'run',
               f'-stateful=links'
               f'--checks all', 
               f'{api_endpoint}/api/v1/api-docs?group=local', 
               f'-H "Authorization: Bearer {auth_token}"',
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
           value=f'{working_direictory}/report-task.txt'
       )

       step_result.add_evidence(
           name='schemathesis-quality-gate-pass',
           value=schemathesis_success
       )
 
       return step_result
 
