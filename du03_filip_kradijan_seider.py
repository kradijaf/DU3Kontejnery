from json import load, dump
from pyproj import Transformer
from math import sqrt
from argparse import ArgumentParser

def parse() -> ArgumentParser.parse_args:
    """Do proměnné parser přiřazuje parametry programu, ty mohou být zadány v libovolném pořadí, pokud některé nejsou zadány, 
    program je hledá ve složce, ve které se nachází."""
    parser = ArgumentParser()
    parser.add_argument('-a', action = 'store', nargs ='?', default = 'adresy.geojson', dest = 'addresses')        # argument -a <názevSouboru> pro soubor s adresami
    parser.add_argument('-k', action = 'store', nargs ='?', default = 'kontejnery.geojson', dest = 'containers')       # argument -k <názevSouboru> pro soubor s kontejnery
    return parser.parse_args()

def fileControl(addressFile : str, containerFile : str, outputFile : str) -> None:
    """Kontroluje existenci vstupních souborů, právo s jimi pracovat a správnost adresních bodů."""
    try:
        with open(addressFile, encoding= 'utf-8') as a,\
        open(containerFile, encoding='utf-8') as c,\
        open(outputFile, 'w' ,encoding = 'utf-8') as o:
            try:
                aJSON = load(a)
                cJSON = load(c)

                if len(aJSON['features']) == 0 or len(cJSON['features']) == 0:
                    print('Vstupní soubor neobsahuje žádné záznamy.')
                    return False

                for addressPoint in aJSON['features']:      # kontrola správnosti dat pro každý adresní bod, pokud nejsou všechny adresní body správné, program bude ukočen
                    try:
                        tmp = addressPoint['properties']['addr:street'][0]      # kontrola správnosti ulice
                        tmp = float(addressPoint['properties']['addr:housenumber'][0])      # kontrola správnosti domovního čísla
                        for i in addressPoint['geometry']['coordinates']:       # kontrola správnosti souřadnic
                            tmp = int(i)
                            if '-' in str(i):
                                raise ValueError
                    except Exception:
                        print('Chyba v adresním bodě s identifikátorem: ' + str(addressPoint['properties']['@id']) + '.')
                        return False
            except Exception as e:      # jiná chyba ve vstupech
                print(f'Neočekávaná chyba ve vstupních souborech: {e}.')
                return False
    except FileNotFoundError as e:
        print(f'Vstupní soubor neexistuje: {e}.')
    except PermissionError as e:
        print(f'Program nemá právo pracovat se vstupním souborem: {e}.')
    except OSError as e:
        print(f'Neočekávaná chyba vyvolaná Vaším počítačem: {e}.')
    except Exception as e:
        print(f'Neočekávaná neznámá chyba: {e}.')
    else:
        return True

def wgsToSjtsk(wgsCoords : list) -> tuple:
    """Převod souřadnic z WGS-84 do S-JTSK."""
    wgs2sjtsk = Transformer.from_crs(4326, 5514, always_xy= True)
    SJTSK = wgs2sjtsk.transform(wgsCoords[0], wgsCoords[1])
    return (SJTSK[0], SJTSK[1])

def pointDistance(points1 : list, points2 : list) -> float:
    """Výpočet 2D vzdálenosti bodů v S-JTSK pomocí Pythagorovy věty."""
    return round(sqrt((points1[0] - points2[0])**2 + (points1[1] - points2[1])**2))

