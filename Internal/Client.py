# common data for client

mainWidget = None
gameObject = None
connector = None
serverSettings = None

def setMainWidget(widget):
    global mainWidget
    if mainWidget is not None:
        mainWidget.deleteLater()
    mainWidget = widget

