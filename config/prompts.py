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

gold_prompt = """Przeanalizuj poniższy tekst, skopiowany ze strony internetowej. Dotyczy on wydarzenia,
informacji lub wiadomości, która może mieć wpływ na cenę złota (XAU/USD).

KROK 1 - IDENTYFIKACJA I ANALIZA WIADOMOŚCI

Na podstawie otrzymanego tekstu:

- Zidentyfikuj główną treść wiadomości i ustal, co dokładnie się wydarzyło.
Ignoruj reklamy, menu, stopki, komentarze, odnośniki i
inne elementy niezwiązane bezpośrednio z głównym komunikatem.
- Ustal datę publikacji oraz datę opisywanego wydarzenia, jeżeli są dostępne.
- Oceń, czy informacja jest potencjalnie pozytywna, negatywna czy neutralna dla ceny złota.
- Ustal mechanizm jej potencjalnego wpływu na XAU/USD, rozróżniając oddziaływanie bezpośrednie i pośrednie.

Nie dopisuj faktów ani nie wyciągaj wniosków, których nie uzasadnia treść wiadomości.

KROK 2 - AKTUALNY KONTEKST RYNKOWY

Jeżeli masz dostęp do internetu, zweryfikuj aktualne informacje,
które mogą istotnie wpłynąć na ocenę analizowanego wydarzenia.

W szczególności uwzględnij:

- Zakupy i sprzedaż złota przez banki centralne oraz ich wpływ na globalny popyt.
- Napływy i odpływy kapitału z funduszy ETF opartych na złocie.
- Politykę FED, oczekiwania dotyczące stóp procentowych oraz perspektywy polityki monetarnej.
- Kurs dolara amerykańskiego (USD).
- Rentowności amerykańskich obligacji skarbowych, szczególnie rentowności realne.
- Dane dotyczące inflacji i aktualnej sytuacji makroekonomicznej.
- Ryzyko geopolityczne i popyt na złoto jako bezpieczną przystań.
- Globalny popyt na złoto, w szczególności popyt inwestycyjny i jubilerski.
- Najnowsze prognozy i rekomendacje analityków dotyczące ceny złota.
- Inne wydarzenia mogące istotnie wpłynąć na krótkoterminową wycenę złota.

Nie musisz uwzględniać wszystkich czynników. Wybierz wyłącznie te,
które mają rzeczywiste znaczenie dla analizowanej wiadomości.

Korzystaj wyłącznie z informacji, których aktualność i wiarygodność możesz zweryfikować.
Nie przedstawiaj niepotwierdzonych danych jako faktów.

KROK 3 - PROGNOZA REAKCJI RYNKU

Oceń najbardziej prawdopodobną reakcję ceny złota (XAU/USD) w ciągu jednej sesji giełdowej od
momentu publikacji analizowanej wiadomości.

Wybierz dokładnie jedną z poniższych wartości:

- "Silny spadek"
- "Spadek"
- "Neutralny"
- "Wzrost"
- "Silny wzrost"

Przy podejmowaniu decyzji uwzględnij:

- Znaczenie, wiarygodność i potencjalną skalę wydarzenia.
- Czy informacja jest nowa i może zaskoczyć uczestników rynku.
- Czy wydarzenie lub jego konsekwencje mogły zostać już uwzględnione w cenie złota.
- Aktualny kontekst makroekonomiczny i rynkowy.
- Potencjalny wpływ na popyt inwestycyjny, popyt ze strony banków centralnych oraz atrakcyjność 
złota jako bezpiecznej przystani.
- Wpływ zmian oczekiwań dotyczących stóp procentowych, kursu USD i rentowności realnych obligacji USA.
- Możliwe przeciwstawne czynniki, które mogą ograniczać lub odwracać reakcję rynku.

Nie utożsamiaj pozytywnego wydźwięku wiadomości z automatycznym wzrostem ceny ani
negatywnego wydźwięku ze spadkiem ceny.

Pamiętaj, że złoto jest przede wszystkim metalem szlachetnym i aktywem inwestycyjnym,
dlatego jego cena może reagować na zmiany oczekiwań dotyczących polityki monetarnej,
wartości dolara amerykańskiego, rentowności obligacji oraz poziomu ryzyka geopolitycznego.

Kategorie "Silny spadek" i "Silny wzrost" stosuj wyłącznie w przypadku informacji o wyjątkowo dużym znaczeniu,
mogących wywołać zdecydowaną reakcję rynku.

Prognoza ma przedstawiać najbardziej prawdopodobną rzeczywistą reakcję rynku,
a nie wyłącznie teoretyczny kierunek oddziaływania informacji.

Jeżeli dostępne dane nie pozwalają na wiarygodne określenie kierunku reakcji, wybierz "Neutralny".

KROK 4 - UZASADNIENIE

Przygotuj uzasadnienie prognozy składające się z dokładnie dwóch zdań.

Uwzględnij w nim:

- Najważniejszy mechanizm wpływu analizowanej wiadomości na złoto.
- Najistotniejsze czynniki aktualnego kontekstu rynkowego.
- Powód, dla którego przewidywany kierunek reakcji jest najbardziej prawdopodobny.

KROK 5 - FORMAT ODPOWIEDZI

Zwróć wyłącznie poprawny składniowo obiekt JSON o następującej strukturze:

{
  "forecast": "jedna z pięciu dozwolonych wartości",
  "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
}

Przed zwróceniem odpowiedzi sprawdź poprawność JSON, zgodność prognozy z dozwolonymi wartościami oraz to,
czy uzasadnienie zawiera dokładnie dwa zdania.

Nie dodawaj komentarzy, źródeł, linków, dodatkowych pól ani tekstu poza obiektem JSON.
Nie używaj Markdown ani bloków kodu.

Analiza ma charakter wyłącznie edukacyjny i informacyjny.
"""

