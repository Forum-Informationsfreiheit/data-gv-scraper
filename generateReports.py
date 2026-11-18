import csv
from datetime import datetime
import operator
import re

from sqlalchemy import func

from api_client.database import Category, CategoryDataset, Community, Dataset, Keyword, KeywordDataset, MissingInfo, get_session, init_db
from checkDistributions import checkDistributions
from parse import emptyOrNull


def generateReports(includesFileCheck):
    session = get_session(init_db())
    importCommunity(session)
    generateMetadataReport(session, includesFileCheck)
    generateKeywordReport(session)
    generateCategoriesReport(session)
    generateCommunityReport(session)
    if (includesFileCheck):
        generateReportWithFailedUrls(session)

def generateMetadataReport(session, includesFileCheck):
    print("generating metadata report...")

    countMissingKeywords = 0
    countMissingCategories = 0
    countNoCreationDate = 0
    countModifiedBeforeCreatedDate = 0
    countNoTitle = 0
    countNoDescription = 0
    countShortDesc = 0
    countTitleAndDescAreTheSame = 0
    countNoPublisherInfo = 0
    countNoContactInfo = 0
    countDatasets = 0
    countNoPublisherName = 0
    countUnsuccessfullDistributions = 0
    countDistributions = 0
    countMissingLicense = 0

    with open("reports/metadataCheck.csv", mode = 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["dataset id", "info"])

        for info in session.query(MissingInfo).all():
           if (info.missing == "Keywords"):
               countMissingKeywords += 1
           if (info.missing == "Categories"):
               countMissingCategories += 1
           writer.writerow([info.datasetId, info.missing])

        datasets = session.query(Dataset).all()       
        countAll = operator.length_hint(datasets)
        
        for dataset in datasets:
            countDatasets += 1
            if includesFileCheck and (countDatasets % 5 == 0):
                print(f"                                {countDatasets}/{countAll} datasets analysed | including {countDistributions} files ({countUnsuccessfullDistributions} were not status 200)")
            
            checkForMatchingCommunity(session, dataset)
            if includesFileCheck:
                dist = checkDistributions(session, dataset.distributions, dataset.id)
                countUnsuccessfullDistributions += dist[0]
                countDistributions += dist[1]
                countMissingLicense += dist[2]

            if emptyOrNull(dataset.title):
                countNoTitle += 1
                writer.writerow([dataset.id, "no title"])

            if emptyOrNull(dataset.description):
                countNoDescription += 1
                writer.writerow([dataset.id, "no description"])

            if len(dataset.description) < 50:
                countShortDesc += 1
                writer.writerow([dataset.id, "description below 50 charts"])

            if dataset.title == dataset.description:
                countTitleAndDescAreTheSame += 1
                writer.writerow([dataset.id, "title and description is same text"])

            if not dataset.created or (datetime.isoformat(dataset.created) < datetime.isoformat(datetime.fromisoformat("1900-01-02T00:00:00Z"))):
                countNoCreationDate += 1
                writer.writerow([dataset.id, "no creation date", dataset.created, dataset.lastModified])
            else:
                if datetime.isoformat(dataset.created) > datetime.isoformat(dataset.lastModified):
                    countModifiedBeforeCreatedDate += 1
                    writer.writerow([dataset.id, "modified date earlier than creation date", dataset.created, dataset.lastModified])

            if emptyOrNull(dataset.publisherName) and emptyOrNull(dataset.publisherMail) and emptyOrNull(dataset.publisherName) and emptyOrNull(dataset.publisherUrl) and emptyOrNull(dataset.publisherResource):
                countNoPublisherInfo += 1
                writer.writerow([dataset.id, "no publisher info (no name, mail, url or resource)"])

            if emptyOrNull(dataset.contactName) and emptyOrNull(dataset.contactMail) and emptyOrNull(dataset.contactAddress) and emptyOrNull(dataset.contactPhone) and emptyOrNull(dataset.contactUrl) and emptyOrNull(dataset.contactOrganizationName) and emptyOrNull(dataset.contactResource):
                countNoContactInfo += 1
                writer.writerow([dataset.id, "no conact info (no name, mail, url or resource)"])

        file.close() 

    print(f"\n------ report metadata for {countDatasets} elements with ------ ")
    print(f"                          No keywords set: {countMissingKeywords}")
    print(f"                        No categories set: {countMissingCategories}")
    print(f"                     No creation date set: {countNoCreationDate}")
    print(f"Modified date before created (or not set): {countModifiedBeforeCreatedDate}")
    print(f"                             No title set: {countNoTitle}")
    print(f"                       No description set: {countNoDescription}")
    print(f"         description is short (<50 chars): {countShortDesc}")
    print(f"              title and desc are the same: {countTitleAndDescAreTheSame}")
    print(f"                        no publisher name: {countNoPublisherName}")
    print(f"                        no publisher info: {countNoPublisherInfo}")
    print(f"                          no contact info: {countNoContactInfo}")
    if includesFileCheck:
        print(f"                            distributions: {countDistributions}")  
        print(f"               unsucessfull distributions: {countUnsuccessfullDistributions}")
        print(f"             distribution without license: {countMissingLicense}")

