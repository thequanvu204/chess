import Internal.Main as Main

############ !!!!!!!!! DO NOT CHANGE THIS FILE !!!!!!!!! ############

# runs the game - must be called as last code line in your game because it will return after your game has finished
# options can also be set in a file settings.json in the working directory or by command line parameters,
# e.g. hostGame=True is --host-game=True or only --host-game because =True can be omitted.
# A list of strings is given by comma separation: --players=Alice,Bob
# If strings contain white space, they must be enclosed by double quotes!
# Priority of the 3 possibilities is:
# 1st: command line parameters
# 2nd: settings in settings.json in working directory
# 3rd: parameters of GamePlayer.run
# Options:
# gameName               : name for the game - if None, it is derived from the filename
# minPlayerCount         : minimum number of players
# maxPlayerCount         : maximum number of players
# players                : if a list with strings: use these player names in local mode
#                          (can be adapted in settings dialog)
#                          if an integer n: same as above and use "player 1", ..., "player n" as player names
#                          if None: same as above with n=minPlayerCount
# autoStart              : if True, start game with default options in local mode
# playerTitles           : list of strings for the player titles, e.g. in many cases like chess the player colors
#                          the length of the list must be maxPlayerCount
#                          if None, no titles will be shown in the GUI
# titlesAreChoosable     : if the titles can be chosen and are not bound to the order like for chess
#                          (white always begins)
# mouseMoveEventsEnabled : if True, makeMove will also be called with mouse move events
# hostGame               : if True, the game will be immediately hosted on the server
#                          if it is a number in [minPlayerCount, maxPlayerCount], automatically a server and
#                          number-1 clients will be started on this computer
#                          and join the session, names will be used according to players parameter
# hostingName            : the name for hosting if the game file is started directly
#                          if None the last used name or the login name is used
# sessionSecret          : a secret if the game is started directly and hosted on the server
#                          only players with the same session secret will see the session and can join
def run(gameName=None, minPlayerCount=2, maxPlayerCount=2, players=None, autoStart=False, playerTitles=None, \
        titlesAreChoosable=False, mouseMoveEventsEnabled=False, hostGame=False, hostingName=None, sessionSecret=None):
    Main.run(locals())

# get the number of players
def getPlayerCount():
    return Main.getGameObject().getPlayerCount()

# get a list of the player names
def getPlayerNames():
    return Main.getGameObject().players

# get a list of the player titles
# is actually the parameter of GamePlayer.run but maybe reordered and shortened to player count length - might be None!
def getPlayerTitles():
    return Main.getGameObject().playerTitles

# get the index of the currently moving player
def getCurrentPlayerIndex():
    return Main.getGameObject().currentPlayerIndex

# show info message by calling during the game (makeMove, playerLeftGame, paintGame)
# is shown after the calling function has returned and game has been painted again
# title is shown in the message box title bar
def showMessageLater(title, text):
    return Main.showMessageLater(title, text, showOnThisPC=True, sendToOthers=False)

# show info message for all players participating by calling during the game (makeMove, playerLeftGame, paintGame)
# is shown after the calling function has returned and game has been painted again
# title is shown in the message box title bar
# in local mode same as showMessageLater!
def showMessageLaterForAll(title, text):
    return Main.showMessageLater(title, text, showOnThisPC=True, sendToOthers=True)

# show info message for other players participating by calling during the game (makeMove, playerLeftGame, paintGame)
# is shown after the calling function has returned and game has been painted again
# title is shown in the message box title bar
# does nothing in local mode
def showMessageLaterForOthers(title, text):
    return Main.showMessageLater(title, text, showOnThisPC=False, sendToOthers=True)


##################### functions for querying options #####################


# The following functions can be called in two context in order to query options:
# - from global scope called before the game:
#     The option will appear in the dialog before the game
# - during the game called from makeMove:
#     After the functions have been called there can be a final call to showOptionsDialog which
#     will show a dialog contain the options

# The option functions always return an object with a value member.
# At first it is None and when the option dialog is open or finished, this member is set to the selected value.

# layout of return object for option functions
# class Option:
#     def __init__(self):
#         self.value = None

# adds a checkbox option - text will be shown next to the checkbox
# value will be True if checked and False otherwise
def addCheckBoxOption(text: str, defaultValue: bool = False):
    return Main.addOption(('checkBox', text, defaultValue))

# add several radio buttons - values must be a list of strings which will be shown next to the buttons
# text is an optional string shown above the buttons
# value will be the text of the selected button
def addRadioButtonsOption(values, text: str = ''):
    return Main.addOption(('radioButtons', (values, str), text))

# similar to a radio button option but shows the values in a drop down box instead
# value will be the text of the selected entry
def addDropDownBoxOption(values):
    return Main.addOption(('dropDownBox', (values, str)))

# add a line edit for entering an arbitrary text line
# text is shown on the left of the line edit and line edit can be filled by default content
# value will be the text typed into the line edit
def addLinEditOption(text: str, defaultContent: str = ''):
    return Main.addOption(('lineEdit', text, defaultContent))

# show an option dialog during the game by calling from makeMove
# the option text will appear before the options
def showOptionsDialog(title, text=''):
    return Main.showOptionsDialog(title, text)

# set a function that is called without arguments next time when options are queried
# the function must check the options and return a non-empty error string if the options are not valid
# then an error message is shown with that error string and the user must change options until
# the function does not return an error string before the options are accepted
def setOptionsChecker(optionsChecker):
    return Main.setOptionsChecker(optionsChecker)

# start a timer that repeatedly calls the paintGame method in the specified interval in milliseconds
# if singleShot is True, paintGame is only called once by this timer
def startPaintGameTimer(milliSeconds, singleShot=False):
    Main.startPaintGameTimer(milliSeconds, singleShot)

# stop the timer started by startPaintGameTimer
# if no such timer has been started, this function does nothing
def stopPaintGameTimer():
    Main.stopPaintGameTimer()

# returns if an timer has been started by startPaintGameTimer and is active
def paintGameTimerIsActive():
    return Main.paintGameTimerIsActive()


##################### relevant for network mode only! #####################


# in local mode same as getCurrentPlayerIndex(), in network mode the index of the player
# who runs the participating program, thus it does not change in network mode throughout the game!
def getThisPlayerIndex():
    return Main.getGameObject().thisPlayerIndex

# register file for transmission over network - on the host the function returns the input filepath
# but on the clients it returns the filepath of the transmitted file in a cache
def registerFile(filepath):
    return Main.registerFile(filepath)

# the handed over names of variables which will not be synchronized over network
def addToNoSyncList(*args):
    Main.addToNoSyncList(*args)

# return a set of player indexes who have already left the game
def getLeftPlayersSet():
    return Main.getGameObject().leftPlayers


# when running this file directly the directory will be searched for games and you can select among the found games
if __name__ == "__main__":
    Main.selectGame()