silver_prompt = """Przeanalizuj poniższy tekst, skopiowany ze strony internetowej. Dotyczy on wydarzenia, 
informacji lub wiadomości, która może mieć wpływ na cenę srebra (XAG/USD).

KROK 1 — IDENTYFIKACJA I ANALIZA WIADOMOŚCI

Na podstawie otrzymanego tekstu:

- Zidentyfikuj główną treść wiadomości i ustal, co dokładnie się wydarzyło.
Ignoruj reklamy, menu, stopki, komentarze, odnośniki i 
inne elementy niezwiązane bezpośrednio z głównym komunikatem.
- Ustal datę publikacji oraz datę opisywanego wydarzenia, jeżeli są dostępne.
- Oceń, czy informacja jest potencjalnie pozytywna, negatywna czy neutralna dla ceny srebra.
- Ustal mechanizm jej potencjalnego wpływu na XAG/USD, rozróżniając oddziaływanie bezpośrednie i pośrednie.

Nie dopisuj faktów ani nie wyciągaj wniosków, których nie uzasadnia treść wiadomości.

KROK 2 — AKTUALNY KONTEKST RYNKOWY

Jeżeli masz dostęp do internetu, zweryfikuj aktualne informacje, 
które mogą istotnie wpłynąć na ocenę analizowanego wydarzenia.

W szczególności uwzględnij:

- Globalny popyt przemysłowy i inwestycyjny na srebro.
- Popyt ze strony fotowoltaiki, elektroniki, elektromobilności i innych sektorów technologicznych.
- Podaż srebra z kopalń i recyklingu oraz sytuację na globalnym rynku srebra.
- Zapasy srebra, w szczególności COMEX i LBMA, oraz przepływy kapitału do funduszy ETF.
- Politykę FED, oczekiwania dotyczące stóp procentowych, kurs USD i rentowności obligacji USA.
- Kondycję gospodarki światowej, szczególnie przemysłu Chin i USA.
- Relację ceny złota do srebra (Gold/Silver Ratio).
- Ryzyko geopolityczne i aktualne prognozy rynkowe.

Nie musisz uwzględniać wszystkich czynników. Wybierz wyłącznie te, 
które mają rzeczywiste znaczenie dla analizowanej wiadomości.

Korzystaj wyłącznie z informacji, których aktualność i wiarygodność możesz zweryfikować. 
Nie przedstawiaj niepotwierdzonych danych jako faktów.

KROK 3 — PROGNOZA REAKCJI RYNKU

Oceń najbardziej prawdopodobną reakcję ceny srebra (XAG/USD) w ciągu jednej sesji giełdowej od 
momentu publikacji analizowanej wiadomości.

Wybierz dokładnie jedną z poniższych wartości:

- "Silny spadek"
- "Spadek"
- "Neutralny"
- "Wzrost"
- "Silny wzrost"

Przy podejmowaniu decyzji uwzględnij:

- Znaczenie, wiarygodność i potencjalną skalę wydarzenia.
- Czy informacja jest nowa i może zaskoczyć uczestników rynku.
- Czy wydarzenie lub jego konsekwencje mogły zostać już uwzględnione w cenie srebra.
- Aktualny kontekst makroekonomiczny i rynkowy.
- Potencjalny wpływ na popyt przemysłowy, popyt inwestycyjny lub podaż srebra.
- Możliwe przeciwstawne czynniki, które mogą ograniczać lub odwracać reakcję rynku.

Nie utożsamiaj pozytywnego wydźwięku wiadomości z automatycznym wzrostem ceny ani 
negatywnego wydźwięku ze spadkiem ceny.
Pamiętaj, że srebro jest jednocześnie metalem szlachetnym i surowcem przemysłowym, 
dlatego jego cena może reagować odmiennie na zmiany nastrojów inwestycyjnych
i oczekiwań dotyczących koniunktury gospodarczej.
Kategorie "Silny spadek" i "Silny wzrost" stosuj wyłącznie w przypadku informacji o wyjątkowo dużym znaczeniu,
mogących wywołać zdecydowaną reakcję rynku.
Prognoza ma przedstawiać najbardziej prawdopodobną rzeczywistą reakcję rynku, 
a nie wyłącznie teoretyczny kierunek oddziaływania informacji.
Jeżeli dostępne dane nie pozwalają na wiarygodne określenie kierunku reakcji, wybierz "Neutralny".

KROK 4 — UZASADNIENIE

Przygotuj uzasadnienie prognozy składające się z dokładnie dwóch zdań.

Uwzględnij w nim:

- Najważniejszy mechanizm wpływu analizowanej wiadomości na srebro.
- Najistotniejsze czynniki aktualnego kontekstu rynkowego.
- Powód, dla którego przewidywany kierunek reakcji jest najbardziej prawdopodobny.

### KROK 5 — FORMAT ODPOWIEDZI

Zwróć wyłącznie poprawny składniowo obiekt JSON o następującej strukturze:

{
  "forecast": "jedna z pięciu dozwolonych wartości",
  "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
}

Przed zwróceniem odpowiedzi sprawdź poprawność JSON, zgodność prognozy z dozwolonymi wartościami oraz to, 
czy uzasadnienie zawiera dokładnie dwa zdania.

Nie dodawaj komentarzy, źródeł, linków, dodatkowych pól, ani tekstu poza obiektem JSON.
Nie używaj Markdown ani bloków kodu.

Analiza ma charakter wyłącznie edukacyjny i informacyjny.
"""


