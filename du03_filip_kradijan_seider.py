from json import load, dump
from pyproj import Transformer
from math import sqrt
from argparse import ArgumentParser

def parse() -> ArgumentParser.parse_args:
    """Do proměnné typu ArgumentParser.parse_args přiřazuje parametry programu, ty mohou být zadány v 
    libovolném pořadí, pokud některé nejsou zadány, program je hledá ve složce, ve které se nachází."""
    parser = ArgumentParser()
    parser.add_argument('-a', action = 'store', nargs ='?', default = 'adresy.geojson', dest = 'addresses')        # argument -a <názevSouboru> pro soubor s adresami
    parser.add_argument('-k', action = 'store', nargs ='?', default = 'kontejnery.geojson', dest = 'containers')       # argument -k <názevSouboru> pro soubor s kontejnery
    return parser.parse_args()

def pointDistance(points1 : tuple, points2 : list) -> float:
    """Vrací 2D vzdálenost bodů v S-JTSK vypočítanou pomocí Pythagorovy věty zaokrouhlenou na celé metry."""
    return round(sqrt((points1[0] - points2[0])**2 + (points1[1] - points2[1])**2))

def inputProcessing(addressFile : str, containerFile : str, outputFile : str):
    """Kontroluje existenci souborů, právo s nimi pracovat, formát a použitelnost dat. Určuje nejbližší kontejner pro 
    každý adresní bod. Vrací seznamy s nejbližšími vzdálenostmi a adresami, ke kterým se vztahují."""
    try:
        with open(addressFile, encoding = 'utf-8') as a,\
        open(containerFile, encoding ='utf-8') as c,\
        open(outputFile, 'w' ,encoding = 'utf-8') as o:

            try:        # testování souboru s adresními body
                aJSON = load(a)     # převod souborů do formátu JSON

                if len(aJSON['features']) == 0:
                    raise SystemExit('Soubor s adresními body neobsahuje žádné záznamy.')
            
                for addressPoint in aJSON['features']:      # kontrola správnosti dat pro každý adresní bod, pokud nejsou všechny adresní body správné, program bude ukočen
                    try:
                        tmp = addressPoint['properties']['addr:street'][0]      # kontrola správnosti ulice
                        tmp = [int(i) for i in addressPoint['geometry']['coordinates']]     # kontrola správnosti souřadnic
                    except Exception:
                        raise SystemExit('Chyba v adresním bodě s identifikátorem: ' + str(addressPoint['properties']['@id']) + '.')
            except Exception as e:      # jiná chyba v souboru s adresními body
                raise SystemExit(f'Neočekávaná chyba v souboru s adresními body: {e}.')
            
            try:        # testování souboru s kontejnery
                cJSON = load(c)
                if len(cJSON['features']) == 0:
                    raise SystemExit('Soubor s kontejnery neobsahuje žádné záznamy.')
            except Exception as e:
                print(f'Neočekávaná chyba v souboru s kontejnery: {e}.')
            else:       # výpočet vzdáleností, pokud kontroly proběhly úspěšně

                privateContainers = []      # vytvoření proměnných potřebných pro práci s kontejnery
                publicContainers = []
                cFeaturesLen = len(cJSON['features'])

                for container in cJSON['features']:     # rozdělení korektních kontejnerů na volně přístupné a určené obyvatelům dané adresy
                    try:
                        tmp = float(container['properties']['ID'])      # kontrola, zda je indentifikátor číslem
                        tmp = container['properties']['STATIONNAME'][0]     # kontrola správnosti ulice
                        tmp = [int(i) for i in container['geometry']['coordinates']]        # kontrola správnosti souřadnic
                    except Exception:
                        pass
                    else:       # rozdělení korektních kontejnerů do seznamů pro volně přístupné kontejnery / pro obyvatele domu
                        containerExtract = {'coordinates' : [float(i) for i in container['geometry']['coordinates']],
                            'ID' : container['properties']['ID'],
                            'STATIONNAME' : container['properties']['STATIONNAME']}
                        if container['properties']['PRISTUP'] == 'obyvatelům domu':
                            privateContainers.append(containerExtract)
                        elif container['properties']['PRISTUP'] == 'volně':
                            publicContainers.append(containerExtract)

                privateContLen = len(privateContainers)
                publicContLen = len(publicContainers)
                if (privateContLen + publicContLen) == 0:       # ukončení programu, pokud neexistují kontejnery se správnými daty
                    raise SystemExit('Neexistuje kontejner s korektními atributy, ukončení programu.')

                nearestDistances = []       # vytvoření proměnných pro výpočet nejbližších kontejnerů 
                nearestAddresses = []
                addressPoints = aJSON['features']
                wgsToSjtsk = Transformer.from_crs(4326, 5514, always_xy= True)

                for addressPoint in addressPoints:      # práce s každým adresním bodem
                    distance = -1
                    address = (addressPoint['properties']['addr:street'] + ' ' + str(addressPoint['properties']['addr:housenumber'])).strip()

                    for privateCntnr in privateContainers:      # určení, zda pro adresu existuje soukromý kontejner se stejnou adresou
                        if privateCntnr['STATIONNAME'].strip() == address:
                            distance = 0
                            addressPoint.update({'kontejner' : privateCntnr['ID']})
                            nearestAddresses.append(address)
                            nearestDistances.append(distance)
                            break

                    if distance == 0:
                        continue

                    # určení nejbližšího veřejného kontejneru, pokud pro adresu neexistuje soukromý
                    if publicContLen == 0:      # ukončení programu, pokud adrese nelze přiřadit kontejner
                        ID = addressPoint['properties']['@id']
                        raise SystemExit(f"""Adresnímu bodu s identifikátorem {ID} nemohl být přiřazen kontejner,\
vstup neobsahuje veřejně přístupné kontejnery a pro adresu neexistuje soukromý kontejner. Ukončení programu.""")     

                    # vytvoření proměnných pro práci s konkrétní adresou:
                    SJTSK = wgsToSjtsk.transform(addressPoint['geometry']['coordinates'][0], addressPoint['geometry']['coordinates'][1])       
                    lowestDistance = -1

                    for publicCntnr in publicContainers:        # určení minimální vzdálenosti pro daný adresní bod
                        currentDistance = pointDistance(SJTSK, publicCntnr['coordinates'])
                        if (lowestDistance == -1) or (currentDistance < lowestDistance):
                            lowestDistance = currentDistance
                            lowestID = publicCntnr['ID']

                    if lowestDistance > 10000:     # ukončení programu, pokud nejbližší vzdálenost > 10 km
                        raise SystemExit('Překročena prahová vzdálenost nejbližšího kontejneru 10 km, ukončení programu.')
                    nearestDistances.append(lowestDistance)        # přidání nejnižší vzdálenosti do seznamu nejnižších vzdáleností
                    nearestAddresses.append(address)        # přidání adresy adresního bodu do seznamu adres
                    addressPoint.update({'kontejner' : lowestID})        # přidání identifikátoru nejbližšího kontejneru do záznamu adresního bodu

                with open(outputFile, 'w' ,encoding = 'utf-8') as output:       # uložení adresních bodů s identifikátory nejbližšího kontejnerů do výstupního souboru
                    dump(addressPoints, output, ensure_ascii = False, indent = 4)

                print(f'Načteno a zpracováno {len(addressPoints)} adresních bodů.')     # výpisy o počtu bodů
                print(f'Z {cFeaturesLen} načtených kontejnerů bylo zpracováno {len(privateContainers) + len(publicContainers)} korektních kontejnerů.')
                return nearestDistances, nearestAddresses
    except FileNotFoundError as e:
        print(f'Vstupní soubor neexistuje: {e}.')
    except PermissionError as e:
        print(f'Program nemá právo pracovat se vstupním souborem: {e}.')
    except OSError as e:
        print(f'Neočekávaná chyba vyvolaná Vaším počítačem: {e}.')
    except Exception as e:
        print(f'Neočekávaná neznámá chyba: {e}.')

