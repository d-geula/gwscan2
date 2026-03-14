class LoginSelectors:
    LOGIN_MODAL = 'button[data-target="#myModal"]'
    PIN_CAPTCHA = "label[for=PIN] > img"
    PIN = "input#PIN"
    USERNAME = "input#usname"
    EMAIL = "input#usemail"
    PASSWORD = "input#uspass"
    SUBMIT = "button[type=submit]"
    COMMAND_CENTER_HEADING = 'main[class="mine"] > h3'


class BattlefieldSelectors:
    PLAYER_ROWS = "tr.hidden-xs-down"
    NAME_CELL = "td#name_titles"
    PLAYER_LINK = 'td#name_titles a[href^="stats.php?id="]'
    POP_CELL = "td#pop"


class ProfileSelectors:
    INFO = "#info"
    INFO_ROWS = "#info tbody tr"
    INFO_CELLS = "td"
    ALLIANCE_LINK = 'a[href^="allianceMembers.php?id="]'
    PLANET_ROWS = "#planets tbody tr"


class SpySelectors:
    SPY_BUTTON = 'input[name="submit"][value="Spy"]'
    NUM_SPIES = 'input[name="numspies"]'
    GO_BUTTON = 'button.btn.btn-outline-secondary[type="submit"]'
    SUCCESS_MESSAGE = "div.row.alert-box.static h4 strong"
    CARD_TITLES = "h6.card-title"
    PLANET_ROWS = "#planets tbody tr"
