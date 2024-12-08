# https://raw.githubusercontent.com/mikel-brostrom/boxmot/refs/heads/master/tracking/utils.py

from enum import Enum

from git import Repo, exc

from mot_toolkit.utils.logs import get_logger

logger = get_logger()
LOGGER = logger


class TrackEvalRepo(Enum):
    TrackEval = "https://github.com/JonathonLuiten/TrackEval"
    GallioPRO = "https://github.com/GallioPRO/TrackEval"
    KHM = "https://github.com/a645162/TrackEvalNew"

    def __str__(self):
        return self.value


use_repo: TrackEvalRepo = TrackEvalRepo.KHM

track_eval_repo_url = use_repo.value
track_eval_repo_url = str(track_eval_repo_url)


def download_mot_eval_tools(val_tools_path):
    """
    Download the official evaluation tools for MOT metrics from the GitHub repository.

    Parameters:
        val_tools_path (Path): Path to the destination folder where the evaluation tools will be downloaded.

    Returns:
        None. Clones the evaluation tools repository and updates deprecated numpy types.
    """
    val_tools_url = track_eval_repo_url

    try:
        # Clone the repository
        Repo.clone_from(val_tools_url, val_tools_path)
        LOGGER.info('Official MOT evaluation repo downloaded successfully.')
    except exc.GitError as err:
        LOGGER.info(f'Evaluation repo already downloaded or an error occurred: {err}')

    # Fix deprecated np.float, np.int & np.bool by replacing them with native Python types
    deprecated_types = {'np.float': 'float', 'np.int': 'int', 'np.bool': 'bool'}

    for file_path in val_tools_path.rglob('*'):
        if file_path.suffix in {'.py', '.txt'}:  # only consider .py and .txt files
            try:
                content = file_path.read_text(encoding='utf-8')
                updated_content = content
                for old_type, new_type in deprecated_types.items():
                    updated_content = updated_content.replace(old_type, new_type)

                if updated_content != content:  # Only write back if there were changes
                    file_path.write_text(updated_content, encoding='utf-8')
                    LOGGER.info(f'Replaced deprecated types in {file_path}.')
            except Exception as e:
                LOGGER.error(f'Error processing {file_path}: {e}')
