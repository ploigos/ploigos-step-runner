"""A mixin class designed to add shared functionality to StepImplementers that interact with Git.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key    | Required? | Default              | Description
---------------------|-----------|----------------------|-----------
`git-repo-root`      | Yes       | `./`                 | Directory path to the Git repository to perform git operations on.
`repo-root`          | No        |                      | Alias for `git-repo-root`.
`git-url`            | No        | Git repo root configured origin url \
                                                        | URL to Git repository to perform Git operations on. \
                                                          If not given will use Git remote url set in given Git repository root.
`url`                | No        |                      | Alias for `git-url`.
`git-username`       | No        |                      | Git username to use when connecting with Git remote. \
                                                          Will override username in given git url. \
                                                          Will override username in Git url in Git repository root remote url. \
                                                          Will be ignored if Git repository url is using SSH.
`git-password`       | No        |                      | Git password to use when connecting with Git remote. \
                                                          Will override password in given git url. \
                                                          Will override password in Git url in Git repository root remote url. \
                                                          Will be ignored if Git repository url is using SSH.
`git-user-name`      | Maybe     | `Ploigos Robot`      | User name to use when creating Git commits.
`git-user-email`     | Maybe     | `ploigos-robot`      | User email to use when creating Git commits.
`git-commit-message` | Maybe     | `Automated commit of changes during release engineering generate-metadata step` \
                                                        | Git commit message to use when/if creating an automated git commit.
"""# pylint: disable=line-too-long

from urllib.parse import urlsplit, urlunsplit

from git import InvalidGitRepositoryError, Repo
from git.exc import GitCommandError
from ploigos_step_runner import StepRunnerException

DEFAULT_CONFIG = {
    'git-repo-root': './',
    'git-commit-message': 'Automated commit of changes during release engineering' \
        ' generate-metadata step',
    'git-user-name': 'Ploigos Robot',
    'git-user-email': 'ploigos-robot'
}
REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    ['git-repo-root', 'repo-root']
]

