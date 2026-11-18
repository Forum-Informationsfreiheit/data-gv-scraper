from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, JSON, Text, Boolean, DATETIME
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Catalogue(Base):
    __tablename__ = "catalogue"

    id = Column(String, primary_key=True)
    description = Column(JSON, nullable=True)
    title = Column(String)
    created = Column(DATETIME)
    lastModified = Column(DATETIME)
    count = Column(Integer)
    isPartOfDataGV = Column(Boolean, default=False, nullable=False)
    data = Column(JSON, nullable=True)
    done_scraping = Column(Boolean, default=False, nullable=False)

    datasets = relationship("Dataset", back_populates="catalogue")

class Dataset(Base):
    __tablename__ = "dataset"

    id = Column(String, primary_key=True)
    catalogueId = Column(String, ForeignKey("catalogue.id"), nullable=False)
    title = Column(String)
    description = Column(String)
    created = Column(DATETIME)
    lastModified = Column(DATETIME)
    distributions = Column(JSON)
    publisherType = Column(String)
    publisherName = Column(String)
    publisherMail = Column(String)
    publisherUrl = Column(String)
    publisherResource = Column(String)
    contactType = Column(String)
    contactName = Column(String)
    contactMail = Column(String)
    contactAddress = Column(String)
    contactPhone = Column(String)
    contactUrl = Column(JSON)
    contactOrganizationName = Column(String)
    contactResource = Column(String)
    resourceLink = Column(String)
    communityId = Column(String, ForeignKey("community.id"))
    #license = Column(String)
    #language?!

    #data = Column(JSON, nullable=False)

    catalogue = relationship("Catalogue", back_populates="datasets")
    # keyword = relationship("KeywordDataset", back_populates="datasets")

class Community(Base):
     __tablename__ = "community"

     id = Column(String, primary_key=True)
     name = Column(String)
     people = Column(Integer)

# class CommunityDataset(Base):
#     __tablename__ = "community_dataset"

#     id = Column(Integer, primary_key=True)
#     communityId = Column(Integer, ForeignKey("community.id"), nullable=False)
#     datasetId = Column(String, ForeignKey("dataset.id"), nullable=False)

class KeywordDataset(Base):
    __tablename__ = "keyword_dataset" 
    
    id = Column(Integer, primary_key=True)
    datasetId = Column(String, ForeignKey("dataset.id"), nullable=False)
    keywordId = Column(String, ForeignKey("keyword.id"), nullable=False)

class Keyword(Base):
    __tablename__ = "keyword"

    id = Column(String, primary_key=True)
    label = Column(String)
    language = Column(String)

class CategoryDataset(Base):
    __tablename__ = "category_dataset" 

    id = Column(Integer, primary_key=True)
    datasetId = Column(String, ForeignKey("dataset.id"), nullable=False)
    categoryId = Column(String, ForeignKey("category.id"), nullable=False)

class Category(Base):
    __tablename__ = "category"

    id = Column(String, primary_key=True)
    label = Column(String)

class MissingInfo(Base):
    __tablename__ = "missing_info"

    id = Column(Integer, primary_key=True)
    datasetId = Column(String)
    missing = Column(String)

class DistributionStatus(Base):
    __tablename__ = "distribution_status"

    id = Column(Integer, primary_key=True)
    distribution_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(Integer, nullable=False)
    url = Column(Text, nullable=True)

def init_db(db_path: str = "db.sqlite3"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()