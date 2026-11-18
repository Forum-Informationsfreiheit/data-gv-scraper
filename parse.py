from datetime import datetime

from api_client.database import Catalogue, Dataset, Keyword, KeywordDataset, Category, CategoryDataset, MissingInfo

def parseJsonCatalog(catalogue_id, detail):
    catalogue = Catalogue(
                    id = catalogue_id, 
                    description = parse(detail, 'description'),
                    title = parseInDefaultLanguage(detail, 'title'),
                    created = parseDate(detail, 'issued'),
                    lastModified = parseDate(detail, 'modified'),
                    count = parse(detail,'count'),
                    isPartOfDataGV = (parse(detail,'is_part_of') == "data-gv-at"),
                    data = detail, 
                    done_scraping=False
                )
    return catalogue

def parseJsonDataset(session, catalogue_id, dataset_id, detail):
    dataset = Dataset(
                    id = dataset_id,
                    catalogueId = catalogue_id,
                    title = parseInDefaultLanguage(detail, 'title'),
                    description = parseInDefaultLanguage(detail, 'description'),
                    created = parseDate(detail, 'issued'),
                    lastModified = parseDate(detail, 'modified'),
                    distributions = parse(detail, 'distributions'),
                    publisherType = parseChild(detail, 'publisher', 'type'),
                    publisherName = parseChild(detail, 'publisher', 'name'),
                    publisherMail = parseChild(detail, 'publisher', 'email'),
                    publisherUrl = parseChild(detail, 'publisher', 'hompage'),
                    publisherResource = parseChild(detail, 'publisher', 'resource'),
                    contactType = parseChild(detail, 'contact_point', 'type'),
                    contactName = parseChild(detail, 'contact_point', 'name'),
                    contactMail = parseChild(detail, 'contact_point', 'email'),
                    contactAddress = parseChild(detail, 'contact_point', 'address'),
                    contactPhone = parseChild(detail, 'contact_point', 'telephone'),
                    contactUrl = parseChildList(detail, 'contact_point', 'url'),
                    contactResource = parseChild(detail, 'contact_point', 'resource'),
                    resourceLink = parse(detail, 'resource')

                    #data = detail
                )

    missing = True
    try:
        for keyword in parse(detail, 'keywords'):
            keywordId = parse(keyword, 'id')
            if not session.query(Keyword).filter_by(id = keywordId).first():
                session.add(Keyword(id = keywordId, label = parse(keyword, 'label'), language = parse(keyword, 'language')))
            
            session.add(KeywordDataset(datasetId = dataset_id, keywordId = keywordId))
            missing = False
    except: ()
    
    if missing:
        session.add(MissingInfo(datasetId = dataset_id, missing = "Keywords"))

    missing = True
    try:
        for category in parse(detail, 'categories'):
            categoryId = parse(category, 'id')
            if not session.query(Category).filter_by(id = categoryId).first():
                session.add(Category(id = categoryId, label = parseInDefaultLanguage(category, 'label')))
            session.add(CategoryDataset(datasetId = dataset_id, categoryId = categoryId))
            missing = False
    except: ()

    if missing:
        session.add(MissingInfo(datasetId = dataset_id, missing = "Categories"))
    
    return dataset

def parseDate (detail, parent):
    try:
        return datetime.fromisoformat(detail[parent])
    except:
        return datetime.fromisoformat("1900-01-01T00:00:00Z")

def parseInDefaultLanguage(detail, parent):
    try: 
        return detail[parent]["de"]
    except:
        try:
            return detail[parent]["en"]
        except:
            return ""

def parse(detail, parent):
    try: 
        return detail[parent]
    except:
        return ""

def parseChildList(detail, parent, child):
    try: 
        return detail[parent][0].get(child)
    except:
        return ""
    
def parseChild(detail, parent, child):
    try: 
        return detail[parent].get(child)
    except:
        return ""

def emptyOrNull(text):
    return (not text) or (text == "")