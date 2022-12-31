## **Uživatelská dokumentace**

Program vyžaduje 2 vstupy formátu .geoJSON - adresní body a kontejnery. Program lze spustit přes příkazový řádek pomocí příkazu `python <NázevProgramu.py> -a <názevVstupníhoSouboruAdres.geojson> -k <názevVstupníhoSouboruAdres.geojson>`. Parametr `-a` se vztahuje k souboru s adresními body, parametr `-k` se vztahuje k souboru s kontejnery, parametry mohou být uvedeny v libovolném pořadí. Pokud tyto soubory nejsou uvedeny, program hledá ve své složce soubory `adresy.geojson` a `kontejnery.geojson`, pokud programu chybí některý ze vstupních souborů, nebude dále pokračovat.

Pokud se všemi adresními body lze pracovat a každému bodu přiřadit nejbližší kontejner, program to vykoná, v opačném případě bude ukončen. Program vypisuje následující informace o vstupních souborech:
- počet načtených (=zpracovaných) adresních bodů
- počet načtených kontejnerů a počet z nich zpracovaných (= kolik záznamů použitelných pro výpočty soubor obsahoval)

Dále program vypisuje následující statistiky o zpracovaných datech (veškeré vzdálenosti jsou zaokrouhleny na m):
- průměrnou vzdálenost mezi adresním bodem a nejbližším kontejnerem
- maximální vzdálenost k nejbližšímu kontejneru a adresu/adresy, ke nimž se vzdálenost vztahuje
- medián vzdálenosti mezi adresním bodem a nejbližším kontejnerem

Program ve své složce vytváří soubor `adresy_kontejnery.geojson` obsahující všechny adresní body a rozšířený o atribut `kontejner` obsahující hodnotu atributu `ID` nejbližšího kontejneru.

## **Vývojářská dokumentace**

Pokud zadané soubory existují, program má právo s nimi pracovat a veškéré adresní body jsou v pořádku (položky `ulice`, `domovní číslo` a `souřadnice`), program počítá vzdálenosti k nejbližšímu kontejneru.
> Program vyžaduje správnost všech adresních bodů, protože v části zadání "Přiřazení kontejnerů k adresám (2 b)" je uvedeno, že výstupní soubor má obsahovat veškeré adresní body a ke každému z nich přiřazený identifikátor  nejbližšího kontejneru.
Funkce `inputProcessing` nejprve kontroluje kontejnery, pokud jsou použitelné pro výpočet, rozděluje je do seznamů pro soukromé/veřejné. Pokud neexistují s kontejnery nelze pracovat (nesprávnost adresy a souřadnic), program je ukončen. Následně si program do seznamu `addressPoints` uloží adresní body a for cyklem je prochází. Nejdříve kontroluje, zda pro adresu existuje soukromý kontejner, v takovém případě je výsledná vzdálenost 0. Pokud pro adresu soukromý kontejner není a neexistují veřejné pro výpočet použitelné kontejnery, nastane ukončení programu. Pokud existují použitelné veřejné kontejnery, vzdálenost adresa - kontejner se počítá z souřadnic převedených do S-JTSK pomocí Pythágorovy věty a zaokrouhluje na celé m. Pro adresu je vypočítána vzdálenost ke každému veřejnému kontejneru, vzdálenost a indentifikátor příslušného kontejneru jsou uloženy každá do samostatného seznamu. Následně je vybrána minimální hodnota ze seznamu vzdáleností a identifikátor odpovídající indexu minima. Pokud je minimální vzdálenost delší 10 km, nastane ukončení programu. Program pro výběr min. vzdálenosti používá funkci min(), ta vrací první nejnižší hodnotu, nikoliv všechny její výskyty, proto je zanedbán nepravděpodobný případ, kdy by pro adresu existovala min. vzdálenost s přesností na m pro více kontejnerů. Po for cyklu počítajícím vzdálenosti pro každý adresní bod je vytvořen výstupní soubor. 

Funkce `statistics` pomocí podfunkcí `strMaximums`, `findMax`, `printMax` a `Median` následně z výstupních seznamů funkce `inputProcessing` určuje a vypisuje výše zmíněné statistiky.
