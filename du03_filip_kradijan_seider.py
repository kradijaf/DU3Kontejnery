from json import load, dump
from pyproj import Transformer
from math import sqrt
from argparse import ArgumentParser, Namespace

def fileControl(addrFile : str, contFile : str, outFile : str):
    """Kontroluje existenci souborů, právo s nimi pracovat, formát a použitelnost dat. 
    Pokud jsou vstupní soubory v pořádku, vrací je načtené do jakožto JSON"""
    try:
        with open(addrFile, encoding = 'utf-8') as a,\
        open(contFile, encoding ='utf-8') as c,\
        open(outFile, 'w', encoding = 'utf-8') as o:

            try:        # testování souboru s adresními body
                addrJSON = load(a)     # převod souborů do formátu JSON
            except Exception as e:      # chyba v souboru s adresními body, např. jedná se o .CSV
                raise SystemExit(f'Neočekávaná chyba v souboru s adresními body: {e}.')

            try:        # testování souboru s kontejnery
                contJSON = load(c)
            except Exception as e:
                raise SystemExit(f'Neočekávaná chyba v souboru s kontejnery: {e}.')

    except FileNotFoundError as e:
        raise SystemExit(f'Vstupní soubor neexistuje: {e}.')
    except PermissionError as e:
        raise SystemExit(f'Program nemá právo pracovat se vstupním souborem: {e}.')
    except OSError as e:
        raise SystemExit(f'Neočekávaná chyba vyvolaná Vaším počítačem: {e}.')
    except Exception as e:
        raise SystemExit(f'Neočekávaná neznámá chyba: {e}.')
    return addrJSON, contJSON

def dataControl(addrJSON : dict, contJSON : dict):
    """Kontroluje správnost dat ve vstupních souborech, případně rozdělí kontejnery na veřejné a soukromé, 
    které vrátí s počtem záznamů v souboru s kontejnery a počtem veřejných kontejnerů."""
    if len(addrJSON['features']) == 0:      # ukončení programu, pokud soubor neobsahuje záznamy 
        raise SystemExit('Soubor s adresními body neobsahuje žádné záznamy.')
    if len(contJSON['features']) == 0:
        raise SystemExit('Soubor s kontejnery neobsahuje žádné záznamy.')

    for addressPoint in addrJSON['features']:      # kontrola správnosti dat pro každý adresní bod, pokud nejsou všechny adresní body správné, program bude ukočen
        try:
            tmp = addressPoint['properties']['addr:street'][0]      # kontrola správnosti ulice
            tmp = [int(i) for i in addressPoint['geometry']['coordinates']]     # kontrola správnosti souřadnic
        except Exception:
            raise SystemExit('Chyba v adresním bodě s identifikátorem: ' + str(addressPoint['properties']['@id']) + '.')

    privateConts = []       # vytvoření proměnných potřebných pro práci s kontejnery       
    publicConts = []          
    contCount = len(contJSON['features'])

    for container in contJSON['features']:     # rozdělení korektních kontejnerů na volně přístupné a určené obyvatelům dané adresy
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
                privateConts.append(containerExtract)
            elif container['properties']['PRISTUP'] == 'volně':
                publicConts.append(containerExtract)

    privateContCount = len(privateConts)
    publicContCount = len(publicConts)
    if (privateContCount + publicContCount) == 0:       # ukončení programu, pokud neexistují kontejnery se správnými daty
        raise SystemExit('Neexistuje kontejner s korektními atributy, ukončení programu.')

    return contCount, publicContCount, privateConts, publicConts

def pointDistance(points1 : tuple, points2 : list) -> float:
    """Vrací 2D vzdálenost bodů v S-JTSK vypočítanou pomocí Pythagorovy věty zaokrouhlenou na celé metry."""
    return round(sqrt((points1[0] - points2[0])**2 + (points1[1] - points2[1])**2))

