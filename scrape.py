#!/usr/bin/env python3
from datetime import datetime
from operator import length_hint
from api_client import APIClient
from api_client.database import init_db, get_session, Catalogue, Dataset

from generateReports import generateReports
from parse import parseJsonCatalog, parseJsonDataset, parseDate

def scrapeAndReport():
    session = get_session(init_db())
    dataSetsSinceIFG = True
    #If the the file check is included, it takes about 10 hours to run the whole script
    #otherwise one or two hours
    includesFileCheck = False

    scrapeOpenDataGVat(session, dataSetsSinceIFG);
    generateReports(includesFileCheck);

    session.close()

def scrapeOpenDataGVat(session, dataSetsSinceIFG):
    client = APIClient(base_url="https://www.data.gv.at/api/hub/search")

    catalogs = scrapeCatalogs(client, session)

    countAll = length_hint(catalogs)
    countCurrent = 0
    for catalogue_id in catalogs:
        countCurrent = countCurrent + 1

        catalogue = session.query(Catalogue).filter_by(id=catalogue_id).first()
        if not catalogue:
            print(f" ------- ERROR: Catalogue not found in database: {catalogue_id}")
            continue

        if catalogue.done_scraping:
            continue

        response = client.get("/datasets", params={"catalogue": catalogue_id})
        response.raise_for_status()
        datasetIds = response.json()

        scrapeDatasets(client, session, catalogue, datasetIds, dataSetsSinceIFG)

        if (countCurrent % 100 == 0):
            print(f"                                {countCurrent}/{countAll} catalogues processed")

        catalogue.done_scraping = True
        session.commit()

    print("\nScraping complete!")

def scrapeCatalogs(client, session):

    catalogExists = session.query(Catalogue).all()

    if catalogExists:
        print(f"Using {len(catalogExists)} existing catalogues from database")
        CatalogIds = [c.id for c in catalogExists]
    else:
        print("Fetching catalogues from API...")
        catalogues_response = client.get("/catalogues")
        CatalogIds = catalogues_response.json()
        print(f"Found {len(CatalogIds)} catalogues")

        print("Creating catalogue records in database...")

        countCurrent = 0
        countAll = length_hint(CatalogIds)
        for catalogueId in CatalogIds:
            countCurrent = countCurrent + 1
            catalogue = session.query(Catalogue).filter_by(id=catalogueId).first()
            if not catalogue:
                response = client.get(f"/catalogues/{catalogueId}")
                detail = response.json()['result']

                catalogue = parseJsonCatalog(catalogueId, detail)
                session.add(catalogue)
                if (countCurrent % 100 == 0):
                    print(f"         {countCurrent}/{countAll} catalogues created")

        session.commit()

        print("All catalogues added to database")
    return CatalogIds

def scrapeDatasets(client, session, catalogue, datasetIds, datasetsSinceIfg):
    countCurrent = 0
    countAll = length_hint(datasetIds)
    for id in datasetIds:
        countCurrent = countCurrent + 1
        if (countCurrent % 100 == 0):
            print(f"         {countCurrent}/{countAll} datasets done")

        dataset = session.query(Dataset).filter_by(id=id).first()
        if not dataset:
            response = client.get(f"/datasets/{id}").raise_for_status()
            detail = response.json()['result']       
            
            date = datetime.isoformat(parseDate(detail, 'issued'))
            if datetime.isoformat(parseDate(detail, 'issued')) < datetime.isoformat(datetime.fromisoformat("1900-01-02T00:00:00Z")):
                date = datetime.isoformat(parseDate(detail, 'modified'))

            if date > datetime.isoformat(datetime.fromisoformat("2025-09-01T00:00:00Z") or not datasetsSinceIfg): 
                session.add(parseJsonDataset(session, catalogue.id, id, detail))

if __name__ == "__main__":
    scrapeAndReport()
