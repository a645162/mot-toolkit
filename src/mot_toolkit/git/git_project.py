import os

import git

enable_git = True


def check_is_git_project():
    """
    Check if the current directory is a git project.

    :return: True if the current directory is a git project, False otherwise.
    """
    try:
        git.Repo(os.getcwd())
        return True
    except git.exc.InvalidGitRepositoryError:
        return False


enable_git = enable_git and check_is_git_project()


def fetch_is_have_new_version():
    """
    Fetch the latest version of the project from the remote repository.

    :return: True if the project has a new version, False otherwise.
    """
    if enable_git:
        repo = git.Repo(os.getcwd())
        repo.remotes.origin.fetch()
        return repo.remotes.origin.compare(repo.head.ref).behind > 0
    else:
        return False


if __name__ == "__main__":
    print("enable_git", enable_git)
    print("fetch_is_have_new_version", fetch_is_have_new_version())
