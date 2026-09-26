GPW_SUBSTRINGS = (
    "waln",
    "zgromadzeni",
    "akcji serii",
    "akcji własnych",
    "członka zarządu",
    "członka rady",
    "księgi popytu",
    "okresowego raportu",
    "subskrypcji obligacji",
    "zmiana terminu publikacji",
    "skupu akcji własnych",
    "emitenta",
    "zawiadomienia akcjonariuszy",
    "w trybie art.",
    "okaziciela",
    "kapitału zakładowego",
    "korekta oznaczenia raportu",
    "korekta raportu bieżącego",
    "ETF",
    "FIZ",
    "Zawiadomienie o zmianie stanu posiadania",
    "publikacji raportu",
    "publikacji raportów",
)


def has_keywords(title: str, keywords: tuple[str, ...]) -> bool:
    title_lower = title.casefold()

    for substring in keywords:
        if substring.casefold() in title_lower:
            return True

    return False
