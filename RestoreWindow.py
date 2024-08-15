from qtpy import QtGui
from qtpy.QtCore import QSize, QPoint
from qtpy.QtWidgets import QMainWindow


def restore_window(window: QMainWindow, conf: dict = None):
    window.setMinimumSize(600, 400)
    window.move(QPoint(20, 20))
    if conf is None:
        conf = window.conf
    if 'main_window' in conf:
        window.resize(QSize(conf['main_window']['size'][0], conf['main_window']['size'][1]))
        x = conf['main_window']['position'][0]
        y = conf['main_window']['position'][1]
        scns = QtGui.QGuiApplication.screens()
        for scn in scns:
            sg = scn.geometry()
            if sg.left() < x < sg.left() + sg.width():
                if sg.top() < y < sg.top() + sg.height():
                    window.move(QPoint(x, y))
                    return

# def restore_settings(window, folder='', file_name=None):
#     window.conf = {
#         'columns': 3,
#         'w_height': 300,
#         'w_width': 300
#     }
#     global CONFIG_FILE
#     if file_name is None:
#         file_name = CONFIG_FILE
#     full_name = os.path.abspath(os.path.join(str(folder), file_name))
#     try:
#         with open(full_name, 'r') as configfile:
#             s = configfile.read()
#         window.conf.update(json.loads(s))
#         global CONFIG
#         CONFIG = window.conf
#         # Log level restore
#         if 'log_level' in window.conf:
#             v = window.conf['log_level']
#             window.logger.setLevel(v)
#             levels = [logging.NOTSET, logging.DEBUG, logging.INFO,
#                       logging.WARNING, logging.ERROR, logging.CRITICAL]
#             mm = 0
#             for m in range(len(levels)):
#                 if v <= levels[m]:
#                     mm = m
#                     break
#             window.log_level.setCurrentIndex(mm)
#         # Restore window size and position
#         window.restore_window_position()
#         # colors
#         if 'colors' in window.conf:
#             window.trace_color = window.conf['colors'].get('trace', window.trace_color)
#             window.previous_color = window.conf['colors'].get('previous', window.previous_color)
#             window.mark_color = window.conf['colors'].get('mark', window.mark_color)
#             window.zero_color = window.conf['colors'].get('zero', window.zero_color)
#         # Last folder
#         if 'folder' in window.conf:
#             window.log_file_name = window.conf['folder']
#         if 'included' in window.conf:
#             window.shown_columns.setPlainText(window.conf['included'])
#         if 'excluded' in window.conf:
#             window.hidden_columns.setPlainText(window.conf['excluded'])
#         if 'extra_plot' in window.conf:
#             window.plainTextEdit_4.setPlainText(window.conf['extra_plot'])
#         if 'extra_col' in window.conf:
#             window.plainTextEdit_5.setPlainText(window.conf['extra_col'])
#         if 'exclude_plots' in window.conf and hasattr(window, 'plainTextEdit_6'):
#             window.hidden_plots.setPlainText(window.conf['exclude_plots'])
#         if 'plot_order' in window.conf and hasattr(window, 'plainTextEdit_7'):
#             window.shown_plots.setPlainText(window.conf['plot_order'])
#         if 'cb_1' in window.conf:
#             window.checkBox_1.setChecked(window.conf['cb_1'])
#         if 'cb_2' in window.conf:
#             window.checkBox_2.setChecked(window.conf['cb_2'])
#         if 'cb_3' in window.conf:
#             window.checkBox_3.setChecked(window.conf['cb_3'])
#         if 'cb_4' in window.conf:
#             window.checkBox_4.setChecked(window.conf['cb_4'])
#         if 'cb_5' in window.conf:
#             window.checkBox_5.setChecked(window.conf['cb_5'])
#         if 'cb_6' in window.conf:
#             window.checkBox_6.setChecked(window.conf['cb_6'])
#         if 'history' in window.conf:
#             window.history.currentIndexChanged.disconnect(window.file_selection_changed)
#             window.history.clear()
#             window.history.addItems(window.conf['history'])
#             window.history.currentIndexChanged.connect(window.file_selection_changed)
#         if 'history_index' in window.conf:
#             window.history.setCurrentIndex(window.conf['history_index'])
#         window.cut_long_names = window.conf.get('cut_long_names', True)
#         window.conf['cut_long_names'] = window.cut_long_names
#         window.fill_empty_lists = window.conf.get('fill_empty_lists', True)
#         window.conf['fill_empty_lists'] = window.fill_empty_lists
#         #
#         if 'right_mouse_button' in window.conf:
#             window.rmb = window.conf['right_mouse_button']
#         #
#         window.logger.debug('Configuration restored from %s' % full_name)
#         return True
#     except:
#         log_exception('Configuration restore error from %s' % full_name)
#         return False
