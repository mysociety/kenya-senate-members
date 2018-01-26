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
    'ANC':      'Q47489380',    # Amani National Congress
    'CCM':      'Q47492863',    # Chama Cha Mashinani
    'EFP':      'Q42954840',    # Economic Freedom Party
    'FAP':      'Q47492871',    # Frontier Alliance Party
    'FORD-K':   'Q5473121',     # Forum for the Restoration of Democracy – Kenya
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
    'Elgeyo/Marakwet': 'Q15216433',
    'Embu': 'Q1335242',
    'Garissa': 'Q1494292',
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
    'Tharaka-Nithi': 'Q2189432',
    'Trans-Nzoia': 'Q1278653',
    'Turkana': 'Q1633078',
    'Uasin Gishu': 'Q1121429',
    'Vihiga': 'Q1313202',
    'Wajir': 'Q1852209',
    'West Pokot': 'Q590860',
}

CONSTITUENCY_MAP = {
    'Webuye East': 'Q47463465',
    'Kilgoris': 'Q6406874',
    'Kisumu Town East': 'Q6417349',
    'Kamukunji': 'Q6359828',
    'Kapenguria': 'Q13640987',
    'Kanduyi': 'Q6361679',
    'Nakuru Town East': 'Q47463452',
    'Ndaragwa': 'Q6983699',
    'Roysambu': 'Q47462592',
    'Narok South': 'Q6966109',
    'Cherangany': 'Q5091828',
    'Starehe': 'Q7601801',
    'Seme': 'Q47463473',
    'Kisumu Town West': 'Q6417350',
    'Changamwe': 'Q5071716',
    'Hamisi': 'Q5645412',
    'Tongaren': 'Q47463467',
    'Nakuru Town West': 'Q47463451',
    'Kipipiri': 'Q13122881',
    'Narok North': 'Q6966106',
    'Taveta': 'Q7689082',
    'Ol Kalou': 'Q7082829',
    'Kesses': 'Q47463440',
    'Sabatia': 'Q7395935',
    'Kabuchai': 'Q47463464',
    'Matuga': 'Q6791957',
    'Embakasi North': 'Q47463494',
    'Eldas': 'Q47463412',
    'Bura': 'Q4998065',
    'Endebess': 'Q47463433',
    'Luanda': 'Q47463463',
    'Kieni': 'Q6405311',
    'Borabu': 'Q47463490',
    'Emurua Dikirr': 'Q19461591',
    'Jomvu': 'Q47463376',
    'Msambweni': 'Q6930119',
    'Embakasi West': 'Q47463499',
    'Dagoretti North': 'Q17048596',
    'Ainabkoi': 'Q47463438',
    'Ainamoi': 'Q4697387',
    'Aldai': 'Q4713420',
    'Alego Usonga': 'Q4714387',
    'Awendo': 'Q47463477',
    'Bahati': 'Q47463450',
    'Balambala': 'Q47463409',
    'Banissa': 'Q47463413',
    'Baringo Central': 'Q4860772',
    'Baringo North': 'Q4860776',
    'Baringo South': 'Q47463444',
    'Belgut': 'Q4882701',
    'Bobasi': 'Q4934581',
    'Bomachoge Borabu': 'Q47463484',
    'Bomachoge Chache': 'Q47463485',
    'Bomet Central': 'Q47463457',
    'Bomet East': 'Q47463456',
    'Bonchari': 'Q4941238',
    'Bondo': 'Q4941430',
    'Budalangi': 'Q4984030',
    'Bumula': 'Q4997372',
    'Bureti': 'Q4998466',
    'Butere': 'Q5002502',
    'Butula': 'Q5003161',
    'Buuri': 'Q24236151',
    'Central Imenti': 'Q5061241',
    'Chepalungu': 'Q5091695',
    'Chesumei': 'Q47463442',
    'Chuka/Igambang\'ombe': 'Q47463418',
    'Dadaab': 'Q47463410',
    'Dagoretti South': 'Q5208646',
    'Eldama Ravine': 'Q5353892',
    'Embakasi Central': 'Q47463496',
    'Embakasi East': 'Q47463497',
    'Embakasi South': 'Q47463492',
    'Emgwen': 'Q17085425',
    'Emuhaya': 'Q5374869',
    'Fafi': 'Q5429344',
    'Funyula': 'Q5509429',
    'Galole': 'Q5519275',
    'Ganze': 'Q5521558',
    'Garissa Township': 'Q17085899',
    'Garsen': 'Q5524277',
    'Gatanga': 'Q5526949',
    'Gatundu North': 'Q5527547',
    'Gatundu South': 'Q5527549',
    'Gem': 'Q5530554',
    'Gichugu': 'Q5559477',
    'Gilgil': 'Q47463447',
    'Githunguri': 'Q5565112',
    'Homa Bay Town': 'Q47463476',
    'Igembe Central': 'Q47463415',
    'Igembe North': 'Q5991642',
    'Igembe South': 'Q5991645',
    'Ijara': 'Q5995093',
    'Ikolomani': 'Q5996095',
    'Isiolo North': 'Q17088189',
    'Isiolo South': 'Q6081154',
    'Juja': 'Q6305268',
    'Kabete': 'Q17088410',
    'Kabondo Kasipul': 'Q6374553',
    'Kacheliba': 'Q6344643',
    'Kaiti': 'Q6348628',
    'Kajiado Central': 'Q6348981',
    'Kajiado East': 'Q47463454',
    'Kajiado North': 'Q6348987',
    'Kajiado South': 'Q6348985',
    'Kajiado West': 'Q30687313',
    'Kaloleni': 'Q13123143',
    'Kandara': 'Q6361325',
    'Kangema': 'Q6362689',
    'Kangundo': 'Q13123144',
    'Kapseret': 'Q47463439',
    'Karachuonyo': 'Q6367802',
    'Kasarani': 'Q6374034',
    'Kasipul': 'Q47463474',
    'Kathiani': 'Q6376607',
    'Keiyo North': 'Q6385295',
    'Keiyo South': 'Q17088491',
    'Khwisero': 'Q6403457',
    'Kiambaa': 'Q6403727',
    'Kiambu': 'Q47463427',
    'Kibra': 'Q22080473',
    'Kibwezi East': 'Q47463423',
    'Kibwezi West': 'Q47463422',
    'Kigumo': 'Q6405979',
    'Kiharu': 'Q6406003',
    'Kikuyu': 'Q6406448',
    'Kilifi North': 'Q18388215',
    'Kilifi South': 'Q47463407',
    'Kilome': 'Q6408123',
    'Kimilili': 'Q6410137',
    'Kiminini': 'Q47463434',
    'Kinango': 'Q6410376',
    'Kinangop': 'Q6410379',
    'Kipkelion East': 'Q22080475',
    'Kipkelion West': 'Q47463455',
    'Kirinyaga Central': 'Q6415320',
    'Kisauni': 'Q13123145',
    'Kisumu Central': 'Q47463472',
    'Kitui Central': 'Q10981053',
    'Kitui East': 'Q6943975',
    'Kitui Rural': 'Q47462466',
    'Kitui South': 'Q6418636',
    'Kitui West': 'Q6418638',
    'Kitutu Chache North': 'Q47463487',
    'Kitutu Masaba': 'Q6418659',
    'Konoin': 'Q6429614',
    'Kuresoi North': 'Q47463449',
    'Kuresoi South': 'Q47463448',
    'Kuria East': 'Q47463483',
    'Kuria West': 'Q47463481',
    'Kwanza': 'Q6450207',
    'Lafey': 'Q17088687',
    'Lagdera': 'Q11034978',
    'Laikipia East': 'Q6473833',
    'Laikipia North': 'Q47463445',
    'Laikipia West': 'Q6473834',
    'Laisamis': 'Q6474135',
    'Lamu East': 'Q6482731',
    'Lamu West': 'Q6482735',
    'Langata': 'Q6485732',
    'Lari': 'Q6489334',
    'Likoni': 'Q6547331',
    'Likuyani': 'Q47463458',
    'Limuru': 'Q10978796',
    'Loima': 'Q47463429',
    'Lugari': 'Q6699735',
    'Lunga Lunga': 'Q47463406',
    'Lurambi': 'Q6704894',
    'Maara': 'Q47463416',
    'Machakos Town': 'Q13123147',
    'Magarini': 'Q6729713',
    'Makadara': 'Q6738586',
    'Makueni': 'Q6740441',
    'Malava': 'Q6741420',
    'Malindi': 'Q6743727',
    'Mandera East': 'Q6747984',
    'Mandera North': 'Q47463414',
    'Mandera South': 'Q47462269',
    'Mandera West': 'Q6747986',
    'Manyatta': 'Q6753394',
    'Maragua': 'Q6754641',
    'Marakwet East': 'Q6754698',
    'Marakwet West': 'Q6754691',
    'Masinga': 'Q6783288',
    'Matayos': 'Q24236285',
    'Mathare': 'Q47462553',
    'Mathioya': 'Q6787280',
    'Mathira': 'Q6787283',
    'Matungu': 'Q17089719',
    'Matungulu': 'Q17089728',
    'Mavoko': 'Q47463421',
    'Mbeere North': 'Q14475849',
    'Mbeere South': 'Q5516225',
    'Mbooni': 'Q6799757',
    'Mogotio': 'Q6890697',
    'Moiben': 'Q47463437',
    'Molo': 'Q6896735',
    'Mosop': 'Q6916414',
    'Moyale': 'Q6927587',
    'Mt. Elgon': 'Q6930268',
    'Muhoroni': 'Q13651057',
    'Mukurweini': 'Q6933680',
    'Mumias East': 'Q47463462',
    'Mumias West': 'Q47463461',
    'Mvita': 'Q6944580',
    'Mwala': 'Q6944627',
    'Mwatate': 'Q6944699',
    'Mwea': 'Q6944711',
    'Mwingi Central': 'Q47463420',
    'Mwingi North': 'Q6944742',
    'Mwingi West': 'Q47463419',
    'Naivasha': 'Q6959832',
    'Nambale': 'Q6961369',
    'Nandi Hills': 'Q47463441',
    'Narok East': 'Q24236157',
    'Narok West': 'Q47463453',
    'Navakholo': 'Q47463460',
    'Ndhiwa': 'Q6983737',
    'Ndia': 'Q6983741',
    'Njoro': 'Q47463446',
    'North Horr': 'Q7055666',
    'North Imenti': 'Q7055691',
    'North Mugirango': 'Q7056156',
    'Nyakach': 'Q7070809',
    'Nyali': 'Q47463398',
    'Nyando': 'Q7070870',
    'Nyaribari Chache': 'Q7070906',
    'Nyaribari Masaba': 'Q7070904',
    'Nyatike': 'Q7070932',
    'Nyeri Town': 'Q7071069',
    'Ol Jorok': 'Q47463424',
    'Othaya': 'Q7108562',
    'Pokot South': 'Q47462472',
    'Rabai': 'Q47463408',
    'Rangwe': 'Q7292934',
    'Rarieda': 'Q7294558',
    'Rongai': 'Q7365616',
    'Rongo': 'Q7365633',
    'Ruaraka': 'Q24236499',
    'Ruiru': 'Q47463426',
    'Runyenjes': 'Q7380154',
    'Saboti': 'Q7396314',
    'Saku': 'Q7403129',
    'Samburu East': 'Q7409117',
    'Samburu North': 'Q47463432',
    'Samburu West': 'Q7409120',
    'Shinyalu': 'Q7497839',
    'Sigor': 'Q7513096',
    'Sigowet/Soin': 'Q39087469',
    'Sirisia': 'Q7530345',
    'Sotik': 'Q7563993',
    'South Imenti': 'Q7567524',
    'South Mugirango': 'Q7568008',
    'Soy': 'Q47463435',
    'Suba North': 'Q6799698',
    'Suba South': 'Q47462489',
    'Subukia': 'Q7632288',
    'Suna East': 'Q47463479',
    'Suna West': 'Q47463480',
    'Tarbaj': 'Q47463411',
    'Teso North': 'Q47463468',
    'Teso South': 'Q47463470',
    'Tetu': 'Q7706991',
    'Tharaka': 'Q7710732',
    'Thika Town': 'Q47463425',
    'Tiaty': 'Q47463443',
    'Tigania East': 'Q7801321',
    'Tigania West': 'Q7801319',
    'Tinderet': 'Q7808048',
    'Turbo': 'Q47463436',
    'Turkana Central': 'Q17099533',
    'Turkana East': 'Q47463430',
    'Turkana North': 'Q7855019',
    'Turkana South': 'Q7855020',
    'Turkana West': 'Q47463428',
    'Ugenya': 'Q7877730',
    'Ugunja': 'Q47463471',
    'Uriri': 'Q7900644',
    'Vihiga': 'Q7929042',
    'Voi': 'Q7939444',
    'Wajir East': 'Q7960716',
    'Wajir North': 'Q7960717',
    'Wajir South': 'Q7960719',
    'Wajir West': 'Q7960720',
    'Webuye West': 'Q47463466',
    'West Mugirango': 'Q7986042',
    'Westlands': 'Q3955339',
    'Wundanyi': 'Q8039242',
    'Yatta': 'Q8050290',
}

