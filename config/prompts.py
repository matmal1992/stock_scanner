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

    KROK 2 — DANE DODATKOWE

    Jeżeli są dostępne w internecie, uwzględnij najnowsze informacje dotyczące spółki, w szczególności:

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

    Prognoza dotyczy reakcji kursu w ciągu jednej sesji giełdowej od momentu publikacji informacji.

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

    - Czy rzeczywiście uzyskałeś i przeanalizowałeś treść wskazanego fragmentu html.
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

gold_prompt = """Przeanalizuj poniższy tekst, skopiowany ze strony internetowej. Dotyczy on wydarzenia, informacji lub wiadomości, która może mieć wpływ na cenę złota (XAU/USD).

### KROK 1 — ANALIZA INFORMACJI

Na podstawie rzeczywistej treści otrzymanego tekstu ustal:

- Co dokładnie wydarzyło się według komunikatu?
- Czy informacja jest potencjalnie pozytywna, negatywna czy neutralna dla ceny złota?
- Jaki jest mechanizm potencjalnego wpływu tej informacji na cenę złota?
- Czy wpływ może być bezpośredni, czy wynika z pośredniego oddziaływania na czynniki rynkowe?

Nie wymyślaj faktów ani nie wyciągaj wniosków, których nie uzasadnia treść wiadomości.

### KROK 2 — AKTUALNY KONTEKST RYNKOWY

Jeżeli masz dostęp do internetu, zweryfikuj najnowsze informacje mogące mieć znaczenie dla oceny wpływu analizowanego wydarzenia na cenę złota.

W szczególności uwzględnij:

- Zakupy i sprzedaż złota przez banki centralne.
- Napływy i odpływy kapitału z funduszy ETF opartych na złocie.
- Politykę monetarną FED i oczekiwania dotyczące stóp procentowych.
- Kurs dolara amerykańskiego (USD).
- Rentowności amerykańskich obligacji skarbowych, szczególnie obligacji realnych.
- Dane dotyczące inflacji i sytuacji makroekonomicznej.
- Ryzyko geopolityczne i popyt na złoto jako bezpieczną przystań.
- Najnowsze prognozy i rekomendacje analityków dotyczące ceny złota.
- Inne wydarzenia mogące istotnie wpłynąć na krótkoterminową wycenę złota.

Uwzględniaj wyłącznie informacje, które możesz rzeczywiście zweryfikować i których aktualność możesz ustalić.

Nie wymuszaj uwzględniania wszystkich wymienionych czynników. Wykorzystuj tylko te, które mają istotne znaczenie dla analizowanej wiadomości.

### KROK 3 — PROGNOZA

Oceń najbardziej prawdopodobny wpływ analizowanej informacji na cenę złota (XAU/USD).

Prognoza dotyczy reakcji ceny złota w ciągu jednej sesji giełdowej od momentu publikacji analizowanej informacji.

Wybierz dokładnie jedną z pięciu wartości:

- "Silny spadek"
- "Spadek"
- "Neutralny"
- "Wzrost"
- "Silny wzrost"

Oceniając potencjalną reakcję rynku:

- Uwzględnij znaczenie i wiarygodność informacji.
- Oceń, czy informacja może zaskoczyć uczestników rynku.
- Uwzględnij, czy wydarzenie mogło zostać już zdyskontowane w cenie złota.
- Weź pod uwagę aktualny kontekst makroekonomiczny i rynkowy.
- Nie utożsamiaj pozytywnego wydźwięku wiadomości z automatycznym wzrostem ceny złota ani negatywnego wydźwięku ze spadkiem ceny.

Prognoza ma przedstawiać najbardziej prawdopodobną reakcję rynku, a nie wyłącznie teoretyczny kierunek wpływu informacji.

### KROK 4 — UZASADNIENIE

Przygotuj uzasadnienie wybranej prognozy składające się z dokładnie dwóch zdań.

Uwzględnij w nim najważniejsze czynniki wynikające z analizowanej wiadomości oraz istotnego, zweryfikowanego kontekstu rynkowego.

Wyjaśnij, dlaczego przewidywany kierunek reakcji ceny złota jest najbardziej prawdopodobny.

### KROK 5 — FORMAT ODPOWIEDZI

Zwróć wyłącznie poprawny składniowo obiekt JSON o następującej strukturze:

{
  "forecast": "jedna z pięciu dozwolonych wartości",
  "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
}

### KROK 6 — WALIDACJA

Przed zwróceniem odpowiedzi sprawdź:

- Czy przeanalizowałeś rzeczywistą treść otrzymanej wiadomości?
- Czy analiza dotyczy wyłącznie rynku złota?
- Czy nie wykorzystałeś informacji, których nie można zweryfikować?
- Czy uwzględniłeś istotny kontekst rynkowy, jeżeli był dostępny?
- Czy prognoza dotyczy właściwego horyzontu czasowego?
- Czy wartość "forecast" jest dokładnie jedną z pięciu dozwolonych wartości?
- Czy "justification" zawiera dokładnie dwa zdania?
- Czy JSON zawiera dokładnie pola "forecast" oraz "justification"?
- Czy JSON jest poprawny składniowo i wartości tekstowe są prawidłowo escapowane?

Jeżeli dostępne informacje nie pozwalają na wiarygodne określenie kierunku reakcji rynku, wybierz "Neutralny", o ile jest to najbardziej uzasadniona ocena.

### WAŻNE

- Nie wymyślaj faktów, danych ani wydarzeń.
- Nie zakładaj automatycznej reakcji ceny złota na podstawie samego pozytywnego lub negatywnego wydźwięku wiadomości.
- Nie wykorzystuj informacji dotyczących rynku srebra.
- Nie dodawaj komentarzy, źródeł, linków ani dodatkowych pól.
- Nie używaj Markdown ani bloków kodu.
- Nie dodawaj żadnego tekstu przed obiektem JSON ani po nim.

OSTATECZNA ODPOWIEDŹ MUSI ZAWIERAĆ WYŁĄCZNIE POPRAWNY OBIEKT JSON.

Analiza ma charakter wyłącznie edukacyjny i informacyjny.
    """