def containerAllocation(addresses : dict, publicContainerCount : int, privateConts : list, publicConts: list):
    """Přiřazuje adresám nejbližší kontejner, pokud je možné každé adrese nějaký přiřadit, vrací slovník adresních 
    bodů rozšířených o nejbližší kontejner, seznamy s nejnižšími vzdálenostmi a jim odpovídajícími adresami."""
    nearestDists = []       # vytvoření proměnných pro výpočet nejbližších kontejnerů 
    nearestAddrs = []
    wgsToSjtsk = Transformer.from_crs(4326, 5514, always_xy= True)

    for addressPoint in addresses:      # práce s každým adresním bodem
        distance = -1
        address = (addressPoint['properties']['addr:street'] + ' ' + str(addressPoint['properties']['addr:housenumber'])).strip()

        for privateCntnr in privateConts:      # určení, zda pro adresu existuje soukromý kontejner se stejnou adresou
            if privateCntnr['STATIONNAME'].strip() == address:
                distance = 0
                addressPoint.update({'kontejner' : privateCntnr['ID']})
                nearestAddrs.append(address)
                nearestDists.append(distance)
                break

        if distance == 0:
            continue
                # určení nejbližšího veřejného kontejneru, pokud pro adresu neexistuje soukromý:
        if publicContainerCount == 0:      # ukončení programu, pokud adrese nelze přiřadit kontejner
            ID = addressPoint['properties']['@id']
            raise SystemExit(f"""Adresnímu bodu s identifikátorem {ID} nemohl být přiřazen kontejner,\
vstup neobsahuje veřejně přístupné kontejnery a pro adresu neexistuje soukromý kontejner. Ukončení programu.""")     
                # vytvoření proměnných pro práci s konkrétní adresou:
        SJTSK = wgsToSjtsk.transform(addressPoint['geometry']['coordinates'][0], addressPoint['geometry']['coordinates'][1])       
        lowestDistance = -1

        for publicCntnr in publicConts:        # určení minimální vzdálenosti pro daný adresní bod
            currentDistance = pointDistance(SJTSK, publicCntnr['coordinates'])
            if (lowestDistance == -1) or (currentDistance < lowestDistance):
                lowestDistance = currentDistance
                lowestID = publicCntnr['ID']

        if lowestDistance > 10000:     # ukončení programu, pokud nejbližší vzdálenost > 10 km
            raise SystemExit('Překročena prahová vzdálenost nejbližšího kontejneru 10 km, ukončení programu.')
        nearestDists.append(lowestDistance)        # přidání nejnižší vzdálenosti do seznamu nejnižších vzdáleností
        nearestAddrs.append(address)        # přidání adresy adresního bodu do seznamu adres
        addressPoint.update({'kontejner' : lowestID})        # přidání identifikátoru nejbližšího kontejneru do záznamu adresního bodu
    return addresses, nearestDists, nearestAddrs

def outputs(outFile : str, addresses : dict, contCount : int, privateContsCount : int, publicContsCount : int) -> None:
    """Do výstupního souboru vkládá na JSON převedený slovník s adresními body a ID jejich nejbližšího kontejneru,
    vypisuje počty načtených a zpracovaných bodů."""
    with open(outFile, 'w' ,encoding = 'utf-8') as output:       # uložení adresních bodů s identifikátory nejbližšího kontejneru do výstupního souboru
        dump(addresses, output, ensure_ascii = False, indent = 2)
    print(f'Načteno a zpracováno {len(addresses)} adresních bodů.')     # výpisy o počtu bodů
    print(f'Z {contCount} načtených kontejnerů bylo zpracováno {privateContsCount + publicContsCount} korektních kontejnerů.')

def inputProcessing(addressFile : str, containerFile : str, outputFile : str):
    """Kontroluje vstupní soubory, určuje nejbližší kontejner pro každý adresní bod. Vrací seznamy s 
    nejbližšími vzdálenostmi a adresami, ke kterým se vztahují a vypisuje informace počtu vstupních záznamů. 
    Vrací seznamy s nejnižšími vzdálenostmi a jim odpovídajícími adresami."""
    aJSON, cJSON = fileControl(addressFile, containerFile, outputFile)      
    containerCount, publicContsCount, privateContainers, publicContainers = dataControl(aJSON, cJSON)
    addressPoints, nearestDistances, nearestAddresses = containerAllocation(aJSON['features'], publicContsCount, privateContainers, publicContainers)
    outputs(outputFile, addressPoints, containerCount, len(privateContainers), len(publicContainers))

    return nearestDistances, nearestAddresses

def findMaximum(distList : list, addrList : list) -> list:
    """Do seznamu vloží maximum nejbližší vzdálenosti ke kontejneru a její index v seznamu vzdáleností."""
    maximum = [distList[0], 0]
    distListLen = len(distList)
    if distListLen > 1:
        for i in range(1, distListLen):
            if distList[i] > maximum[0]:
                maximum = [distList[i], addrList[i]]
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

    maximum = findMaximum(distances, addresses)
    print(f'Maximální vzdálenost k nejbližšímu kontejneru je {maximum[0]} m a to z adresy {maximum[1]}.')
    median(distances, length)

def parse() -> Namespace:
    """Do proměnné typu argparse.Namespace přiřazuje parametry programu, ty mohou být zadány v 
    libovolném pořadí, pokud některé nejsou zadány, program je hledá ve složce, ve které se nachází."""
    parser = ArgumentParser()
    parser.add_argument('-a', action = 'store', nargs ='?', default = 'adresy.geojson', dest = 'addresses')        # argument -a <názevSouboru> pro soubor s adresami
    parser.add_argument('-k', action = 'store', nargs ='?', default = 'kontejnery.geojson', dest = 'containers')       # argument -k <názevSouboru> pro soubor s kontejnery
    
    return parser.parse_args()

try:
    args = parse()
    dists, addrs = inputProcessing(args.addresses, args.containers, 'adresy_kontejnery.geojson')
    statistics(dists, addrs)
except OSError as e:
    print(f'Neočekávaná chyba vyvolaná Vaším počítačem: {e}.')
except KeyboardInterrupt as e:
    print('Program ukončen uživatelem.')
except Exception as e:
    print(f'Neočekávaná chyba: {e}.')