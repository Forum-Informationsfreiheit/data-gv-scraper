from operator import length_hint

import httpx
from sqlalchemy.exc import IntegrityError

from api_client.database import DistributionStatus, MissingInfo


def checkDistributions(session, distributions, datasetId):
    http_client = httpx.Client(follow_redirects=True, timeout=3.0)
    
    broken_dist_names = []
    countMissingLicense = 0

    if distributions:
        for distribution in distributions:
            distribution_id = distribution.get("id")
            try:
                access_urls = distribution["access_url"] or []
            except:
                access_urls = []

            if not distribution_id or not access_urls:
                continue

            # Check if already checked
            existing = session.query(DistributionStatus).filter_by(
                distribution_id=distribution_id
            ).first()

            hasLicense = False
            try:
                if not distribution["license"]["resource"]:
                    if not distribution["license"]["resource"]:
                        if not distribution["license"]["resource"]:
                            if not distribution["license"]["resource"]:
                                hasLicense = True
            except:
                countMissingLicense += 1
                session.add(MissingInfo(datasetId=datasetId, missing="file has no license"), )
                            
            if existing:
                # If already checked and it was broken, add to list
                if existing.status != 200:
                    title = distribution.get("title", {})
                    if isinstance(title, dict):
                        title = title.get("de") or title.get("en") or title.get("it") or str(distribution_id)
                    broken_dist_names.append(title)
                continue

            final_status = 200  # Default to success
            failed_url = None

            # Check each access URL
            for url in access_urls:
                if "sdi.noe.gv.at" in url or "WFSServer" in url or "https://data.wien.gv.at/daten/geo" in url or "https://data.wien.gv.at/daten/wms" in url:
                    final_status = 200
                else: 
                    try:
                        # Use stream=True to avoid reading the body, just get headers
                        with http_client.stream("GET", url, timeout=3.0) as response:
                            if response.status_code != 200:
                                final_status = response.status_code
                                failed_url = url  # Track which URL we're checking
                                #print(f"BROKEN: {url} -> Status {response.status_code}")
                                break
                            # Connection is automatically closed when exiting the context manager
                    except httpx.HTTPError as e:
                        try: 
                            final_status = e.raise_for_status()  
                        except:
                            final_status = 0 # Use 0 for network/connection errors
                        failed_url = url  # Track which URL we're checking
                        #print(f"ERROR: {url} -> {type(e).__name__}")
                        break
                    except Exception as e:
                        final_status = -1  # Use -1 for unexpected errors
                        failed_url = url  # Track which URL we're checking
                        #print(f"UNEXPECTED ERROR: {url} -> {type(e).__name__}")
                        break

            # If broken, add to the list and db
            if final_status != 200:
                dist_status = DistributionStatus(
                    distribution_id=distribution_id,
                    status=final_status,
                    url=failed_url
                )
                session.add(dist_status)
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                title = distribution.get("title", {})
                if isinstance(title, dict):
                    title = title.get("de") or title.get("en") or title.get("it") or str(distribution_id)
                broken_dist_names.append(title)
    return [length_hint(broken_dist_names), length_hint(distributions), countMissingLicense]
        