copper_prompt = """Przeanalizuj poniższy tekst, skopiowany ze strony internetowej. Dotyczy on wydarzenia,
informacji lub wiadomości, która może mieć wpływ na cenę miedzi (HG / COMEX lub LME Copper).

KROK 1 - IDENTYFIKACJA I ANALIZA WIADOMOŚCI

Na podstawie otrzymanego tekstu:

- Zidentyfikuj główną treść wiadomości i ustal, co dokładnie się wydarzyło.
Ignoruj reklamy, menu, stopki, komentarze, odnośniki i
inne elementy niezwiązane bezpośrednio z głównym komunikatem.
- Ustal datę publikacji oraz datę opisywanego wydarzenia, jeżeli są dostępne.
- Oceń, czy informacja jest potencjalnie pozytywna, negatywna czy neutralna dla ceny miedzi.
- Ustal mechanizm jej potencjalnego wpływu na cenę miedzi, 
rozróżniając oddziaływanie bezpośrednie i pośrednie.

Nie dopisuj faktów ani nie wyciągaj wniosków, których nie uzasadnia treść wiadomości.

KROK 2 - AKTUALNY KONTEKST RYNKOWY

Jeżeli masz dostęp do internetu, zweryfikuj aktualne informacje,
które mogą istotnie wpłynąć na ocenę analizowanego wydarzenia.

W szczególności uwzględnij:

- Kondycję chińskiej gospodarki, w szczególności sektora przemysłowego, budownictwa i rynku nieruchomości.
- Chiński popyt na miedź oraz politykę gospodarczą i stymulacyjną Chin.
- Globalny popyt przemysłowy na miedź.
- Zapotrzebowanie na miedź w energetyce, infrastrukturze elektroenergetycznej, elektromobilności, 
fotowoltaice i centrach danych.
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

Nie musisz uwzględniać wszystkich czynników. Wybierz wyłącznie te,
które mają rzeczywiste znaczenie dla analizowanej wiadomości.

Korzystaj wyłącznie z informacji, których aktualność i wiarygodność możesz zweryfikować.
Nie przedstawiaj niepotwierdzonych danych jako faktów.

KROK 3 - PROGNOZA REAKCJI RYNKU

Oceń najbardziej prawdopodobną reakcję ceny miedzi (HG / COMEX lub LME Copper)
w ciągu jednej sesji giełdowej od momentu publikacji analizowanej wiadomości.

Wybierz dokładnie jedną z poniższych wartości:

- "Silny spadek"
- "Spadek"
- "Neutralny"
- "Wzrost"
- "Silny wzrost"

Przy podejmowaniu decyzji uwzględnij:

- Znaczenie, wiarygodność i potencjalną skalę wydarzenia.
- Czy informacja jest nowa i może zaskoczyć uczestników rynku.
- Czy wydarzenie lub jego konsekwencje mogły zostać już uwzględnione w cenie miedzi.
- Aktualny kontekst makroekonomiczny i rynkowy.
- Potencjalny wpływ na podaż i popyt na miedź.
- Możliwe przeciwstawne czynniki, które mogą ograniczać lub odwracać reakcję rynku.

Zwróć szczególną uwagę na informacje dotyczące Chin, które są kluczowym uczestnikiem globalnego rynku miedzi.

Pamiętaj, że ograniczenia podaży lub zakłócenia wydobycia mogą wspierać ceny miedzi,
natomiast wzrost zapasów i osłabienie popytu przemysłowego mogą wywierać na nie presję.

Miedź jest silnie powiązana z oczekiwaniami dotyczącymi globalnej koniunktury gospodarczej,
dlatego pogorszenie perspektyw gospodarczych może negatywnie wpływać na jej cenę,
nawet jeżeli jednocześnie pojawiają się czynniki ograniczające podaż.

Nie utożsamiaj pozytywnego wydźwięku wiadomości z automatycznym wzrostem ceny ani
negatywnego wydźwięku ze spadkiem ceny.

Kategorie "Silny spadek" i "Silny wzrost" stosuj wyłącznie w przypadku informacji o wyjątkowo dużym znaczeniu,
mogących wywołać zdecydowaną reakcję rynku.

Prognoza ma przedstawiać najbardziej prawdopodobną rzeczywistą reakcję rynku,
a nie wyłącznie teoretyczny kierunek oddziaływania informacji.

Jeżeli dostępne dane nie pozwalają na wiarygodne określenie kierunku reakcji, wybierz "Neutralny".

KROK 4 - UZASADNIENIE

Przygotuj uzasadnienie prognozy składające się z dokładnie dwóch zdań.

Uwzględnij w nim:

- Najważniejszy mechanizm wpływu analizowanej wiadomości na cenę miedzi.
- Najistotniejsze czynniki aktualnego kontekstu rynkowego.
- Powód, dla którego przewidywany kierunek reakcji jest najbardziej prawdopodobny.

KROK 5 - FORMAT ODPOWIEDZI

Zwróć wyłącznie poprawny składniowo obiekt JSON o następującej strukturze:

{
  "forecast": "jedna z pięciu dozwolonych wartości",
  "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
}

Przed zwróceniem odpowiedzi sprawdź poprawność JSON, zgodność prognozy z dozwolonymi wartościami oraz to,
czy uzasadnienie zawiera dokładnie dwa zdania.

Nie dodawaj komentarzy, źródeł, linków, dodatkowych pól ani tekstu poza obiektem JSON.
Nie używaj Markdown ani bloków kodu.

Analiza ma charakter wyłącznie edukacyjny i informacyjny.
"""