def inputProcessing(addressFile : str, containerFile : str, outputFile : str):
    """Výpočet nejbližšího kontejneru pro každý adresní bod, výsledek ukládá do seznamu 
    pro nejbližší vzdálenost a adresu, ke které se vztahuje."""
    with open(addressFile, encoding= 'utf-8') as a,\
    open(containerFile, encoding='utf-8') as c:

        aJSON = load(a)     # převod souborů do formátu JSON
        cJSON = load(c)
        
        privateContainers = []      # vytvoření proměnných potřebných pro práci s kontejnery
        publicContainers = []
        cFeaturesLen = len(cJSON['features'])

        for container in cJSON['features']:     # rozdělení korektních kontejnerů na volně přístupné a určené obyvatelům dané adresy
            try:
                tmp = float(container['properties']['ID'])      # kontrola, zda je indentifikátor číslem
                tmp = container['properties']['STATIONNAME'][0]     # kontrola správnosti ulice
                for i in container['geometry']['coordinates']:      # kontrola správnosti souřadnic
                    tmp = int(i)
                    if '-' not in str(i):
                        raise ValueError
            except Exception:
                pass
            else:       # rozdělení korektních kontejnerů do seznamů pro volně přístupné kontejnery / pro obyvatele domu
                if container['properties']['PRISTUP'] == 'obyvatelům domu':
                    privateContainers.append({'coordinates' : [float(str(i).replace(' ', '')) for i in container['geometry']['coordinates']],
                                              'ID' : container['properties']['ID'],
                                              'STATIONNAME' : container['properties']['STATIONNAME']})
                elif container['properties']['PRISTUP'] == 'volně':
                    publicContainers.append({'coordinates' : [float(str(i).replace(' ', '')) for i in container['geometry']['coordinates']],
                                              'ID' : container['properties']['ID'],
                                              'STATIONNAME' : container['properties']['STATIONNAME']})

        privateContLen = len(privateContainers)
        publicContLen = len(publicContainers)
        if (privateContLen + publicContLen) == 0:       # ukončení programu, pokud neexistují kontejnery se správnými daty
            raise SystemExit('Neexistuje kontejner s korektními atributy, ukončení programu.')

        nearestDistances = []       # vytvoření proměnných pro určení nejbližších kontejnerů 
        nearestAddresses = []
        addressPoints = aJSON['features']

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
                
            if distance == -1:      # určení nejbližšího veřejného kontejneru, pokud pro adresu neexistuje soukromý
                if publicContLen == 0:      # ukončení programu, pokud adrese nelze přiřadit kontejner
                    ID = addressPoint['properties']['@id']
                    raise SystemExit(f'Adresnímu bodu s identifikátorem {ID} nemohl být přiřazen kontejner,\
 vstup neobsahuje veřejně přístupné kontejnery a pro adresu neexistuje soukromý kontejner. Ukončení programu.')     

                # vytvoření proměnných pro práci s konkrétním adresou:
                SJTSK = wgsToSjtsk([float(str(i).replace(' ', '')) for i in addressPoint['geometry']['coordinates']])       
                currentDistances = [] 
                currentIDs = []

                for publicCntnr in publicContainers:        # výpočet vzdálenosti pro každý veřejný kontejner
                    currentDistances.append(pointDistance(SJTSK, publicCntnr['coordinates']))
                    currentIDs.append(publicCntnr['ID'])

                minDist = min(currentDistances)     # určení minimální vzdálenosti
                if minDist > 10000:     # ukončení programu, pokud nejbližší vzdálenost > 10 km
                    raise SystemExit('Překročena prahová vzdálenost nejbližšího kontejneru 10 km, ukončení programu.')
                nearestDistances.append(minDist)        # přidání nejnižší vzdálenosti do seznamu nejnižších vzdáleností
                nearestAddresses.append(address)        # přidání adresy adresního bodu do seznamu adres
                addressPoint.update({'kontejner' : currentIDs[currentDistances.index(minDist)]})        # přidání identifikátoru nejbližšího kontejneru do záznamu adresního bodu

        with open(outputFile, 'w' ,encoding = 'utf-8') as output:       # uložení adresních bodů s identifikátory nejbližšího kontejnerů do výstupního souboru
            dump(addressPoints, output, ensure_ascii = False, indent = 4)

        print(f'Načteno a zpracováno {len(addressPoints)} adresních bodů.')     # výpisy o počtu bodů
        print(f'Z {cFeaturesLen} načtených kontejnerů bylo zpracováno {len(privateContainers) + len(publicContainers)} korektních kontejnerů.')
        return nearestDistances, nearestAddresses

def strMaximums(maximums : list) -> str:    
    """Ze seznamu vytvoří řetězec s každou položkou na samostatném řádku."""
    maximumsStr = f',{",".join(max for max in [*maximums])}'
    maximumsStr = maximumsStr.replace(',', '\n')
    return maximumsStr

def findMax(distList : list) -> list:
    """V závislosti na četnosti hodnoty do seznamu vloží odpovídají počet slovníků obsahující 
    hodnotu maximální nejbližší vzdálenosti ke kontejneru a její index v seznamu."""
    max = [{'dist' : distList[0], 'indx' : 0}]
    for i in range(1, len(distList)):
        if distList[i] > max[0]['dist']:
            max = [{'dist' : distList[i], 'indx' : i}]
        elif distList[i] == max[0]['dist']:
            max.append({'dist' : distList[i], 'indx' : i}) 
    return max

def printMax(maxList : list, addrList : list) -> None:
    """Vypisuje maximum a adresy odpovídající této vzdálenosti k nejbližšímu kontejneru."""
    maximums = len(maxList)
    maxDist = maxList[0]['dist']
    if maximums == 1:
        indx = maxList[0]['indx']
        print(f'Maximální vzdálenost k nejbližšímu kontejneru je {maxDist} m a to z adresy {addrList[indx]}.')
    elif maximums > 1:
        maxAddresses = [addrList[i['indx']] for i in maxList]
        maxAddresses = strMaximums(maxAddresses)
        print(f'Maximální vzdálenost k nejbližšímu kontejneru {maxDist} m byla dosažena pro následující adresy: {maxAddresses}.')

def Median(distList : list, listLen : int) -> None:
    """Počítá a vypisuje medián vzdálenosti k nejbližšímu kontejneru."""
    distList.sort()
    mid = int(listLen / 2)
    if listLen % 2 == 0:        # výpočet v závislosti na sudém / lichém počtu vzdáleností
        median = round((distList[mid - 1] + distList[mid]) / 2)
    else:
        median = distList[mid]
    print(f'Medián průměrné vzdálenosti k nejbližšímu kontejneru je {median} m.')

def statistics(distances : list, addresses : list) -> None:
    """S využitím podfunkcí vypisuje průměrnou vzdálenost a medián vzdálenosti k nejbližšímu 
    kontejneru a adresu/y, pro které je to nejdál k nejbližšímu kontejneru."""
    length = len(distances)
    if length == 1:
        print('Vzdálenost k nejbližšímu kontejneru byla vypočtena pouze pro 1 adresu, výsledek nelze s ničím porovnávat.')
    print(f'Průměrná vzdálenost k nejbližšímu kontejneru je {round(sum(distances) / len(distances))} m.')

    max = findMax(distances)
    printMax(max, addresses)
    Median(distances, length)

args = parse()
if fileControl(args.addresses, args.containers, 'adresy_kontejnery.geojson'):
    dists, addrs = inputProcessing(args.addresses, args.containers, 'adresy_kontejnery.geojson')
    statistics(dists, addrs)