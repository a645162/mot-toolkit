import os

os.system("flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics")
# os.system("flake8 . --ignore=E501,E203,W503,W504,W605,W291")
