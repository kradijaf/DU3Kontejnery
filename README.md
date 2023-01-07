## **Uživatelská dokumentace**

Program vyžaduje 2 vstupní soubory, adresní body a kontejnery.
> adresní body:
- **formát:** .GEOJSON
- **souřadnicový systém:** WGS84 (EPSG: 4326)
- **požadované atributy:** `název ulice` (properties\addr:street), `domovní číslo` (properties\addr:housenumber), `souřadnice` (geometry\coordinates), `identifikátor` (properties\@id)

Program lze díky funkce `parse` spustit přes příkazový řádek pomocí příkazu `python <NázevProgramu.py> -a <názevVstupníhoSouboruAdres.geojson> -k <názevVstupníhoSouboruAdres.geojson>`. Parametr `-a` se vztahuje k souboru s adresními body, parametr `-k` se vztahuje k souboru s kontejnery, parametry mohou být uvedeny v libovolném pořadí. Pokud tyto soubory nejsou uvedeny, program hledá ve své složce soubory `adresy.geojson` a `kontejnery.geojson`, pokud programu chybí některý ze vstupních souborů, nebude dále pokračovat.

Pokud se všemi adresními body lze pracovat a každému bodu přiřadit nejbližší kontejner, program to vykoná, v opačném případě bude ukončen. Program vypisuje následující informace o vstupních souborech:
- počet načtených (=zpracovaných) adresních bodů
- počet načtených kontejnerů a počet z nich zpracovaných (= kolik záznamů použitelných pro výpočty soubor obsahoval)

Dále program vypisuje následující statistiky o zpracovaných datech (veškeré vzdálenosti jsou zaokrouhleny na m):
- průměrnou vzdálenost mezi adresním bodem a nejbližším kontejnerem
- maximální vzdálenost k nejbližšímu kontejneru a adresu, ke které se vzdálenost vztahuje
- medián vzdálenosti mezi adresním bodem a nejbližším kontejnerem

Program ve své složce vytváří soubor `adresy_kontejnery.geojson` obsahující všechny adresní body a rozšířený o atribut `kontejner` obsahující hodnotu atributu `ID` nejbližšího kontejneru.

## **Vývojářská dokumentace**

Kvůli efektivitě program neobsahuje samostanou funkci pro kontrolu vstupů, kontroly vstupních souborů jsou prováděny na začátku funkce `inputProcessing()`, kontroly správnosti ve chvíli, kdy je s nimi potřeba pracovat. 

Kontrola nejprve ověřuje následující:
- zda zadané soubory existují
- má-li program právo s nimi pracovat
- jsou-li veškeré adresní body v pořádku (položky `ulice`, `domovní číslo` a `souřadnice`)
- zda v obou souborech s daty potřebnými pro výpočet existuje alespoň 1 záznam
> Program vyžaduje správnost všech adresních bodů, protože v části zadání "Přiřazení kontejnerů k adresám (2 b)" je uvedeno, že výstupní soubor má obsahovat veškeré adresní body a ke každému z nich přiřazený identifikátor  nejbližšího kontejneru.

V průběhu výpočtů funkce `inputProcessing()` program nejprve kontroluje kontejnery, pokud jsou použitelné pro výpočet, rozděluje je do seznamů pro soukromé/veřejné. Pokud s žádným kontejnerem nelze pracovat (nesprávnost adresy a souřadnic), program je ukončen. Následně si program do seznamu `addressPoints()` uloží adresní body a prochází je cyklem. Nejprve cyklem v seznamu soukromých kontejnerů hledá, zda pro adresu nějaký existuje, v takovém případě je výsledná vzdálenost 0. Pokud pro adresu soukromý kontejner neexistuje a neexistují veřejné, pro výpočet použitelné, kontejnery, nastane ukončení programu. Pokud existují použitelné veřejné kontejnery, vzdálenost adresa–kontejner se počítá z souřadnic převedených do S–JTSK pomocí Pythagorovy věty a zaokrouhluje na celé m. Pro adresu je vypočítána vzdálenost ke každému veřejnému kontejneru, vzdálenost a indentifikátor příslušného kontejneru jsou uloženy každá do samostatného seznamu. Poté je vybrána minimální hodnota ze seznamu vzdáleností a identifikátor odpovídající indexu minima. Pokud je minimální vzdálenost delší 10 km, nastane ukončení programu. Program pro výběr min. vzdálenosti používá funkci `min()`, ta vrací první nejnižší hodnotu, nikoliv všechny její výskyty, proto je zanedbán nepravděpodobný případ, kdy by pro adresu existovala min. vzdálenost s přesností na m pro více kontejnerů. Po cyklu počítajícím vzdálenosti pro každý adresní bod je vytvořen výstupní soubor. 

Funkce `statistics()` pomocí podfunkcí `findMax()` a `Median()` následně z výstupních seznamů funkce `inputProcessing()` určuje a vypisuje výše zmíněné statistiky.

## **Použité zdroje**
https://stackoverflow.com/questions/42756537/f-string-syntax-for-unpacking-a-list-with-brace-suppression
