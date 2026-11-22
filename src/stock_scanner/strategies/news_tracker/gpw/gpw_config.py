import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GPWConfig:
    gpw_exceptions: tuple[str, ...] = (
        "XTB",
        "CREOTECH",
        "KGHM",
        "CENTURION",
        "KOMBINAT KONOPNY",
        "BUMECH",
        "MEDINICE",
        "CD PROJEKT",
        "ORLEN",
        "SCANWAY",
    )

    gpw_substrings: tuple[str, ...] = (
        "waln",
        "unicredit",
        "michael/str",
        "ab inter rao",
        "liczby głosów",
        "zgromadzeni",
        "skonsolidowanych przychodach",
        "art.",
        "akcji",
        "członka zarządu",
        "członka rady",
        "księgi popytu",
        "okresowego raportu",
        "subskrypcji obligacji",
        "zmiana terminu publikacji",
        "emitenta",
        "zawiadomienia akcjonariuszy",
        "w trybie art.",
        "okaziciela",
        "kapitału zakładowego",
        "korekta oznaczenia raportu",
        "korekta raportu bieżącego",
        "ETF",
        "FIZ",
        "stanu posiadania",
        "rejestracja zmian",
        "zawiadomienie od okcjonariusza",
        "publikacji raportu",
        "publikacji raportów",
        "inne informacje",
        "kapitału docelowego",
        "terminu notowania",
        "osoby zarządzającej",
        "obowiązki zarządcze",
        "złożenie rezygnacji",
        "obligacji",
        "dywidendy",
        "serii",
        "zmiany w strukturze udziałowej",
        "zmiany osobowe",
        "rady nadzorczej",
        "zmiana prokurenta",
        "bank",
        "korekta raportu",
        "raport kwartalny",
        "raport miesięczny",
        "raport roczny",
        "audyt",
        "MOL",
        "raportów okresowych",
        "ryzykiem kursowym",
        "emisji obligacji",
        "nwz",
        "kwartał",
        "danych finansowych",
        "pożycz",
        "kernel holding",
        "po spotkaniu",
        "financial report",
    )

    valid_forecasts = {
        "Silny spadek",
        "Spadek",
        "Neutralny",
        "Wzrost",
        "Silny wzrost",
    }

    gpw_prompt = """WYKONAJ PONIŻSZE POLECENIE DOSŁOWNIE.

    Przeanalizuj zawartość html, który załączam poniżej.

    Tekst zawarty w html, zawsze będzie dotyczył konkretnej spółki giełdowej,
    notowanej na GPW lub na New Connect.

    KROK 1 — ANALIZA INFORMACJI

    Ustal na podstawie rzeczywistej treści html:

    Co dokładnie wydarzyło się według komunikatu?
    Czy informacja jest potencjalnie pozytywna, negatywna czy neutralna dla spółki?
    Czy informacja może mieć istotny wpływ na przyszłe wyniki finansowe, sytuację spółki lub jej wycenę?
    Jaki jest potencjalny mechanizm wpływu tej informacji na kurs akcji?

    Nie wymyślaj żadnych faktów ani danych.

    KROK 2 — PROGNOZA

    Oceń prawdopodobny wpływ analizowanej informacji na kurs akcji spółki.

    Prognoza dotyczy reakcji kursu w ciągu jednej sesji giełdowej od momentu publikacji informacji.

    Prognoza może przyjąć wyłącznie jedną z następujących wartości:

    - "Silny spadek"
    - "Spadek"
    - "Neutralny"
    - "Wzrost"
    - "Silny wzrost"

    KROK 3 — UZASADNIENIE

    Napisz dokładnie dwa zdania uzasadnienia wybranej prognozy.

    Uzasadnienie powinno wskazywać najważniejsze czynniki wynikające z analizowanej informacji.

    KROK 4 — FORMAT ODPOWIEDZI

    Odpowiedź MUSI być poprawnym składniowo obiektem JSON, o strukturze:

    {
    "forecast": "jedna z pięciu dozwolonych wartości",
    "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
    }

    KROK 6 — WALIDACJA

    Przed zwróceniem odpowiedzi sprawdź:

    - Czy rzeczywiście uzyskałeś i przeanalizowałeś treść wskazanego fragmentu html.
    - Czy prognoza jest dokładnie jedną z pięciu dozwolonych wartości.
    - Czy uzasadnienie zawiera dokładnie dwa zdania.
    - Czy odpowiedź jest poprawnym JSON-em.
    - Czy JSON zawiera dokładnie pola "forecast" oraz "justification".
    - Czy poza obiektem JSON nie znajduje się żaden dodatkowy tekst.
    - Czy wartości tekstowe są prawidłowo escapowane zgodnie ze składnią JSON.
    - Jeśli w tekście występują cudzysłowy, użyj apostrofów ' albo escapuj je jako \".

    WAŻNE:

    - Nie dodawaj komentarzy.
    - Nie dodawaj źródeł.
    - Nie dodawaj linków.
    - Nie dodawaj Markdown.
    - Nie używaj bloków ```json.
    - Nie dodawaj tekstu przed ani po obiekcie JSON.
    - Nie dodawaj dodatkowych pól.
    - Nie zwracaj placeholderów.
    - Nie wymyślaj brakujących informacji.

    OSTATECZNA ODPOWIEDŹ MUSI ZAWIERAĆ WYŁĄCZNIE POPRAWNY OBIEKT JSON.

    Analiza ma charakter wyłącznie edukacyjny i informacyjny.
    """


def has_keywords(title: str, keywords: tuple[str, ...]) -> bool:
    title_lower = title.casefold()

    for substring in keywords:
        if substring.casefold() in title_lower:
            return True

    return False


def skip_entry(title: str) -> bool:
    has_exceptions = has_keywords(title, GPWConfig.gpw_exceptions)
    has_substrings = has_keywords(title, GPWConfig.gpw_substrings)

    return has_substrings and not has_exceptions
