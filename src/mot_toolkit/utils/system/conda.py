import os


def get_conda_env_name() -> str:
    # Get "CONDA_DEFAULT_ENV"
    conda_default_env = os.environ.get("CONDA_DEFAULT_ENV")

    if conda_default_env is None:
        return ""

    return conda_default_env


if __name__ == '__main__':
    print(get_conda_env_name())
