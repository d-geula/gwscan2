class LoginLocators:
    LOGIN_MODAL = 'button[data-target="#myModal"]'
    PIN_CAPTCHA = "label[for=PIN] > img"
    PIN = "input#PIN"
    USERNAME = "input#usname"
    EMAIL = "input#usemail"
    PASSWORD = "input#uspass"
    SUBMIT = "button[type=submit]"
    COMMAND_CENTER_HEADING = 'main[class="mine"] > h3'


class BattlefieldLocators:
    PLAYER_ROWS = "tr.hidden-xs-down"
    NAME_CELL = "td#name_titles"
    PLAYER_LINK = 'td#name_titles a[href^="stats.php?id="]'
    POP_CELL = "td#pop"


class ProfileLocators:
    INFO = "#info"
    INFO_ROWS = "#info tbody tr"
    INFO_CELLS = "td"
    ALLIANCE_LINK = 'a[href^="allianceMembers.php?id="]'
    PLANET_ROWS = "#planets tbody tr"


class SpyLocators:
    SPY_BUTTON = 'input[name="submit"][value="Spy"]'
    NUM_SPIES = 'input[name="numspies"]'
    GO_BUTTON = 'button.btn.btn-outline-secondary[type="submit"]'
    SUCCESS_MESSAGE = "div.row.alert-box.static h4 strong"
    CARD_TITLES = "h6.card-title"
    PLANET_ROWS = "#planets tbody tr"


battlefield_players_table = """
        (() => Array.from(document.querySelectorAll("tr.hidden-xs-down")).map((row) => {
            const nameCell = row.querySelector("td#name_titles");
            const link = row.querySelector('td#name_titles a[href^="stats.php?id="]');
            let alliance = "";
            if (nameCell) {
                // Alliance text is not directly labeled; it sits after the bracketed title text
                // and before the next line break inside the same name cell.
                const childNodes = Array.from(nameCell.childNodes);
                for (let index = 0; index < childNodes.length; index += 1) {
                    const node = childNodes[index];
                    if (node.nodeType !== Node.TEXT_NODE || !(node.textContent || "").includes("[")) {
                        continue;
                    }

                    for (let siblingIndex = index + 1; siblingIndex < childNodes.length; siblingIndex += 1) {
                        const sibling = childNodes[siblingIndex];
                        if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === "BR") {
                            break;
                        }
                        if (sibling.nodeType !== Node.ELEMENT_NODE || sibling.tagName !== "SPAN") {
                            continue;
                        }

                        alliance = (sibling.textContent || "").trim();
                        break;
                    }

                    if (alliance) {
                        break;
                    }
                }
            }
            const popCell = row.querySelector("td#pop");
            // Keep the raw text so Python can decide whether the pop value is intentionally hidden.
            return {
                name: link ? (link.textContent || "").trim() : "",
                href: link ? (link.getAttribute("href") || "") : "",
                alliance,
                pop_text: popCell ? (popCell.textContent || "") : "",
                has_pop_cell: Boolean(popCell),
            };
        }))()
        """