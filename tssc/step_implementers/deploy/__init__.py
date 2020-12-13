"""tssc.StepImplementers for the 'deploy' TSSC step.

Step Configuration
------------------
All tssc.StepImplementers for this step should
accept minimally the following configuration options.

| Parameter           | Description
|---------------------|------------
| `kube-api-uri`      | k8s API endpoint
| `git-email`         | Git email for commit
| `git-name` | Git name for commit
| `git-username`      | If the config repo is accessed via http(s) this must be supplied
| `git-password`      | If the config repo is accessed via http(s) this must be supplied

Results
-------
All tssc.StepImplementers for this step should
minimally produce the following step results.

| Result Key            | Description
|-----------------------|------------
| `config-repo-git-tag` | The git tag applied to the configuration repo for deployment
| `deploy-endpoint-url` | The endpoint url for the deployed app
"""

from .argocd import ArgoCD

__all__ = [
    'argocd'
]
