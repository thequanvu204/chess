import getpass, os, json
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

import Internal.Client as Client
from Internal.Server import sessionServer as defaultAddress


settingsFile = 'settings.json'


def loadSettings():
    if os.path.isfile(settingsFile):
        with open(settingsFile) as f:
            try:
                return json.load(f)
            except Exception as e:
                raise Exception(f'Settings file {os.path.realpath(settingsFile)} has an invalid syntax:\n{e}')
    return {}


def updateSettings(changedSettings):
    settings = loadSettings()
    settings.update(changedSettings)
    with open(settingsFile, 'w') as f:
        json.dump(settings, f, indent=4)


class ServerSettings:
    def __init__(self, address=None, name=None, secret=None, locked=False):
        self.address = address if address is not None else defaultAddress
        self.name    = name    if name    is not None else getpass.getuser()
        self.secret  = secret  if secret  is not None else ''
        self.locked = locked


class ServerSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('Internal/FormServerSettings.ui', self)
        if Client.serverSettings is None:
            Client.serverSettings = ServerSettings()
        self.lineEdit_address.setText(Client.serverSettings.address)
        self.lineEdit_name.setText(Client.serverSettings.name)
        self.lineEdit_secret.setText(Client.serverSettings.secret)
        self.setDisabled(Client.serverSettings.locked)

    def lock(self):
        settings = ServerSettings(
            address=self.lineEdit_address.text(),
            name=self.lineEdit_name.text(),
            secret=self.lineEdit_secret.text(),
            locked=not self.isEnabled()
        )
        changedSettings = {}
        if settings.address != Client.serverSettings.address:
            changedSettings['serverAddress'] = settings.address
        if settings.name != Client.serverSettings.name:
            changedSettings['hostingName'] = settings.name
        if settings.secret != Client.serverSettings.secret:
            changedSettings['sessionSecret'] = settings.secret
        if len(changedSettings) > 0:
            updateSettings(changedSettings)
        Client.serverSettings = settings
        self.setDisabled(True)

    def unlock(self):
        self.setDisabled(False)
