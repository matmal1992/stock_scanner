from dataclasses import dataclass


@dataclass
class Config:
    page_load_timeout: float = 15_000
    prompt_timeout: float = 30_000

    gpw_substrings: tuple[str, ...] = (
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

    valid_forecasts = {
        "Silny spadek",
        "Spadek",
        "Neutralny",
        "Wzrost",
        "Silny wzrost",
    }

    gpw_prompt = """WYKONAJ PONIŻSZE POLECENIE DOSŁOWNIE.

    Otwórz i przeanalizuj rzeczywistą treść artykułu znajdującego się pod podanym linkiem.

    Nie zgaduj treści na podstawie tytułu, adresu URL ani innych metadanych. 
    Jeżeli nie możesz uzyskać rzeczywistej treści artykułu, nie wymyślaj jej.

    Artykuł zawsze będzie dotyczył konkretnej spółki giełdowej, notowanej na GPW lub na New Connect.

    KROK 1 — ANALIZA INFORMACJI

    Ustal na podstawie rzeczywistej treści artykułu:

    Co dokładnie wydarzyło się według komunikatu?
    Czy informacja jest potencjalnie pozytywna, negatywna czy neutralna dla spółki?
    Czy informacja może mieć istotny wpływ na przyszłe wyniki finansowe, sytuację spółki lub jej wycenę?
    Jaki jest potencjalny mechanizm wpływu tej informacji na kurs akcji?

    Nie wymyślaj żadnych faktów ani danych.

    KROK 2 — DANE DODATKOWE

    Jeżeli są dostępne, uwzględnij najnowsze informacje dotyczące spółki, w szczególności:

    - wyniki finansowe,
    - prognozy,
    - rekomendacje analityków,
    - strategię spółki,
    - istotne wydarzenia korporacyjne,
    - inne informacje mogące mieć znaczenie dla oceny reakcji rynku.

    Uwzględniaj wyłącznie informacje, które możesz rzeczywiście zweryfikować.
    Bazuj wyłącznie na najnowszych dostępnych danych w odniesieniu do 
    daty i godziny wykonania niniejszego polecenia.

    KROK 3 — PROGNOZA

    Oceń prawdopodobny wpływ analizowanej informacji na kurs akcji spółki.

    Prognoza dotyczy reakcji kursu w ciągu 1-2 sesji giełdowych od momentu publikacji informacji.

    Prognoza może przyjąć wyłącznie jedną z następujących wartości:

    - "Silny spadek"
    - "Spadek"
    - "Neutralny"
    - "Wzrost"
    - "Silny wzrost"

    KROK 4 — UZASADNIENIE

    Napisz dokładnie dwa zdania uzasadnienia wybranej prognozy.

    Uzasadnienie powinno wskazywać najważniejsze czynniki wynikające z analizowanej informacji oraz, 
    jeżeli są istotne, z dodatkowych zweryfikowanych danych.

    KROK 5 — FORMAT ODPOWIEDZI

    Odpowiedź MUSI być poprawnym składniowo obiektem JSON, o strukturze:

    {
    "forecast": "jedna z pięciu dozwolonych wartości",
    "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
    }

    KROK 6 — WALIDACJA

    Przed zwróceniem odpowiedzi sprawdź:

    - Czy rzeczywiście uzyskałeś i przeanalizowałeś treść wskazanego linku.
    - Czy nie wykorzystałeś informacji, których nie można zweryfikować.
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
