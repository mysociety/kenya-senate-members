# coding=utf-8

import scraperwiki
import lxml.html
import sqlite3
import re

BASE_URL = 'http://www.parliament.go.ke/the-national-assembly/members?start='

HONORIFIC_MAP = {
    'Hon.': 'Q2746176'
}

PARTY_MAP = {
    'IND': 'Q327591',  # Independent
    'JP': 'Q27963537',  # Jubilee Party of Kenya
    'FORD-K': 'Q5473121',  # Forum for the Restoration of Democracy – Kenya
    'ODM': 'Q1640905',  # Orange Democratic Movement
    'WDM-K': 'Q5251223',  # Wiper Democratic Movement
    'KANU': 'Q1422517',  # Kenya African National Union
}

parsedMembers = []

PAGES = 12
PER_PAGE = 30

for x in range(0, PAGES):

    pageStart = PER_PAGE * x

    scrapeUrl = BASE_URL + str(pageStart)

    print('Scraping from ' + scrapeUrl)

    # Get the page!
    html = scraperwiki.scrape(scrapeUrl)
    ssRoot = lxml.html.fromstring(html)

    rows = ssRoot.cssselect('tr')

    # Skip the header row
    for row in rows[1:]:

        memberData = {}

        nameLink = row.cssselect('a')[0]

        nameUnparsed = nameLink.text.strip()

        linkHref = nameLink.attrib['href']

        idRegex = re.search('\/the-national-assembly\/members\/item\/(.+)', linkHref)
        memberData['id'] = idRegex.group(1)

        memberData['url'] = 'http://www.parliament.go.ke/the-national-assembly/members/item/' + memberData['id']

        nameRegex = re.search('(.+?) (.+), (.+)', nameUnparsed)
        memberData['honorific_string'] = nameRegex.group(1)
        memberData['honorific_id'] = HONORIFIC_MAP[nameRegex.group(1)]

        memberData['name'] = nameRegex.group(3) + ' ' + nameRegex.group(2)

        memberData['district'] = row.cssselect('td')[3].text.strip()

        partyCode = row.cssselect('td')[4].text.strip()

        if partyCode in PARTY_MAP:
            memberData['party'] = PARTY_MAP[partyCode]
        else:
            memberData['party'] = partyCode

        electoralStatus = row.cssselect('td')[5].text.strip()

        print memberData

        if electoralStatus == 'Elected':
            parsedMembers.append(memberData)
        else:
            print ('Skipping insert, status is ' + electoralStatus)

    print 'Counted {} Members so far...'.format(len(parsedMembers))

try:
    scraperwiki.sqlite.execute('DELETE FROM data')
except sqlite3.OperationalError:
    pass
scraperwiki.sqlite.save(
    unique_keys=['id'],
    data=parsedMembers)
