import inspect, sys
from bisect import bisect_right
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, \
                            QComboBox, QStyle, QHeaderView, QPushButton, QLabel, QGroupBox, QGridLayout, \
                            QCheckBox, QRadioButton


def getInspectMember(object, mem: str):
    for m in inspect.getmembers(object):
        if m[0] == mem:
            return m[1]
    else:
        return None

def getInspectMembers(object, mems: list):
    ret = [None] * len(mems)
    for m in inspect.getmembers(object):
        try:
            ret[mems.index(m[0])] = m[1]
        except ValueError:
            pass
    return ret


def makeToolButton(iconOrText):
    button = QToolButton()
    if type(iconOrText) == str:
        button.setText(iconOrText)
        button.setToolButtonStyle(Qt.ToolButtonTextOnly)
    else:
        button.setIcon(QApplication.instance().style().standardIcon(iconOrText))
        button.setToolButtonStyle(Qt.ToolButtonIconOnly)
    return button


def fillGroupBox(groupBox: QGroupBox, widget: QWidget):
    if groupBox.layout() is None:
        groupBox.setLayout(QVBoxLayout())
    groupBox.layout().addWidget(widget)


def makeTableWidgetItem(text, flags=Qt.ItemIsEnabled):
    item = QTableWidgetItem(text)
    item.setFlags(flags)
    return item


def getModuleAttrDict(module):
    return module if type(module) == dict else module.__dict__


def getModuleFilePath(module):
    return getModuleAttrDict(module)['__file__']


def getParam(paramkey, typ=str):
    paramkey += '='
    param = list(filter(lambda x: x.startswith(paramkey), sys.argv))
    if len(param) == 0:
        return None
    val = param[-1][len(paramkey):]
    try:
        return typ(val)
    except ValueError:
        raise Exception('"{}" for parameter {} could not be converted to typ "{}"'.format(val, paramkey, typ.__name__))


def parseArgs():
    args = dict()
    for arg in sys.argv[1:]:
        if arg.startswith('--'):
            arg = arg[2:]
            equalPos = arg.find('=')
            keyDash = arg if equalPos == -1 else arg[:equalPos]
            key = ''
            lastDash = False
            for c in keyDash:
                if c == '-':
                    lastDash = True
                else:
                    key += c.upper() if lastDash else c
                    lastDash = False
            if equalPos == -1:
                dict[key] = True
                continue
            value = arg[(equalPos + 1):]
            try:
                args[key] = int(value)
                continue
            except ValueError:
                pass
            unquote = lambda x: x[1:-1] if x.startswith('"') and x.endswith('"') else x
            value = unquote(value)
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.lower() == 'none':
                value = None
            else:
                parts = list(map(unquote, value.split(',')))
                args[key] = value if len(parts) == 1 else parts
    return args