silver_prompt = """Przeanalizuj poniższy tekst, skopiowany ze strony internetowej. Dotyczy on wydarzenia, informacji lub wiadomości, która może mieć wpływ na cenę srebra (XAG/USD).

### KROK 1 — ANALIZA INFORMACJI

Na podstawie rzeczywistej treści otrzymanego tekstu ustal:

- Co dokładnie wydarzyło się według komunikatu?
- Czy informacja jest potencjalnie pozytywna, negatywna czy neutralna dla ceny srebra?
- Jaki jest mechanizm potencjalnego wpływu tej informacji na cenę srebra?
- Czy wpływ może być bezpośredni, czy wynika z pośredniego oddziaływania na czynniki rynkowe?

Nie wymyślaj faktów ani nie wyciągaj wniosków, których nie uzasadnia treść wiadomości.

### KROK 2 — AKTUALNY KONTEKST RYNKOWY

Jeżeli masz dostęp do internetu, zweryfikuj najnowsze informacje mogące mieć znaczenie dla oceny wpływu analizowanego wydarzenia na cenę srebra.

W szczególności uwzględnij:

- Globalny popyt przemysłowy na srebro.
- Zapotrzebowanie na srebro w fotowoltaice, elektronice, elektromobilności i innych sektorach technologicznych.
- Podaż srebra z kopalń oraz poziom produkcji największych producentów.
- Podaż srebra pochodzącego z recyklingu.
- Dane dotyczące deficytu lub nadwyżki na globalnym rynku srebra.
- Zapasy srebra w magazynach giełdowych, w szczególności COMEX i LBMA.
- Napływy i odpływy kapitału z funduszy ETF opartych na srebrze.
- Politykę monetarną FED i oczekiwania dotyczące stóp procentowych.
- Kurs dolara amerykańskiego (USD).
- Rentowności amerykańskich obligacji skarbowych.
- Kondycję globalnej gospodarki, szczególnie przemysłu chińskiego i amerykańskiego.
- Relację ceny złota do ceny srebra (Gold/Silver Ratio).
- Ryzyko geopolityczne i popyt inwestycyjny na metale szlachetne.
- Najnowsze prognozy i rekomendacje analityków dotyczące ceny srebra.
- Inne wydarzenia mogące istotnie wpłynąć na krótkoterminową wycenę srebra.

Uwzględniaj wyłącznie informacje, które możesz rzeczywiście zweryfikować i których aktualność możesz ustalić.

Nie wymuszaj uwzględniania wszystkich wymienionych czynników. Wykorzystuj tylko te, które mają istotne znaczenie dla analizowanej wiadomości.

### KROK 3 — PROGNOZA

Oceń najbardziej prawdopodobny wpływ analizowanej informacji na cenę srebra (XAG/USD).

Prognoza dotyczy reakcji ceny srebra w ciągu jednej sesji giełdowej od momentu publikacji analizowanej informacji.

Wybierz dokładnie jedną z pięciu wartości:

- "Silny spadek"
- "Spadek"
- "Neutralny"
- "Wzrost"
- "Silny wzrost"

Oceniając potencjalną reakcję rynku:

- Uwzględnij znaczenie i wiarygodność informacji.
- Oceń, czy informacja może zaskoczyć uczestników rynku.
- Uwzględnij, czy wydarzenie mogło zostać już zdyskontowane w cenie srebra.
- Weź pod uwagę aktualny kontekst makroekonomiczny i rynkowy.
- Rozróżniaj wpływ czynników inwestycyjnych i przemysłowych.
- Uwzględnij, że pogorszenie koniunktury gospodarczej może negatywnie wpływać na popyt przemysłowy na srebro.
- Pamiętaj, że srebro może reagować silniej niż złoto na zmiany nastrojów rynkowych i oczekiwań dotyczących koniunktury gospodarczej.

Nie utożsamiaj pozytywnego wydźwięku wiadomości z automatycznym wzrostem ceny srebra ani negatywnego wydźwięku ze spadkiem ceny.

Prognoza ma przedstawiać najbardziej prawdopodobną reakcję rynku, a nie wyłącznie teoretyczny kierunek wpływu informacji.

### KROK 4 — UZASADNIENIE

Przygotuj uzasadnienie wybranej prognozy składające się z dokładnie dwóch zdań.

Uwzględnij w nim najważniejsze czynniki wynikające z analizowanej wiadomości oraz istotnego, zweryfikowanego kontekstu rynkowego.

Wyjaśnij, dlaczego przewidywany kierunek reakcji ceny srebra jest najbardziej prawdopodobny.

### KROK 5 — FORMAT ODPOWIEDZI

Zwróć wyłącznie poprawny składniowo obiekt JSON o następującej strukturze:

{
  "forecast": "jedna z pięciu dozwolonych wartości",
  "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
}

### KROK 6 — WALIDACJA

Przed zwróceniem odpowiedzi sprawdź:

- Czy przeanalizowałeś rzeczywistą treść otrzymanej wiadomości?
- Czy analiza dotyczy wyłącznie rynku srebra?
- Czy nie wykorzystałeś informacji, których nie można zweryfikować?
- Czy uwzględniłeś istotny kontekst rynkowy, jeżeli był dostępny?
- Czy prognoza dotyczy właściwego horyzontu czasowego?
- Czy wartość "forecast" jest dokładnie jedną z pięciu dozwolonych wartości?
- Czy "justification" zawiera dokładnie dwa zdania?
- Czy JSON zawiera dokładnie pola "forecast" oraz "justification"?
- Czy JSON jest poprawny składniowo i wartości tekstowe są prawidłowo escapowane?

Jeżeli dostępne informacje nie pozwalają na wiarygodne określenie kierunku reakcji rynku, wybierz "Neutralny", o ile jest to najbardziej uzasadniona ocena.

### WAŻNE

- Nie wymyślaj faktów, danych ani wydarzeń.
- Nie zakładaj automatycznej reakcji ceny srebra na podstawie samego pozytywnego lub negatywnego wydźwięku wiadomości.
- Nie wykorzystuj informacji dotyczących rynku innych metali jako bezpośredniego substytutu analizy srebra.
- Nie dodawaj komentarzy, źródeł, linków ani dodatkowych pól.
- Nie używaj Markdown ani bloków kodu.
- Nie dodawaj żadnego tekstu przed obiektem JSON ani po nim.

OSTATECZNA ODPOWIEDŹ MUSI ZAWIERAĆ WYŁĄCZNIE POPRAWNY OBIEKT JSON.

Analiza ma charakter wyłącznie edukacyjny i informacyjny.
    """