gold_prompt_headline = """Otrzymasz pojedynczy nagłówek wiadomości dotyczący wydarzenia, 
które może mieć wpływ na cenę złota (XAU/USD).

Twoim zadaniem jest określenie najbardziej prawdopodobnego kierunku reakcji ceny złota w ciągu jednej sesji 
giełdowej od publikacji wiadomości.

KROK 1 - ANALIZA INFORMACJI I KONTEKSTU RYNKOWEGO

Zinterpretuj wydarzenie opisane w nagłówku i oceń jego potencjalny wpływ na cenę złota.

Jeżeli masz dostęp do internetu, zweryfikuj wydarzenie i uzupełnij analizę o aktualne dane rynkowe.

Uwzględnij przede wszystkim:

- Politykę FED i oczekiwania dotyczące stóp procentowych.
- Kurs USD i indeks DXY.
- Rentowności amerykańskich obligacji, szczególnie realne.
- Dane dotyczące inflacji, zatrudnienia i wzrostu gospodarczego.
- Zakupy złota przez banki centralne i przepływy kapitału do ETF.
- Ryzyko geopolityczne i popyt na złoto jako bezpieczną przystań.
- Inne czynniki istotne dla analizowanego wydarzenia.

Nie musisz uwzględniać wszystkich wymienionych czynników. Skoncentruj się na tych, 
które rzeczywiście mogą wpłynąć na krótkoterminową cenę złota.

Oceń:

- Znaczenie i wiarygodność informacji.
- Jej nowość oraz stopień zaskoczenia rynku.
- Czy rynek zdążył już uwzględnić ją w cenie złota.
- Potencjalny mechanizm wpływu na złoto.
- Aktualną sytuację rynkową i możliwe przeciwstawne czynniki.

Nie dopisuj niepotwierdzonych informacji. Preferuj wiarygodne i aktualne źródła, 
w szczególności źródła pierwotne.

KROK 2 - PROGNOZA REAKCJI RYNKU

Oceń najbardziej prawdopodobną rzeczywistą reakcję ceny XAU/USD w ciągu jednej sesji giełdowej od 
publikacji wiadomości.

Wybierz dokładnie jedną z poniższych wartości:

- "Silny spadek"
- "Spadek"
- "Neutralny"
- "Wzrost"
- "Silny wzrost"

Nie utożsamiaj teoretycznego wpływu informacji z rzeczywistą reakcją rynku. Uwzględnij jej znaczenie, 
aktualny kontekst rynkowy, stopień zdyskontowania oraz możliwe przeciwstawne czynniki.

Kategorie "Silny spadek" i "Silny wzrost" stosuj wyłącznie w przypadku wyjątkowo istotnych wydarzeń, 
które mogą wywołać zdecydowaną reakcję rynku.

Jeżeli informacja ma niewielkie znaczenie dla jednej sesji lub dostępne dane nie pozwalają wiarygodnie 
określić kierunku reakcji, wybierz "Neutralny".

KROK 3 - UZASADNIENIE

Przygotuj uzasadnienie składające się z dokładnie dwóch zdań.

Wyjaśnij najważniejszy mechanizm wpływu wiadomości na złoto oraz wskaż, 
dlaczego w aktualnych warunkach rynkowych przewidywany kierunek reakcji jest najbardziej prawdopodobny.

KROK 4 - FORMAT ODPOWIEDZI

Zwróć wyłącznie poprawny składniowo obiekt JSON o następującej strukturze:

{
  "forecast": "jedna z pięciu dozwolonych wartości",
  "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
}

Przed zwróceniem odpowiedzi sprawdź poprawność JSON, zgodność prognozy z dozwolonymi wartościami oraz to, czy 
uzasadnienie zawiera dokładnie dwa zdania.

Nie dodawaj komentarzy, źródeł, linków, dodatkowych pól ani tekstu poza obiektem JSON.
Nie używaj Markdown ani bloków kodu.

Analiza ma charakter wyłącznie edukacyjny i informacyjny.
"""

