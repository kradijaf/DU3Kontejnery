# dodělat:
#   kontrola vstupů - existence souborů (nepokračovat, pokud len = 0), práva apod., správnost adresních bodů
#   práce se vstupy - strip adres apod, '-' ve WGS souřadnicích?, ukončit, pokud existuje 0 korektních kontejnerů nebo adres, vypsat
#   zadání - další požadavky
# očekává korektní adresní body, protože bonus chce nejbližší kontejner pro VŠECHNY adresy
# zanedbává případ kdy adresní bod má více stejně vzdálených kontejnerů s přesností na metry, bere první takový

from json import load, dump
from pyproj import Transformer
from math import sqrt

def wgsToSjtsk(wgsCoords : list) -> tuple:
    wgs2sjtsk = Transformer.from_crs(4326, 5514, always_xy= True)
    SJTSK = wgs2sjtsk.transform(wgsCoords[0], wgsCoords[1])
    return (SJTSK[0], SJTSK[1])

def pointDistance(points1 : list, points2 : list) -> float:
    return round(sqrt((points1[0] - points2[0])**2 + (points1[1] - points2[1])**2))

def inputProcessing(addressFile : str, containerFile : str, outputFile : str):
    with open(addressFile, encoding= 'utf-8') as a,\
    open(containerFile, encoding='utf-8') as c:

        aJSON = load(a)
        cJSON = load(c)
        
        privateContainers = []
        publicContainers = []
        cFeaturesLen = len(cJSON['features'])
        for container in cJSON['features']:
            try:
                tmp = [int(i) for i in container['geometry']['coordinates']]
                tmp = float(container['properties']['ID'])
                tmp = container['properties']['STATIONNAME'][0]
            except BaseException:
                pass
            else:
                if container['properties']['PRISTUP'] == 'obyvatelům domu':
                    privateContainers.append({'coordinates' : container['geometry']['coordinates'],
                                              'ID' : container['properties']['ID'],
                                              'STATIONNAME' : container['properties']['STATIONNAME']})
                elif container['properties']['PRISTUP'] == 'volně':
                    publicContainers.append({'coordinates' : container['geometry']['coordinates'],
                                              'ID' : container['properties']['ID'],
                                              'STATIONNAME' : container['properties']['STATIONNAME']})

        nearestDistances = []
        nearestAddresses = []
        addressPoints = aJSON['features']
        for addressPoint in addressPoints:
            """try:
                tmp = addressPoint['properties']['addr:street'][1]
                tmp = float(addressPoint['properties']['addr:housenumber'][0])
            except BaseException as e:
                id = addressPoint['id']
                print(f'V adresním bodě s identifikátorem: {id} nastala chyba: ', e)
            else:"""

            distance = -1
            address = addressPoint['properties']['addr:street'] + ' ' + str(addressPoint['properties']['addr:housenumber'])

            for privateCntnr in privateContainers:
                if privateCntnr['STATIONNAME'] == address:
                    distance = 0
                    addressPoint.update({'kontejner' : privateCntnr['ID']})
                    nearestAddresses.append(address)
                    nearestDistances.append(distance)
                    break
                
            if distance == -1:
                SJTSK = wgsToSjtsk(addressPoint['geometry']['coordinates'])
                currentDistances = []
                currentIDs = []

                for publicCntnr in publicContainers:
                    currentDistances.append(pointDistance(SJTSK, publicCntnr['coordinates']))
                    currentIDs.append(publicCntnr['ID'])

                minDist = min(currentDistances)
                nearestDistances.append(minDist)
                nearestAddresses.append(address)
                addressPoint.update({'kontejner' : currentIDs[currentDistances.index(minDist)]})

        with open(outputFile, 'w' ,encoding = 'utf-8') as output:
            dump(addressPoints, output, ensure_ascii = False, indent = 4)

        print(f'Načteno a zpracováno {len(addressPoints)} adresních bodů.')
        print(f'Z {cFeaturesLen} načtených kontejnerů bylo zpracováno {len(privateContainers) + len(publicContainers)} korektních kontejnerů.')
        return nearestDistances, nearestAddresses

def strMaximums(maximums : list) -> str:    
    maximumsStr = f',{",".join(max for max in [*maximums])}'
    maximumsStr = maximumsStr.replace(',', '\n')
    return maximumsStr

def findMax(distList : list) -> list:
    max = [{'dist' : distList[0], 'indx' : 0}]
    for i in range(1, len(distList)):
        if distList[i] > max[0]['dist']:
            max = [{'dist' : distList[i], 'indx' : i}]
        elif distList[i] == max[0]['dist']:
            max.append({'dist' : distList[i], 'indx' : i}) 
    return max

def printMax(maxList : list, addrList : list) -> None:
    maximums = len(maxList)
    maxDist = maxList[0]['dist']
    if maximums == 1:
        indx = maxList[0]['indx']
        print(f'Maximální vzdálenost k nejbližšímu kontejneru je {maxDist} m a to z adresy {addrList[indx]}.')
    elif maximums > 1:
        maxAddresses = [addrList[i['indx']] for i in maxList]
        maxAddresses = strMaximums(maxAddresses)
        print(f'Maximální vzdálenost k nejbližšímu kontejneru {maxDist} m byla dosažena pro následující adresy: {maxAddresses}.')
    pass

def Median(distList : list, listLen : int) -> None:
    distList.sort()
    mid = int(listLen / 2)
    if listLen % 2 == 0:
        median = round((distList[mid - 1] + distList[mid]) / 2)
    else:
        median = distList[mid]
    print(f'Medián průměrné vzdálenosti k nejbližšímu kontejneru je {median} m.')

def statistics(distances : list, addresses : list) -> None:
    length = len(distances)
    if length == 1:
        print('Vzdálenost k nejbližšímu kontejneru byla vypočtena pouze pro 1 adresu, výsledek nelze s ničím porovnávat.')

    print(f'Průměrná vzdálenost k nejbližšímu kontejneru je {round(sum(distances) / len(distances))} m.')

    max = findMax(distances)
    printMax(max, addresses)
    Median(distances, length)

dists, addrs = inputProcessing('DU3Kontejnery\\adresyShort.geojson', 'DU3Kontejnery\\kontejneryShort.geojson', 'DU3Kontejnery\\adresy_kontejnery.geojson')
statistics(dists, addrs)