copper_prompt = """Przeanalizuj poniższy tekst, skopiowany ze strony internetowej. Dotyczy on wydarzenia, informacji lub wiadomości, która może mieć wpływ na cenę miedzi (HG / COMEX lub LME Copper).

### KROK 1 — ANALIZA INFORMACJI

Na podstawie rzeczywistej treści otrzymanego tekstu ustal:

- Co dokładnie wydarzyło się według komunikatu?
- Czy informacja jest potencjalnie pozytywna, negatywna czy neutralna dla ceny miedzi?
- Jaki jest mechanizm potencjalnego wpływu tej informacji na cenę miedzi?
- Czy wpływ może być bezpośredni, czy wynika z pośredniego oddziaływania na czynniki rynkowe?

Nie wymyślaj faktów ani nie wyciągaj wniosków, których nie uzasadnia treść wiadomości.

### KROK 2 — AKTUALNY KONTEKST RYNKOWY

Jeżeli masz dostęp do internetu, zweryfikuj najnowsze informacje mogące mieć znaczenie dla oceny wpływu analizowanego wydarzenia na cenę miedzi.

W szczególności uwzględnij:

- Kondycję chińskiej gospodarki, w szczególności sektora przemysłowego, budownictwa i rynku nieruchomości.
- Chiński popyt na miedź oraz politykę gospodarczą i stymulacyjną Chin.
- Globalny popyt przemysłowy na miedź.
- Zapotrzebowanie na miedź w energetyce, infrastrukturze elektroenergetycznej, elektromobilności, fotowoltaice i centrach danych.
- Produkcję największych kopalń miedzi na świecie.
- Zakłócenia wydobycia, strajki, problemy operacyjne i zamykanie kopalń.
- Podaż miedzi z recyklingu.
- Globalny bilans podaży i popytu, w szczególności deficyt lub nadwyżkę na rynku miedzi.
- Poziom zapasów miedzi na giełdach LME, COMEX i SHFE.
- Premie fizyczne i inne dostępne wskaźniki popytu na miedź.
- Politykę handlową największych gospodarek, w szczególności cła, sankcje i ograniczenia eksportowe.
- Kurs dolara amerykańskiego (USD).
- Politykę monetarną FED i oczekiwania dotyczące stóp procentowych.
- Kondycję globalnej gospodarki i najnowsze wskaźniki PMI.
- Najnowsze prognozy i rekomendacje analityków dotyczące ceny miedzi.
- Inne wydarzenia mogące istotnie wpłynąć na krótkoterminową wycenę miedzi.

Uwzględniaj wyłącznie informacje, które możesz rzeczywiście zweryfikować i których aktualność możesz ustalić.

Nie wymuszaj uwzględniania wszystkich wymienionych czynników. Wykorzystuj tylko te, które mają istotne znaczenie dla analizowanej wiadomości.

### KROK 3 — PROGNOZA

Oceń najbardziej prawdopodobny wpływ analizowanej informacji na cenę miedzi.

Prognoza dotyczy reakcji ceny miedzi w ciągu jednej sesji giełdowej od momentu publikacji analizowanej informacji.

Wybierz dokładnie jedną z pięciu wartości:

- "Silny spadek"
- "Spadek"
- "Neutralny"
- "Wzrost"
- "Silny wzrost"

Oceniając potencjalną reakcję rynku:

- Uwzględnij znaczenie i wiarygodność informacji.
- Oceń, czy informacja może zaskoczyć uczestników rynku.
- Uwzględnij, czy wydarzenie mogło zostać już zdyskontowane w cenie miedzi.
- Weź pod uwagę aktualny kontekst makroekonomiczny i rynkowy.
- Rozróżniaj wpływ czynników podażowych i popytowych.
- Zwróć szczególną uwagę na informacje dotyczące Chin, które są kluczowym uczestnikiem globalnego rynku miedzi.
- Uwzględnij, że ograniczenia podaży lub zakłócenia wydobycia mogą wspierać ceny miedzi, natomiast wzrost zapasów i osłabienie popytu przemysłowego mogą wywierać na nie presję.
- Pamiętaj, że miedź jest silnie powiązana z oczekiwaniami dotyczącymi globalnej koniunktury gospodarczej.

Nie utożsamiaj pozytywnego wydźwięku wiadomości z automatycznym wzrostem ceny miedzi ani negatywnego wydźwięku ze spadkiem ceny.

Prognoza ma przedstawiać najbardziej prawdopodobną reakcję rynku, a nie wyłącznie teoretyczny kierunek wpływu informacji.

### KROK 4 — UZASADNIENIE

Przygotuj uzasadnienie wybranej prognozy składające się z dokładnie dwóch zdań.

Uwzględnij w nim najważniejsze czynniki wynikające z analizowanej wiadomości oraz istotnego, zweryfikowanego kontekstu rynkowego.

Wyjaśnij, dlaczego przewidywany kierunek reakcji ceny miedzi jest najbardziej prawdopodobny.

### KROK 5 — FORMAT ODPOWIEDZI

Zwróć wyłącznie poprawny składniowo obiekt JSON o następującej strukturze:

{
  "forecast": "jedna z pięciu dozwolonych wartości",
  "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
}

### KROK 6 — WALIDACJA

Przed zwróceniem odpowiedzi sprawdź:

- Czy przeanalizowałeś rzeczywistą treść otrzymanej wiadomości?
- Czy analiza dotyczy wyłącznie rynku miedzi?
- Czy nie wykorzystałeś informacji, których nie można zweryfikować?
- Czy uwzględniłeś istotny kontekst rynkowy, jeżeli był dostępny?
- Czy prognoza dotyczy właściwego horyzontu czasowego?
- Czy wartość "forecast" jest dokładnie jedną z pięciu dozwolonych wartości?
- Czy "justification" zawiera dokładnie dwa zdania?
- Czy JSON zawiera dokładnie pola "forecast" oraz "justification"?
- Czy JSON jest poprawny składniowo i wartości tekstowe są prawidłowo escapowane?

Jeżeli dostępne informacje nie pozwalają na wiarygodne określenie kierunku reakcji rynku, wybierz "Neutralny", o ile jest to najbardziej uzasadniona ocena.

### WAŻNE

- Nie wymyślaj faktów, danych ani wydarzeń.
- Nie zakładaj automatycznej reakcji ceny miedzi na podstawie samego pozytywnego lub negatywnego wydźwięku wiadomości.
- Nie wykorzystuj informacji dotyczących innych metali jako bezpośredniego substytutu analizy miedzi.
- Nie dodawaj komentarzy, źródeł, linków ani dodatkowych pól.
- Nie używaj Markdown ani bloków kodu.
- Nie dodawaj żadnego tekstu przed obiektem JSON ani po nim.

OSTATECZNA ODPOWIEDŹ MUSI ZAWIERAĆ WYŁĄCZNIE POPRAWNY OBIEKT JSON.

Analiza ma charakter wyłącznie edukacyjny i informacyjny.
    """
