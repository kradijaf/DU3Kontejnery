## **Uživatelská dokumentace**

Program vyžaduje 2 vstupy formátu .geoJSON - adresní body a kontejnery. Program lze spustit pomocí příkazového řádku pomocí příkazu `python <NázevProgramu.py> -a <názevVstupníhoSouboruAdres.geojson> -k <názevVstupníhoSouboruAdres.geojson>`. Parametr `-a` se vztahuje k souboru s adresními body, parametr `-k` se vztahuje k souboru s adresními body, mohou být uvedeny v libovoolném pořadí. Pokud tyto soubory nejsou uvedeny, program hledá ve své složce soubory `adresy.geojson` a `kontejnery.geojson`, pokud programu chybí některý ze vstupních souborů, nebude dále pokračovat.

Pokud se všemi adresními body lze pracovat a každému bodu přiřadit nejbližší kontejner, program to vykoná, v opačném případě bude ukončen. Program vypisuje následující informace o vstupních souborech:
-počet načtených (=zpracovaných) adresních bodů
- počet načtených kontejnerů a počet z nich zpracovaných zpracoval (= kolik záznamů použitelných pro výpočty soubor obsahoval)

