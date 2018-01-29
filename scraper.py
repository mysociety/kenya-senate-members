# coding=utf-8

import scraperwiki
import lxml.html
import sqlite3
import re

BASE_URL = 'http://parliament.go.ke/the-senate/senators?start='

HONORIFIC_MAP = {
    'Sen.': 'Q2746176'
}

PARTY_MAP = {
    'N/A':      '',             # N/A
    'ANC':      'Q47489380',    # Amani National Congress
    'CCM':      'Q47492863',    # Chama Cha Mashinani
    'EFP':      'Q42954840',    # Economic Freedom Party
    'FAP':      'Q47492871',    # Frontier Alliance Party
    'FORD-K':   'Q5473121',     # Forum for the Restoration of Democracy – Kenya
    'FORD - K': 'Q5473121',     # Forum for the Restoration of Democracy – Kenya
    'IND':      'Q327591',      # Independent
    'JP':       'Q27963537',    # Jubilee Party of Kenya
    'KANU':     'Q1422517',     # Kenya African National Union
    'KPP':      'Q47492848',    # Kenya Patriots Party
    'MCCP':     'Q47489396',    # Maendeleo Chap Chap Party
    'NAPK':     'Q47492879',    # National Agenda Party of Kenya
    'ODM':      'Q1640905',     # Orange Democratic Movement
    'PDR':      'Q7141057',     # Party of Development and Reforms
    'PNU':      'Q2559675',     # Party of National Unity
    'WDM-K':    'Q5251223',     # Wiper Democratic Movement
    'PDP':      'Q22666200',    # Peoples Democratic Party
    'CCU':      'Q5069325',     # Chama Cha Uzalendo
    'KNC':      'Q6392670',     # Kenya National Congress
    'DP':       'Q3272441',     # Democratic Party
    'ND':       'Q47490108',    # New Democrats
    'MUUNGANO': 'Q22666185',    # Muungano Party
}

# We maintain an internal map of counties and constituencies to WD items.
# TODO: This should really live somewhere else

COUNTY_MAP = {
    'Baringo': 'Q808201',
    'Bomet': 'Q891952',
    'Bungoma': 'Q2928204',
    'Busia': 'Q1017519',
    'Elgeyo Marakwet': 'Q15216433',
    'Embu': 'Q1335242',
    'Garisa': 'Q1494292',
    'Homa Bay': 'Q1625834',
    'Isiolo': 'Q1499046',
    'Kajiado': 'Q285072',
    'Kakamega': 'Q1721867',
    'Kericho': 'Q1739252',
    'Kiambu': 'Q2575594',
    'Kilifi': 'Q1741307',
    'Kirinyaga': 'Q2230311',
    'Kisii': 'Q1743730',
    'Kisumu': 'Q1743809',
    'Kitui': 'Q1722597',
    'Kwale': 'Q952571',
    'Laikipia': 'Q1800699',
    'Lamu': 'Q1951652',
    'Machakos': 'Q1882639',
    'Makueni': 'Q473717',
    'Mandera': 'Q1477874',
    'Marsabit': 'Q1323683',
    'Meru': 'Q15045704',
    'Migori': 'Q429955',
    'Mombasa': 'Q1112885',
    'Murang\'a': 'Q1781723',
    'Nairobi': 'Q3335223',
    'Nakuru': 'Q1852202',
    'Nandi': 'Q1964569',
    'Narok': 'Q1852220',
    'Nyamira': 'Q1569613',
    'Nyandarua': 'Q1714352',
    'Nyeri': 'Q749665',
    'Samburu': 'Q2096419',
    'Siaya': 'Q3482913',
    'Taita Taveta': 'Q7193788',
    'Tana River': 'Q383150',
    'Tharaka Nithi': 'Q2189432',
    'Trans Nzoia': 'Q1278653',
    'Turkana': 'Q1633078',
    'Uasin Gishu': 'Q1121429',
    'Vihiga': 'Q1313202',
    'Wajir': 'Q1852209',
    'West Pokot': 'Q590860',
}

parsedMembers = []
unreconciledCounties = []
unreconciledParties = []

PAGES = 4
PER_PAGE = 20


def cleanup(string):

    # Strip any annoying whitespace
    string = string.strip()

    # Lose any curled apostrophies
    string = string.replace(u'’', '\'')

    return string

for x in range(0, PAGES):

    pageStart = PER_PAGE * x

    scrapeUrl = BASE_URL + str(pageStart)

    print('(i) Scraping from ' + scrapeUrl)

    # Get the page!
    html = scraperwiki.scrape(scrapeUrl)
    ssRoot = lxml.html.fromstring(html)

    rows = ssRoot.cssselect('tr')

    # Skip the header row
    for row in rows[1:]:

        memberData = {}

        nameLink = row.cssselect('a')[0]

        nameUnparsed = nameLink.text.strip()

        nameRegex = re.search('(.+?) (.+)', nameUnparsed)
        memberData['honorific_string'] = nameRegex.group(1)
        memberData['honorific_id'] = HONORIFIC_MAP[nameRegex.group(1)]

        memberData['name'] = cleanup(nameRegex.group(2))

        print('    ' + memberData['name'])

        linkHref = nameLink.attrib['href']

        idRegex = re.search('\/the-senate\/senators\/item\/(.+)', linkHref)
        memberData['id'] = idRegex.group(1)

        memberData['url'] = cleanup('http://parliament.go.ke/the-senate/senators/item/' + memberData['id'])

        partyCode = cleanup(row.cssselect('td')[4].text)

        memberData['party'] = partyCode
        if partyCode in PARTY_MAP:
            memberData['party_id'] = PARTY_MAP[partyCode]
        else:
            memberData['party_id'] = 'Code: "{}"'.format(partyCode)
            unreconciledParties.append(partyCode)

        electoralStatus = cleanup(row.cssselect('td')[5].text)

        if electoralStatus == 'Elected':

            # We only need to account for location if the person is elected.
            # Nominees don't have these things, but are still members.

            county = cleanup(row.cssselect('td')[2].text)
            constituency = cleanup(row.cssselect('td')[3].text)

            memberData['county'] = county
            memberData['constituency'] = constituency

            if county in COUNTY_MAP:
                memberData['district_id'] = COUNTY_MAP[county]
            else:
                memberData['district_id'] = 'County: "{}", Constituency: "{}"'.format(county, constituency)
                unreconciledCounties.append(county)
                print('      > Unreconciled county: ' + county)

        parsedMembers.append(memberData)

    print '(i) Counted {} Members so far...'.format(len(parsedMembers))

print('(i) Done.')
print '(i) Counted {} Members in total'.format(len(parsedMembers))
print '<!> {} unreconciled counties:'.format(len(unreconciledCounties))
print unreconciledCounties
print '<!> {} unreconciled parties:'.format(len(unreconciledParties))
print unreconciledParties

try:
    scraperwiki.sqlite.execute('DELETE FROM data')
except sqlite3.OperationalError:
    pass
scraperwiki.sqlite.save(
    unique_keys=['id'],
    data=parsedMembers)