def importCommunity(session):
    # https://www.statistik.at/statistiken/bevoelkerung-und-soziales/bevoelkerung/bevoelkerungsstand/bevoelkerung-zu-jahres-/-quartalsanfang
    # Detailergebnise >> Bevölkerung zu Jahresbeginn nach administrativen Gebietseinheiten (Bundesländer, NUTS-Regionen, Bezirke, Gemeinden) seit 2002 (.ods)
    # https://www.statistik.at/fileadmin/pages/405/Bev_Zeitreihe_Jahresbeginn_Gebietseinheiten.ods
    # open - only keep 'Insgesamt' -> delete the others - save as .csv (in utf-8)
    print("import communities from csv...")
    with open('import/Bev_Zeitreihe_Jahresbeginn_Gebietseinheiten.csv', encoding = 'utf-8') as file:
        reader = csv.reader(file, delimiter=',')
        lineCount = 0
        for row in reader:
            lineCount += 1
            addToDatabase = False
            id = row[0]
            name = row[1]
            people = row[26]
            people = people.replace(".", "")
            people = people.replace(",", "")

            if lineCount > 8 and lineCount < 17:
                name = "Land " + row[1]
                addToDatabase = True

            #TODO needed?
            # if lineCount > 54 and lineCount < 148:
            #     name = "BH " + row[1]
            #     addToDatabase = True

            if lineCount > 171 and lineCount < 2264:
                addToDatabase = True
            
            if addToDatabase:
                if not session.query(Community).filter_by(id=id).first():
                    session.add(Community(id = id, name = name, people = people))

    session.commit()
    file.close()

def generateKeywordReport(session):
    countOnlyUsedOnce = 0
    countIsIfg = 0
    countContainsIfg = 0
    query = session.query(KeywordDataset, Keyword, func.count(KeywordDataset.keywordId)
        ).group_by(KeywordDataset.keywordId
        ).filter(KeywordDataset.keywordId == Keyword.id
    )   .order_by(func.count(KeywordDataset.keywordId).desc()).all()

    with open("reports/keywordCount.csv", mode = 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["id", "label", "count"])

        for entry in query:
            writer.writerow([entry[1].id[:100], entry[1].label[:100], entry[2]])
            if entry[1].id == "ifg":
                countIsIfg = entry [2]
            if "ifg" in entry[1].id :
                countContainsIfg += entry [2]
            if entry[2] == 1:
                countOnlyUsedOnce += 1

        file.close() 
    print(f"                              has ifg tag: {countIsIfg}")
    print(f"                       tag contains \'ifg\': {countContainsIfg}")
    print(f"\n------ report keywords for {len(query)} elements ------ ")
    print(f"                      keywordOnlyUsedOnce: {countOnlyUsedOnce}")

