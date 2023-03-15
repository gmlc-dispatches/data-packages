import sys


def main(args=None):
    from dispatches_data.api import path

    args = args or sys.argv[1:]

    if args:
        pkg_name = args[0]
        path_to_print = path(pkg_name)
    else:
        pkg_name = "_for_api_testing"
        path_to_print = path(pkg_name).parent

    print(str(path_to_print))
