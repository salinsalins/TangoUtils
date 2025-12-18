import os, sys

def append_utils_folder_to_path(path='TangoUtils'):
    real = os.path.realpath('../' + path)
    if not os.path.exists(real):
        raise ImportError('Can not find %s folder' % path)
    if real not in sys.path:
        sys.path.append(real)

append_utils_folder_to_path('TangoUtils')
append_utils_folder_to_path('IT6900')