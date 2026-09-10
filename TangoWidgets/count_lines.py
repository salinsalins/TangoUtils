import sys
import os


def count_newlines(fname):
    def _make_gen(reader):
        while True:
            b = reader(2 ** 16)
            if not b: break
            yield b

    with open(fname, "rb") as f:
        count = sum(buf.count(b"\n") for buf in _make_gen(f.raw.read))
    return count


def count_lines_in_list(file_list):
    total = 0
    for f in file_list:
        # fn = os.path.join(folder, f)
        count = count_newlines(f)
        print('     file: ', f, ' lines:  ', count)
        total += count
    return total


def count_lines_in_folder(folder):
    print('folder:    ', folder)
    all_files = os.listdir(folder)
    filtered_files = [os.path.join(folder, f) for f in all_files if f.endswith('.py')]
    total = count_lines_in_list(filtered_files)
    print('total files: ', len(filtered_files), 'lines: ', total)
    return total


def count_lines_in_subfolders(folder):
    total = 0
    all_files = os.listdir(folder)
    filtered_dirs = [os.path.join(folder, f) for f in all_files
                     if not f.startswith('.') and f != '__pycache__' and
                     os.path.isdir(os.path.join(folder, f))]
    if len(filtered_dirs) == 0:
        total += count_lines_in_folder(folder)
        return total
    for f in filtered_dirs:
        total += count_lines_in_subfolders(f)
    return total


folder = r"d:\Your files\Sanin\Documents\PyCharm Projects"
print('Counting total lines in python file in all subfolder of ', folder)
print('Grand total: ', count_lines_in_subfolders(folder))