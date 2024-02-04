from pathlib import Path
from pathvalidate import sanitize_filename
import traceback
from pytube.exceptions import PytubeError


class AgeRestrictionError(PytubeError):
    def __init__(self, message):
        super().__init__(message)
        pass


class UnavailableError(PytubeError):
    def __init__(self, message):
        super().__init__(message)
        pass

def dump(obj, i=1):
    s = "-" * i
    i = i + 1
    for attr in dir(obj):
        print(f"{s} obj.%s = %r" % (attr, getattr(obj, attr)))
        # print(type(obj), type(object))
        if type(obj) is object:
            dump(obj, i)


def slugify(str):
    return sanitize_filename(str)


def is_valid_path(path, is_dir=False):
    if path:
        if is_dir and Path(path).is_dir():
            return True
        elif path and Path(path).is_file():
            return True
    return False


def show_error(e):
    # traceback.print_exc()
    file = traceback.extract_tb(e.__traceback__)[-1].filename
    line_number = traceback.extract_tb(e.__traceback__)[-1].lineno
    code = traceback.extract_tb(e.__traceback__)[-1].line
    col_no = traceback.extract_tb(e.__traceback__)[-1].colno
    func = traceback.extract_tb(e.__traceback__)[-1].name
    print(f"Exception occurred on {file}:{line_number}")
    print(f"Col Number: {col_no}")
    print(f"Code: {code}")
    print(f"Function: {func}")
    print(e)
    # dump(traceback.extract_tb(e.__traceback__)[-1])

#
# def cli_progress_bar(progress=0, total=100):
#     percent = 100 * (progress / float(total))
#     bar = '-' * int(percent) + '-' * (100 - int(percent))
#     print(f"\r{bar}| {percent:2f}%", end="\r")