class GitMixin:
    """A mixin class designed to add shared functionality
    to StepImplementers that interact with Git.
    """
    def __init__(self):
        self.__git_repo = None
        self.__git_url = None

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

    @property
    def git_repo(self):
        """Get the Git repository.

        Returns
        -------
        Repo
            Git repository object for the given git repository root.

        Raises
        ------
        StepRunnerException
            If given git repo root is not a Git repository.
        """
        if not self.__git_repo:
            repo_root = self.get_value(['git-repo-root', 'repo-root'])
            try:
                self.__git_repo = Repo(repo_root)
            except InvalidGitRepositoryError as error:
                raise StepRunnerException(
                    f'Given git-repo-root ({repo_root}) is not a Git repository: {error}'
                ) from error

        return self.__git_repo

    @property
    def git_url(self): # pylint: disable=too-many-branches
        """Get the Git url including auth if given.

        This function tries to be smart and combine given username/password into given URL
        and/or with username/password/url determined from Git repository remote configuration.

        Raises
        ------
        StepRunnerException
            If Git username given but Git url uses SSH
            If Git password given but Git url uses SSH
        """
        if not self.__git_url:
            # get git url from config or current repo remote
            git_url = self.get_value(['git-url', 'url'])
            if not git_url:
                git_url = self.git_repo.remote().url

            # if git url is ssh, throw error if git username or password given
            # if git url is http|https combine git username and password with git url
            split_git_url = urlsplit(git_url)
            if split_git_url.scheme in ['ssh']:
                self.__git_url = git_url
            elif split_git_url.scheme in ['http', 'https']:
                # get given git username and pass
                git_username = self.get_value('git-username')
                git_password = self.get_value('git-password')

                # determine git username
                if split_git_url.username and git_username:
                    print(
                        f"WARNING: Git url ({git_url}) includes username ({split_git_url.username})"
                        f" but was given Git username ({git_username})."
                        f" Will use given Git username ({git_username})."
                    )
                elif split_git_url.username:
                    git_username = split_git_url.username

                # determine git password
                if split_git_url.password and git_password:
                    print(
                        f"WARNING: Git url ({git_url}) includes password ({split_git_url.password})"
                        f" but was given Git password ({git_password})."
                        f" Will use given Git password ({git_password})."
                    )
                elif split_git_url.password:
                    git_password = split_git_url.password

                # construct new git url with auth
                git_netloc = None
                if git_username and git_password:
                    git_netloc = f"{git_username}:{git_password}@{split_git_url.hostname}"
                elif git_username:
                    git_netloc = f"{git_username}@{split_git_url.hostname}"
                else:
                    git_netloc = split_git_url.hostname

                if split_git_url.port:
                    git_netloc += f":{split_git_url.port}"

                self.__git_url = urlunsplit((
                    split_git_url.scheme,
                    git_netloc,
                    split_git_url.path,
                    split_git_url.query,
                    split_git_url.fragment
                ))

        return self.__git_url

    def configure_git_user(self):
        """Configures the git user.

        Raises
        ------
        StepRunnerException
            If given git repo root is not a Git repository.
        """
        repo = self.git_repo
        repo.config_writer().set_value(
            "user",
            "name",
            self.get_value('git-user-name')
        ).release()
        repo.config_writer().set_value(
            "user",
            "email",
            self.get_value('git-user-email')
        ).release()

    def git_commit_changes(self):
        """Stages and commits any and all unstaged changes in the Git repository.

        Raises
        ------
        StepRunnerException
            If given git repo root is not a Git repository.
            If error commiting changes to current branch.
        """
        repo = self.git_repo
        try:
            repo.git.commit('-am', self.get_value('git-commit-message'))
        except (GitCommandError, Exception) as error:
            raise StepRunnerException(
                f"Error committing changes to current branch ({repo.active_branch.name})"
                f": {error}"
            ) from error

    def git_push(self):
        """Push all committed Git changes.

        Raises
        ------
        StepRunnerException
            If given git repo root is not a Git repository.
            If error pushing changes to remote.
        """
        repo = self.git_repo
        url = self.git_url

        try:
            # NOTE:
            #   using repo.git.push rather then repo.remote().push() because need to be
            #   able to override the git url for the push
            repo.git.push(url)
        except (GitCommandError, Exception) as error:
            raise StepRunnerException(
                f"Error pushing changes to remote ({url})"
                f" on current branch ({repo.active_branch.name}): {error}"
            ) from error

    def git_push_tags(self):
        """Push Git tags.

        Raises
        ------
        StepRunnerException
            If given git repo root is not a Git repository.
            If error pushing tags to remote.
        """
        repo = self.git_repo
        url = self.git_url

        try:
            # NOTE:
            #   using repo.git.push rather then repo.remote().push() because need to be
            #   able to override the git url for the push
            repo.git.push(url, '--tag')
        except (GitCommandError, Exception) as error:
            raise StepRunnerException(
                f"Error pushing tags to remote ({url})"
                f" on current branch ({repo.active_branch.name}): {error}"
            ) from error

    def commit_changes_and_push(self):
        """Commits all changes in the given repo and pushes them to the current remote on the
        current branch. If no changes to commit this is a no-op.

        Parameters
        ----------
        repo : git.Repo
            Repo to commit and push changes to.

        Raises
        ------
        StepRunnerException
            If given git repo root is not a Git repository.
            If error commiting changes to current branch.
            If error pushing changes to remote.

        """
        repo = self.git_repo
        print(
            f"Commit all changes and push to current remote ({repo.remote().url})" \
            f" on current branch ({repo.active_branch.name})"
        )

        if repo.is_dirty():
            # configure git user
            self.configure_git_user()

            # commit changes
            self.git_commit_changes()

            # push changes
            self.git_push()
        else:
            print("No changes to commit and push")


    def git_tag(self, git_tag_value):
        """Create a git tag.

        Parameters
        ----------
        git_tag_value : str
            Value to tag Git repository with.

        Raises
        ------
        StepRunnerException
            If given git repo root is not a Git repository.
            If error creating Git tag.
        """
        try:
            # NOTE:
            #   this force is only needed locally in case of a re-run of the same pipeline
            #   without a fresh check out. You will notice there is no force on the push
            #   making this an acceptable work around to the issue since on the off chance
            #   actually overwriting a tag with a different comment, the push will fail
            #   because the tag will be attached to a different git hash.
            self.git_repo.create_tag(git_tag_value, force=True)
        except (GitCommandError, Exception) as error:
            raise StepRunnerException(
                f"Error creating git tag ({git_tag_value}): {error}"
            ) from error