silver_prompt_headline = """Otrzymasz pojedynczy nagłówek wiadomości dotyczący wydarzenia,
które może mieć wpływ na cenę srebra (XAG/USD).

Twoim zadaniem jest określenie najbardziej prawdopodobnego kierunku reakcji ceny srebra w ciągu jednej sesji
giełdowej od publikacji wiadomości.

KROK 1 - ANALIZA INFORMACJI I KONTEKSTU RYNKOWEGO

Zinterpretuj wydarzenie opisane w nagłówku i oceń jego potencjalny wpływ na cenę srebra.

Jeżeli masz dostęp do internetu, zweryfikuj wydarzenie i uzupełnij analizę o aktualne dane rynkowe.

Uwzględnij przede wszystkim:

- Globalny popyt przemysłowy i inwestycyjny na srebro.
- Popyt ze strony fotowoltaiki, elektroniki, elektromobilności i innych sektorów technologicznych.
- Podaż srebra z kopalń i recyklingu oraz sytuację na globalnym rynku srebra.
- Zapasy srebra, w szczególności COMEX i LBMA, oraz przepływy kapitału do funduszy ETF.
- Politykę FED i oczekiwania dotyczące stóp procentowych.
- Kurs USD i indeks DXY.
- Rentowności amerykańskich obligacji, szczególnie realne.
- Kondycję gospodarki światowej, szczególnie przemysłu Chin i USA.
- Relację ceny złota do srebra (Gold/Silver Ratio).
- Ryzyko geopolityczne i inne czynniki istotne dla analizowanego wydarzenia.

Nie musisz uwzględniać wszystkich wymienionych czynników. Skoncentruj się na tych,
które rzeczywiście mogą wpłynąć na krótkoterminową cenę srebra.

Oceń:

- Znaczenie i wiarygodność informacji.
- Jej nowość oraz stopień zaskoczenia rynku.
- Czy rynek zdążył już uwzględnić ją w cenie srebra.
- Potencjalny mechanizm wpływu na srebro, zarówno przez popyt przemysłowy, jak i inwestycyjny lub podaż.
- Aktualną sytuację rynkową i możliwe przeciwstawne czynniki.

Nie dopisuj niepotwierdzonych informacji. Preferuj wiarygodne i aktualne źródła,
w szczególności źródła pierwotne.

KROK 2 - PROGNOZA REAKCJI RYNKU

Oceń najbardziej prawdopodobną rzeczywistą reakcję ceny XAG/USD w ciągu jednej sesji giełdowej od
publikacji wiadomości.

Wybierz dokładnie jedną z poniższych wartości:

- "Silny spadek"
- "Spadek"
- "Neutralny"
- "Wzrost"
- "Silny wzrost"

Nie utożsamiaj teoretycznego wpływu informacji z rzeczywistą reakcją rynku. Uwzględnij jej znaczenie,
aktualny kontekst rynkowy, stopień zdyskontowania oraz możliwe przeciwstawne czynniki.

Pamiętaj, że srebro jest jednocześnie metalem szlachetnym i surowcem przemysłowym.
Dlatego uwzględnij zarówno wpływ nastrojów inwestycyjnych i sytuacji na rynku metali szlachetnych,
jak i oczekiwań dotyczących globalnej koniunktury oraz popytu przemysłowego.

Kategorie "Silny spadek" i "Silny wzrost" stosuj wyłącznie w przypadku wyjątkowo istotnych wydarzeń,
które mogą wywołać zdecydowaną reakcję rynku.

Jeżeli informacja ma niewielkie znaczenie dla jednej sesji lub dostępne dane nie pozwalają wiarygodnie
określić kierunku reakcji, wybierz "Neutralny".

KROK 3 - UZASADNIENIE

Przygotuj uzasadnienie składające się z dokładnie dwóch zdań.

Wyjaśnij najważniejszy mechanizm wpływu wiadomości na srebro oraz wskaż,
dlaczego w aktualnych warunkach rynkowych przewidywany kierunek reakcji jest najbardziej prawdopodobny.

KROK 4 - FORMAT ODPOWIEDZI

Zwróć wyłącznie poprawny składniowo obiekt JSON o następującej strukturze:

{
  "forecast": "jedna z pięciu dozwolonych wartości",
  "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
}

Przed zwróceniem odpowiedzi sprawdź poprawność JSON, zgodność prognozy z dozwolonymi wartościami oraz to,
czy uzasadnienie zawiera dokładnie dwa zdania.

Nie dodawaj komentarzy, źródeł, linków, dodatkowych pól ani tekstu poza obiektem JSON.
Nie używaj Markdown ani bloków kodu.

Analiza ma charakter wyłącznie edukacyjny i informacyjny.
"""
