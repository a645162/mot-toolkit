# read the contents of your README file
from pathlib import Path

from setuptools import setup, find_packages

from mot_toolkit import __version__

this_directory = Path(__file__).parent
base_dir = this_directory.parent
long_description = (base_dir / "README.md").read_text()

url_github_main_readme_zh_cn = (
    r"https://github.com/a645162/mot-toolkit/blob/main/README.zh-CN.md"
)
long_description = long_description.replace(
    "(README.zh-CN.md)", f"({url_github_main_readme_zh_cn})"
)

setup(
    name="mot-toolkit",
    version=__version__,
    description="MOT Toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/a645162/mot-toolkit",
    author="Haomin Kong",
    author_email="a645162@gmail.com",
    license="GPLv3",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "loguru",

        "pyside6",
        "opencv-python",
        "numpy<2",

        "chardet",

        "pygame",
    ],
    entry_points={
        "console_scripts": [
            "mot-toolkit = mot_toolkit.main_gui:main",
        ],
    },
)
