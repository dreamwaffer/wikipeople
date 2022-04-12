from urllib.request import urlopen
import requests
import xmltodict
import json
import asyncio
import aiohttp


# Get all pages from a
def getPages(outFile):
    url = "https://petscan.wmflabs.org/?format=json&psid=21581706"

    # This URL is just a full query and can be used in case the PSID (which PetScan documentations consider stable)
    # ever stopped working
    # url = "https://petscan.wmflabs.org/?edits%5Bflagged%5D=both&language=en&search_max_results=500&cb_labels_no_l=1&edits%5Banons%5D=both&categories=1900_births%0A1901_births%0A1902_births%0A1903_births%0A1904_births%0A1905_births%0A1906_births%0A1907_births%0A1908_births%0A1909_births%0A1910_births%0A1911_births%0A1912_births%0A1913_births%0A1914_births%0A1915_births%0A1916_births%0A1917_births%0A1918_births%0A1919_births%0A1920_births%0A1921_births%0A1922_births%0A1923_births%0A1924_births%0A1925_births%0A1926_births%0A1927_births%0A1928_births%0A1929_births%0A1930_births%0A1931_births%0A1932_births%0A1933_births%0A1934_births%0A1935_births%0A1936_births%0A1937_births%0A1938_births%0A1939_births%0A1940_births%0A1941_births%0A1942_births%0A1943_births%0A1944_births%0A1945_births%0A1946_births%0A1947_births%0A1948_births%0A1949_births%0A1950_births%0A1951_births%0A1952_births%0A1953_births%0A1954_births%0A1955_births%0A1956_births%0A1957_births%0A1958_births%0A1959_births%0A1960_births%0A1961_births%0A1962_births%0A1963_births%0A1964_births%0A1965_births%0A1966_births%0A1967_births%0A1968_births%0A1969_births%0A1970_births%0A1971_births%0A1972_births%0A1973_births%0A1974_births%0A1975_births%0A1976_births%0A1977_births%0A1978_births%0A1979_births%0A1980_births%0A1981_births%0A1982_births%0A1983_births%0A1984_births%0A1985_births%0A1986_births%0A1987_births%0A1988_births%0A1989_births%0A1990_births%0A1991_births%0A1992_births%0A1993_births%0A1994_births%0A1995_births%0A1996_births%0A1997_births%0A1998_births%0A1999_births%0A2000_births%0A2001_births%0A2002_births%0A2003_births%0A2004_births%0A2005_births%0A2006_births%0A2007_births%0A2008_births%0A2009_births%0A2010_births&cb_labels_yes_l=1&interface_language=en&since_rev0=&ns%5B0%5D=1&project=wikipedia&combination=union&cb_labels_any_l=1&edits%5Bbots%5D=both&minlinks=&doit"

    response = urlopen(url)  # TODO change urllib to request
    jsonData = json.loads(response.read())

    with open(outFile, "w", encoding="UTF-8") as f:
        json.dump(jsonData, f, ensure_ascii=False, indent=2)


def createYearsList(outFile):
    beginYear = 1900
    finalYear = 2010
    string = ""
    while beginYear <= finalYear:
        string += str(beginYear) + "_births\n"
        beginYear += 1

    with open(outFile, 'w', encoding="UTF-8") as f:
        f.write(string)


def createIdList(inFile, outFile):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    names = ""
    for person in people:
        if 'wikidata' in person:
            names += "wd:" + person['wikidata'] + "\n"

    with open(outFile, 'w', encoding="UTF-8") as f:
        f.write(names)


def formatJSON(inFile, outFile, indent):
    with open(inFile, 'r', encoding="UTF-8") as f:
        jsonData = json.loads(f.read())

    with open(outFile, "w", encoding="UTF-8") as f:
        json.dump(jsonData, f, ensure_ascii=False, indent=indent)


def simplifyJSON(inFile, outFile, indent):
    with open(inFile, 'r', encoding="UTF-8") as f:
        jsonData = json.loads(f.read())

    newJson = []
    people = jsonData['*'][0]['a']['*']
    for person in people:
        personData = {}
        if 'q' in person:
            personData['wikidata'] = person['q']
        if 'title' in person:
            personData['title'] = person['title']
        newJson.append(personData)

    with open(outFile, "w", encoding="UTF-8") as f:
        json.dump(newJson, f, ensure_ascii=False, indent=indent)


def createXML(inFile, outFile, indent):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    pages = []
    baseUrl = "https://en.wikipedia.org/wiki/Special:Export/"
    url = ""
    headers = {
        "User-Agent": "wikipeople-bot/0.0 (https://github.com/dreamwaffer/wikipeople; kotrblu2@fel.cvut.cz)"
    }

    for index, value in enumerate(people):
        url = baseUrl + people[index]['title']
        response = requests.get(url=url, headers=headers)
        data = xmltodict.parse(response.content)
        pages.append(data)
        print(index)

    with open(outFile, "w", encoding="UTF-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=indent)


def createXMLParallel(inFile, outFile, indent):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    print("File was read!")
    asyncio.run(main(people))


def createListOfPages(inFile, outFile):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    string = ""
    for person in people:
        string += person['title'] + "\n"

    with open(outFile, 'w', encoding="UTF-8") as f:
        f.write(string)


async def get(url, session):
    try:
        async with session.get(url=url) as response:
            resp = await response.read()
            data = xmltodict.parse(resp)
            return data
            # print("Successfully got url {} with resp of length {}.".format(url, len(resp)))
    except Exception as e:
        print("Unable to get url {} due to {}.".format(url, e.__class__))


async def main(urls):
    baseUrl = "https://en.wikipedia.org/wiki/Special:Export/"
    async with aiohttp.ClientSession() as session:
        ret = await asyncio.gather(*[get(baseUrl + url['title'], session) for url in urls])

    with open("outputs/allPeople.json", 'w', encoding="UTF-8") as f:
        json.dump(ret, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # getPages("wikipeople.json")
    # simplifyJSON("wikipeople.json", "wikipeople_simplified.json", 1)
    # createListOfPages("wikipeople_simplified.json", "list.txt")
    # createXMLParallel("wikipeople_simplified.json", "allPeople.json.", 2)
    # createIdList("wikipeople_simplified.json", "wikidataIDs.txt")
    formatJSON("outputs/tagsDictionary.json", "outputs/tagsDictionary.json", 2)