def findMaximum(distList : list) -> list:
    """Do seznamu vloží maximum nejbližší vzdálenosti ke kontejneru a její index v seznamu vzdáleností."""
    maximum = [distList[0], 0]
    distListLen = len(distList)
    if distListLen > 1:
        for i in range(1, distListLen):
            if distList[i] > maximum[0]:
                maximum = [distList[i], i]
    return maximum

def median(distList : list, listLen : int) -> None:
    """Počítá a vypisuje medián vzdálenosti k nejbližšímu kontejneru."""
    distList.sort()
    mid = listLen // 2
    if listLen % 2 == 0:        # výpočet v závislosti na sudém / lichém počtu vzdáleností
        median = (distList[mid - 1] + distList[mid]) // 2
    else:
        median = distList[mid]
    print(f'Medián průměrné vzdálenosti k nejbližšímu kontejneru je {median} m.')

def statistics(distances : list, addresses : list) -> None:
    """S využitím podfunkcí vypisuje průměrnou vzdálenost a medián vzdálenosti k nejbližšímu 
    kontejneru a adresu, pro kterou je vzdálenost k nejbližšímu kontejneru nejvyšší."""
    length = len(distances)
    if length == 1:
        print('Vzdálenost k nejbližšímu kontejneru byla vypočtena pouze pro 1 adresu, výsledek nelze s ničím porovnávat.')
    print(f'Průměrná vzdálenost k nejbližšímu kontejneru je {sum(distances) // len(distances)} m.')

    maximum = findMaximum(distances)
    print(f'Maximální vzdálenost k nejbližšímu kontejneru je {maximum[0]} m a to z adresy {maximum[1]}.')
    median(distances, length)

args = parse()
try:        # prevence pádu pro případ neexistence souboru "adresy.geojson" nebo "kontejnery.geojson" pokud nebyl zadán odpovídající parametr souboru
    dists, addrs = inputProcessing(args.addresses, args.containers, 'adresy_kontejnery.geojson')
    statistics(dists, addrs)
except TypeError as e:
    print('Alespoň jeden z výchozích vstupních souborů neexistuje.')