parsedMembers = []
unreconciledCounties = []
unreconciledConstituencies = []
unreconciledParties = []

PAGES = 12
PER_PAGE = 30


def cleanup(string):
    return string.strip().replace(u'’', '\'')

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

        nameRegex = re.search('(.+?) (.+), (.+)', nameUnparsed)
        memberData['honorific_string'] = nameRegex.group(1)
        memberData['honorific_id'] = HONORIFIC_MAP[nameRegex.group(1)]

        memberData['name'] = cleanup(nameRegex.group(3) + ' ' + nameRegex.group(2))

        print('    ' + memberData['name'])

        linkHref = nameLink.attrib['href']

        idRegex = re.search('\/the-national-assembly\/members\/item\/(.+)', linkHref)
        memberData['id'] = idRegex.group(1)

        memberData['url'] = cleanup('http://www.parliament.go.ke/the-national-assembly/members/item/' + memberData['id'])

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

            # Same constituency and county? Probably a women's rep
            if constituency == county:

                memberData['role'] = 'Q47484213'

                if county in COUNTY_MAP:
                    memberData['district_id'] = COUNTY_MAP[county]
                else:
                    memberData['district_id'] = 'County: "{}", Constituency: "{}"'.format(county, constituency)
                    unreconciledCounties.append(county)
                    print('      > Unreconciled county: ' + county)
            else:
                if constituency in CONSTITUENCY_MAP:
                    memberData['district_id'] = CONSTITUENCY_MAP[constituency]
                else:
                    memberData['district_id'] = 'County: "{}", Constituency: "{}"'.format(county, constituency)
                    unreconciledConstituencies.append(county)
                    print('      > Unreconciled constituency: {}'.format(constituency, county))

        parsedMembers.append(memberData)


    print '(i) Counted {} Members so far...'.format(len(parsedMembers))

print('(i) Done.')
print '(i) Counted {} Members in total'.format(len(parsedMembers))
print '<!> {} unreconciled counties:'.format(len(unreconciledCounties))
print unreconciledCounties
print '<!> {} unreconciled constituencies:'.format(len(unreconciledConstituencies))
print unreconciledConstituencies
print '<!> {} unreconciled parties:'.format(len(unreconciledParties))
print unreconciledParties

try:
    scraperwiki.sqlite.execute('DELETE FROM data')
except sqlite3.OperationalError:
    pass
scraperwiki.sqlite.save(
    unique_keys=['id'],
    data=parsedMembers)
