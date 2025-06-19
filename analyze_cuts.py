import sqlite3
from collections import defaultdict
import itertools
import networkx as nx


def getData():
    conn = sqlite3.connect('cables.db')
    c = conn.cursor()
    c.execute('SELECT name, landing_point, country FROM cables WHERE country != ""')
    data = c.fetchall()
    conn.close()
    return data



def MinCut(targetCountry, cableToCountries):
    cutSet = set()
    for cable, countries in cableToCountries.items():
        if targetCountry in countries and len(countries) > 1:
            cutSet.add(cable)   
    return sorted(list(cutSet))


def buildgraph(dbData):
    G = nx.Graph()
    lpToCountry = {}  # lp = landing point
    cableToLps = defaultdict(list)

    for cable, lp, country in dbData:
        lpToCountry[lp] = country
        G.add_node(lp, country=country)
        cableToLps[cable].append(lp)
    
    for cable, lps in cableToLps.items():
        for lp1, lp2 in itertools.combinations(lps, 2):
            if lp1 != lp2:
                G.add_edge(lp1, lp2, cable=cable)
                
    return G, lpToCountry

def internalcutNodes(targetCountry, dbData):
    cableToCountries = defaultdict(set)
    for cable, lp, country in dbData:
        cableToCountries[cable].add(country)

    internationalCables = {c for c, countries in cableToCountries.items() if len(countries) > 1}
    
    internalCutSet = set()
    for cable, lp, country in dbData:
        if country == targetCountry and cable in internationalCables:
            internalCutSet.add(lp)
            
    return sorted(list(internalCutSet))

def globalMinCut(G, targetCountry, lpToCountry):
    H = G.copy()
    internal = {lp for lp, country in lpToCountry.items() if country == targetCountry}
    external = {lp for lp, country in lpToCountry.items() if country != targetCountry}

    if not internal or not external or not any(nx.has_path(H, u, v) for u in internal for v in external):
        return []

    source, sink = 'SOURCE', 'SINK'
    H.add_node(source)
    H.add_node(sink)

    for node in internal: H.add_edge(source, node)
    for node in external: H.add_edge(node, sink)
    
    cutSet = nx.minimum_node_cut(H, source, sink)
    return sorted(list(cutSet))


def byCountry(analysisType, targetCountry, dbData, graphData):
    graph, lpToCountry, cableToCountries = graphData
    print(f"\nAnalyzing: {targetCountry}")
    print("="*50)

    if analysisType == 'cable':
        minCutCables = MinCut(targetCountry, cableToCountries)
        print(f"{len(minCutCables)} cables :")
        if not minCutCables:
            print("  None")
        else:
            for cable in minCutCables:
                print(f"  - {cable}")
    
    elif analysisType == 'landing_point':
        internalCut = internalcutNodes(targetCountry, dbData)
        print("Internal Cut")
        print(f"  Nodes to disable: {len(internalCut)}")
        if not internalCut:
            print(f" ")
        else:
            for node in internalCut:
                print(f"  - {node}")

        globalCut = globalMinCut(graph, targetCountry, lpToCountry)
        print(f"\nMinimum Global Cut (Includes external nodes if needed to achieve smallest possible cut)")
        print(f"  Nodes to disable: {len(globalCut)}")
        if not globalCut:
            print("  This country is already isolated or has no international connections.")
        else:
            for node in globalCut:
                nodeCountry = lpToCountry.get(node, "Unknown")
                print(f"  - {node} ({nodeCountry})")
    
    print("-" * 50 + "\n")

def Everything(analysisType, allCountries, dbData, graphData):
    for country in allCountries:
        byCountry(analysisType, country, dbData, graphData)

def main():
    dbData = getData()
    if not dbData:
        return

    graph, lpToCountry = buildgraph(dbData)
    cableToCountries = defaultdict(set)
    for cable, lp, country in dbData:
        cableToCountries[cable].add(country)
    allCountries = sorted(list(set(lpToCountry.values())))
    graphData = (graph, lpToCountry, cableToCountries)

    while True:
        print("1. Edge Cut (Cables)")
        print("2. Node Cut (Landing Points)")
        print("3. Exit")
        choice = input()

        if choice == '1':
            analysisType = 'cable'
        elif choice == '2':
            analysisType = 'landing_point'
        elif choice == '3':
            print("Exiting.")
            break
        else:
            print("Please enter 1, 2, or 3.")
            continue

        while True:
            print("\n")
            print("1. Single country")
            print("2. List all countries")
            print("3. Back to main menu")
            
            subChoice = input("Enter your choice (1, 2, or 3): ")

            if subChoice == '1':
                countryToCheck = input(f"\nCountry Name: ")
                if countryToCheck not in allCountries:
                    print(f"\nCountry '{countryToCheck}' not found.")
                else:
                    byCountry(analysisType, countryToCheck, dbData, graphData)
            elif subChoice == '2':
                Everything(analysisType, allCountries, dbData, graphData)
            elif subChoice == '3':
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    main()