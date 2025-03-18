import os

from log_exception import log_exception


def import_modules_from_folder(folder_name="Devices"):
    #folder_name = 'Devices'
    for filename in os.listdir(folder_name):
        # Process all python files in a directory that don't start
        # with underscore (which also prevents this module from
        # importing itself).
        if filename.startswith('_'):
            continue
        fns = filename.split('.')
        if fns[-1] in ('py', 'pyw'):
            module_name = fns[0]
            try:
                exec(f'from {folder_name}.{module_name} import {module_name} as {module_name}')
            except:
                log_exception(f'Error during import from {folder_name}.{module_name}')
    del fns, filename, module_name, folder_name
