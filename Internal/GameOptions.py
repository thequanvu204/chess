import inspect
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QGroupBox, QCheckBox, QVBoxLayout, QRadioButton, QComboBox, QDialog, \
                            QHBoxLayout, QLabel, QLineEdit, QMessageBox

from Internal.Util import getInspectMembers, fillGroupBox
import Internal.Client as Client


options = []
checker = None


def empty():
    return len(options) == 0


class Option:
    def __init__(self):
        self.value = None


def add(argTuple):
    option = Option()
    args = [option, argTuple[0]]
    f = inspect.stack()[1]
    [code, ann] = getInspectMembers(f.frame.f_globals[f.function], ['__code__', '__annotations__'])
    for i, varName in enumerate(code.co_varnames):
        arg = argTuple[i+1]
        argType = type(arg)
        errorStart = lambda: 'The parameter "{}" of function "{}" must '.format(varName, f.function)
        if type(arg) == tuple:
            if not hasattr(arg[0], '__iter__'):
                raise Exception(errorStart() + 'be a list but it has type <{}>'.format(type(arg[0]).__name__))
            arglist = list(arg[0])
            for j, x in enumerate(arglist):
                xtype = type(x)
                if type(x) != arg[1]:
                    raise Exception((errorStart() + 'contain only elements of type <{}> but element {} has type <{}>!').
                                    format(arg[1].__name__, j, xtype.__name__))
            args.append(arglist)
        else:
            varType = ann.get(varName)
            if varType is not None:
                if varType != argType:
                    raise Exception(errorStart() + 'have type <{}> but it is <{}>'.
                                    format(varType.__name__, argType.__name__))
            args.append(arg)
    options.append(args)
    return option


def checkOptions():
    global checker
    if checker is not None:
        error = checker()
        if type(error) == str and len(error) > 0:
            QMessageBox.critical(Client.mainWidget, 'Invalid Options', error)
            return False
        checker = None
    return True


def setChecker(optionsChecker):
    global checker
    if optionsChecker is not None:
        if not callable(optionsChecker):
            raise Exception('Options checker must be callable')
        try:
            if len(inspect.getcallargs(optionsChecker)) > 0:
                raise TypeError()
        except TypeError:
            raise Exception('Options checker must not expect parameters')
    checker = optionsChecker


class Widget(QWidget):

    class ValueSetter:
        def __init__(self, obj):
            self.obj = obj

        def __call__(self, value):
            self.obj.value = value

    def __init__(self):
        global options
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        for option in options:
            [obj, optionType] = option[:2]
            handleValueChanged = self.ValueSetter(obj)
            if optionType == 'checkBox':
                [text, defaultValue] = option[2:]
                checkBox = QCheckBox(text)
                layout.addWidget(checkBox)
                checkBox.toggled.connect(handleValueChanged)
                checkBox.setChecked(defaultValue)
            elif optionType == 'radioButtons':
                [values, text] = option[2:]
                groupBox = QGroupBox(text)
                layout.addWidget(groupBox)
                groupBox.setLayout(QVBoxLayout())
                for i, value in enumerate(values):
                    radioButton = QRadioButton(value)
                    groupBox.layout().addWidget(radioButton)
                    def handleToggled(toggled, capturedObj=obj, capturedValue=value):
                        if toggled:
                            capturedObj.value = capturedValue
                    radioButton.toggled.connect(handleToggled)
                    radioButton.setChecked(i == 0)
            elif optionType == 'dropDownBox':
                [values] = option[2:]
                comboBox = QComboBox()
                layout.addWidget(comboBox)
                layout.addWidget(comboBox)
                comboBox.addItems(values)
                comboBox.currentTextChanged.connect(handleValueChanged)
                obj.value = comboBox.itemText(0)
            elif optionType == 'lineEdit':
                [text, defaultContent] = option[2:]
                lineEdit = QLineEdit()
                if text == '':
                    layout.addWidget(lineEdit)
                else:
                    self.addHorizontalWrapperWidget([QLabel(text), lineEdit])
                lineEdit.setText(defaultContent)
                lineEdit.textChanged.connect(handleValueChanged)
                obj.value = defaultContent
        options = []

    def addHorizontalWrapperWidget(self, childWidgets=[]):
        widget = QWidget()
        self.layout().addWidget(widget)
        widget.setLayout(QHBoxLayout())
        widget.layout().setContentsMargins(0, 0, 0, 0)
        for w in childWidgets:
            widget.layout().addWidget(w)


def showDialog(title, text):
    global options
    if len(options) == 0:
        raise Exception('There are no options - you can only show a options dialog after options have been added.')
    dialog = QDialog(Client.mainWidget)
    uic.loadUi('Internal/FormOptionsDialog.ui', dialog)
    dialog.setWindowTitle(title)
    dialog.label.setText(text)
    if text == '':
        dialog.label.hide()
    fillGroupBox(dialog.groupBox, Widget())
    def handleAccepted():
        if checkOptions():
            dialog.accept()
    dialog.buttonBox.accepted.connect(handleAccepted)
    dialog.exec()
