import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DAXConfig:
    page_load_timeout: float = 15_000
    prompt_timeout: float = 30_000
    prompt_load_timeout: float = 30_000

    EXCLUDE_KEYWORDS: tuple[str, ...] = (
        # Raporty finansowe
        "geschäftsbericht",
        "jahresfinanzbericht",
        "halbjahresfinanzbericht",
        "quartalsbericht",
        "quartalsmitteilung",
        "zwischenbericht",
        "finanzbericht",
        "jahresabschluss",
        "konzernabschluss",
        "finanzkennzahlen",
        "vorabbekanntmachung",
        "veröffentlichung des finanzberichts",
        # Formalności giełdowe i regulacyjne
        "stimmrechtsmitteilung",
        "stimmrechtsanteile",
        "schwellenberührung",
        "directors' dealings",
        "eigengeschäfte von führungskräften",
        "hauptversammlung",
        "tagesordnung",
        "einberufung",
        "beschlussvorschlag",
        "dividendenbekanntmachung",
        "wertpapierprospekt",
        "bezugsangebot",
        "anleihebedingungen",
        "änderung der satzung",
        # Zmiany personalne
        "personalveränderung",
        "vorstandswechsel",
        "niederlegung des amtes",
        "bestellung zum vorstand",
        "mitglied des aufsichtsrat",
        # Korekty i sprostowania
        "korrektur",
        "berichtigung",
        "korrektur der mitteilung",
        # Raporty i komunikaty okresowe
        "quartalsergebnis",
        "jahresergebnis",
        "zwischenmitteilung",
        "monatsbericht",
        "Search Atlas",
    )

    dax_prompt = """WYKONAJ PONIŻSZE POLECENIE DOSŁOWNIE.

        Przeanalizuj zawartość tekstu, który załączam poniżej.
        Tekst zawsze będzie dotyczył konkretnej spółki giełdowej, notowanej na niemieckiej giełdzie.

        KROK 1 — ANALIZA INFORMACJI

        Ustal na podstawie rzeczywistej treści tekstu:

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

        - Czy rzeczywiście uzyskałeś i przeanalizowałeś treść wskazanego tekstu.
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

    def should_skip(self, title: str) -> bool:
        normalized = title.casefold()

        return any(keyword.casefold() in normalized for keyword in self.EXCLUDE_KEYWORDS)