def generateCategoriesReport(session):
    countOnlyUsedOnce = 0
    query = session.query(CategoryDataset, Category, func.count(CategoryDataset.categoryId)
        ).group_by(CategoryDataset.categoryId
        ).filter(CategoryDataset.categoryId == Category.id
        ).order_by(func.count(CategoryDataset.categoryId).desc()).all()

    with open("reports/categoriesCount.csv", mode = 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["id", "label", "count"])

        for entry in query:
            writer.writerow([entry[1].id[:100], entry[1].label[:100], entry[2]])
            if entry[2] == 1:
                countOnlyUsedOnce += 1

        file.close() 
    print(f"\n------ report categories for {len(query)} elements ------ ")
    print(f"                   categoriesOnlyUsedOnce: {countOnlyUsedOnce}")

def generateCommunityReport(session):
    print("generating community report...")
    query = session.query(Dataset, Community, func.count(Dataset.communityId)
        ).group_by(Dataset.communityId
        ).filter(Dataset.communityId == Community.id
        ).order_by(Community.people.desc()).all()

    countCommunitys = session.query(Community.id).count()
    
    with open("reports/communityCount.csv", mode = 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["glz", "name", "people", "count", "entries per 1000 people"])

        countBig = 0
        sumBig = 0
        countSmall = 0
        sumSmall = 0
        communityWithoutEntry = 0

        for entry in query:
            countCommunitys -= 1
            entriesPerPeople = entry[2] / entry[1].people * 1000;
            writer.writerow([entry[1].id, entry[1].name, entry[1].people, entry[2], entriesPerPeople])
            if entry[1].people > 5000:
                countBig += 1
                sumBig += entry[2]
            else:
                countSmall += 1
                sumSmall += entry[2]
            if entry[2] < 1:
                communityWithoutEntry += 1
                
        file.close() 
    print(f"\n------ report community for {len(query)} elements ------ ")
    print(f"                   community without data: {countCommunitys}")  
    print(f"             communities over 5000 people: {countBig}")
    print(f"                 entries over 5000 people: {sumBig}")
    print(f"                average entries over 5000: {sumBig/countBig}")
    print(f"            communities below 5000 people: {countSmall}")
    print(f"                entries below 5000 people: {sumSmall}")
    print(f"               average entries below 5000: {sumSmall/countSmall}")
    print(f"          communities without publication: {communityWithoutEntry}")          


def generateReportWithFailedUrls(session):
    print("generate report with failed urls...")
    

def checkForMatchingCommunity(session, dataset):
    if dataset.publisherName and not dataset.communityId:
        if 'Land ' in dataset.publisherName or 'Landesregierung' in dataset.publisherName or 'gemeinde' in dataset.publisherName.lower() or re.search(r"\b\d{5}\b", dataset.publisherName):
                            #print(f"{dataset.publisherName}...")
            for community in session.query(Community).all():
                community.name = community.name.replace("Sankt", "St.")
                community.name = community.name.replace("Lenzing an der Ager", "Lenzing")
                community.name = community.name.replace("Reißeck", "Reisseck")
                community.name = community.name.replace("Breitenfurt bei Wien", "Breitenfurt")
                community.name = community.name.replace("Neuhofen an der Krems", "Neuhofen/Krems")
                community.name = community.name.replace("Straß in Steiermark", "Strass in der Steiermark")
                community.name = community.name.replace("Kirchdorf an der Krems", "Kirchdorf")
                community.name = community.name.replace("Saalfelden am Steinernen Meer", "Saalfelden")
                community.name = community.name.replace("Veit an der Glan", "Veit/Glan")
                community.name = community.name.replace("Zwettl-Niederösterreich", "Zwettl-NÖ")
                community.name = community.name.replace("Hohenwarth-Mühlbach am Manhartsberg", "Hohenwarth-Mühlbach a.M.")
                community.name = community.name.replace("Krems an der Donua", "Stadt Krems")
                community.name = community.name.strip() 
                if community.name.lower() in dataset.publisherName.lower() or community.id in dataset.publisherName:
                    dataset.communityId = community.id


if __name__ == "__main__":
    generateReports()
