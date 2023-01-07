## **Uživatelská dokumentace**

Program vyžaduje 2 vstupní soubory zastupující adresní body a kontejnery.
### Adresní body:
- **formát:** .GEOJSON
- **souřadnicový systém:** World Geodetic System 1984 (WGS84)(EPSG: 4326)
- **požadované atributy:** `název ulice` (properties\addr:street), `domovní číslo` (properties\addr:housenumber), `souřadnice` (geometry\coordinates), `identifikátor` (properties\\@id)

### Kontejnery:
- **formát:** .GEOJSON
- **souřadnicový systém:** Systém jednotné trigonometrické sítě katastrální (S–JTSK)(EPSG: 5514)
- **požadované atributy:** `adresa` (properties\STATIONNAME), `souřadnice` (geometry\coordinates), `identifikátor` (properties\ID), `přístup ke kontejneru` (properties\PRISTUP)

Program lze spustit přes příkazový řádek pomocí příkazu `python <NázevProgramu.py> -a <názevVstupníhoSouboruAdres.geojson> -k <názevVstupníhoSouboruAdres.geojson>`. Parametr `-a` se vztahuje k souboru s adresními body, parametr `-k` se vztahuje k souboru s kontejnery, parametry mohou být uvedeny v libovolném pořadí. Pokud tyto soubory nejsou uvedeny, program hledá ve své složce soubory `adresy.geojson` a `kontejnery.geojson`, pokud programu chybí některý ze vstupních souborů, nebude dále pokračovat.

Pokud se všemi adresními body lze pracovat a každému bodu přiřadit nejbližší kontejner, program to vykoná, v opačném případě bude ukončen. Program vypisuje následující informace o vstupních souborech:
- počet načtených (= zpracovaných) adresních bodů
- počet načtených kontejnerů a počet z nich zpracovaných (= kolik záznamů použitelných pro výpočty soubor obsahoval)

Dále program vypisuje následující statistiky o zpracovaných datech (veškeré vzdálenosti jsou zaokrouhleny na m):
- průměrnou vzdálenost mezi adresním bodem a nejbližším kontejnerem
- maximální vzdálenost k nejbližšímu kontejneru a adresu, ke které se vzdálenost vztahuje
- medián vzdálenosti mezi adresním bodem a nejbližším kontejnerem

Program ve své složce vytváří soubor `adresy_kontejnery.geojson` obsahující všechny adresní body a rozšířený o atribut `kontejner` obsahující hodnotu atributu `ID` nejbližšího kontejneru.

## **Vývojářská dokumentace**

Program je rozdělen do hlavních funkcí `inputProcessing()` a `statistics()`. Ty pro přehlednost využívají podfunkce. 
Funkce `inputProcessing()` začíná funkcí `fileControl()`, ta kontroluje následující:
- zda zadané soubory existují
- má-li program právo s nimi pracovat

Následně podfunkce `dataControl()` určuje správnost dat následovně:
- zda v obou souborech s daty potřebnými pro výpočet existuje alespoň 1 záznam
- jsou-li veškeré adresní body v pořádku (položky `ulice`, `domovní číslo` a `souřadnice`)
> Program vyžaduje správnost všech adresních bodů, protože v části zadání "Přiřazení kontejnerů k adresám (2 b)" je uvedeno, že výstupní soubor má obsahovat veškeré adresní body a ke každému z nich přiřazený identifikátor nejbližšího kontejneru.
Dále vybírá kontejnery, použitelné pro výpočet, rozděluje je do seznamů pro soukromé/veřejné. Pokud s žádným kontejnerem nelze pracovat (nesprávnost adresy a souřadnic), program je ukončen.  

Podfunkce `containerAllocation()` prochází adresy cyklem. Nejprve cyklem v seznamu soukromých kontejnerů hledá, zda pro adresu nějaký existuje, v takovém případě je výsledná vzdálenost 0. Pokud pro adresu soukromý kontejner neexistuje, cyklem hledá nejbližší veřejný. Pokud neexistují veřejné, pro výpočet použitelné, kontejnery, nastane ukončení programu. Případná vzdálenost adresa–kontejner je počítána ze souřadnic převedených do S–JTSK pomocí Pythagorovy věty a je zaokrouhlena na celé m. Pro adresu je vypočítána vzdálenost ke každému veřejnému kontejneru, dále program uchovává minimální hodnotu a odpovídající adresu do seznamů min. vzdáleností a adres. Pokud je minimální vzdálenost delší 10 km, nastane ukončení programu.  

Podfunkce `outputs()` vytváří výstupní soubor `adresy_kontejnery` ve formátu `.GEOJSON`, ten obsahuje veškeré adresní body a v atributu "kontejner" ID nejbližšího kontejneru. Také vypisuje, kolik adresních bodů a kontejnerů bylo načteno a zpracováno.

Funkce `statistics()` pomocí podfunkcí `findMax()` a `median()` následně z výstupních seznamů funkce `inputProcessing()` určuje a vypisuje výše zmíněné statistiky.

## **Použité zdroje**
https://stackoverflow.com/questions/42756537/f-string-syntax-for-unpacking-a-list-with-brace-suppression
