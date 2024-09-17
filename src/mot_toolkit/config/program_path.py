import os

py_path = os.path.abspath(__file__)
path_base_package = \
    os.path.dirname(
        os.path.dirname(py_path)
    )
path_src = \
    os.path.dirname(path_base_package)
path_project = \
    os.path.dirname(path_src)

if __name__ == '__main__':
    print(py_path)
    print(path_base_package)
    print(path_src)
    print(path_project)
