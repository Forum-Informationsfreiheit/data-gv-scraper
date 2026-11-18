# data-gv-scraper
## run all
<code>python scrape.py</code> runs scrapping of data.gv.at (creates local db) and creates reports in /reports folder. Furthermore there is a overall and simplied report in the terminal

## create reports from db
<code>python generateReports.py</code>
This only works if you created the database in the past

## Feature toggles
### since IFG
<code>dataSetsSinceIFG = True</code> is default. This means the scrapping and report only uses datasets which where published after the 2026-09-01.

### file check
<code>includedFileCheck = False </code> is default. If this is true, every resource link gets opened and checked for http status. This takes almost 10 hours of time.

## Excecution times
* scrape: arround 1 or 2 hours to generate the db
* reporting only: a few minutes
* filecheck: ~10 hours
