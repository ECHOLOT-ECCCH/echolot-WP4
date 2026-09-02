import codecs
from collections import defaultdict
from datetime import datetime
from enum import Enum
from functools import lru_cache
import logging
import json
from json.decoder import JSONDecodeError
import pickle
import re
import sys
import time
import urllib.parse
import unicodedata as ud

import SPARQLWrapper
import rdflib.namespace
import requests
from requests.exceptions import HTTPError


LOGGER = logging.getLogger(sys.argv[0])


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = ''

class Nametype(Enum):
    PREFERABLE =  "preferable"
    MARIEDNAME =  "marriedname"
    BIRTHNAME =   "birthname"
    NATIVE =      "native"
    PSEUDONYM =   "pseudonym"
    ALTERNATIVE = "alternative"

NAMEPRIORITIES = {
    Nametype.PREFERABLE.value:  6,
    Nametype.MARIEDNAME.value:  5,
    Nametype.BIRTHNAME.value:   4,
    Nametype.NATIVE.value:      3,
    Nametype.PSEUDONYM.value:   2,
    Nametype.ALTERNATIVE.value: 1
}

WIKIENDPOINT = "https://query.wikidata.org/sparql"
wikiwrapper = SPARQLWrapper.SPARQLWrapper(WIKIENDPOINT,
                        agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 Chrome/50.0.2661.102 Safari/537.36')
wikiwrapper.setReturnFormat(SPARQLWrapper.JSON)
wikiwrapper.setMethod(SPARQLWrapper.POST)
wikiwrapper.setTimeout(5*60)

ULANENDPOINT = "http://vocab.getty.edu/sparql"
ulanwrapper = SPARQLWrapper.SPARQLWrapper(ULANENDPOINT)
ulanwrapper.setReturnFormat(SPARQLWrapper.JSON)
ulanwrapper.setMethod(SPARQLWrapper.POST)
ulanwrapper.setTimeout(5*60)


REPLACE_NON_LATIN = str.maketrans(
    "ÁȺÂÅÆÇÈÉĚÍÓÔÖÜÝàáâãäⱥæāąçèéêěëėēļģğíîïīıķñńņóôöōõøřúûüūýżžźăćČčĘİłňœŠŚšşßțÚŮŽŻАВЕОСŇ",
    "AAAAACEEEIOOOUYaaaaaaaaaceeeeeeelggiiiiiknnnooooooruuuuyzzzacCcEIlnoSSssstUUZZABEOCN")
# "Délégation Norvégienne".translate(REPLACE_NON_LATIN)

_caps = ''.join([chr(n) for n in range(65,91)])
REPLACE_NON_LATIN_LOWERCASE = str.maketrans(
     "ÁȺÂÅÆÇÈÉĚÍÓÔÖÜÝàáâãäⱥæāąçèéêěëėēļģğíîïīıķñńņóôöōõøřúûüūýżžźăćČčĘİłňœŠŚšşßțÚŮŽŻАВЕОСŇ" + _caps,
    ("AAAAACEEEIOOOUYaaaaaaaaaceeeeeeelggiiiiiknnnooooooruuuuyzzzacCcEIlnoSSssstUUZZABEOCN" + _caps).lower())
# "Délégation Norvégienne".translate(REPLACE_NON_LATIN_LOWERCASE)

def getcleanchars():
    dcct ,arr = {}, [('áàâā', 'a'), ('ćčç', 'c'), ('èéë', 'e'),
                    ('æǽ', 'ä'), ('ł', 'l'), ('ńñ', 'n'), ('š', 's'),('ü', 'y'),
                    ('Žẓźžż', 'z'), ('óóôō', 'o'), ('œø','ö'), ('úù', 'u'),
                    ('"→()/0123456789,.;:?!&[]\'-', '')
                    ]
    [[dcct.setdefault(k,v) for k in arr] for arr,v in arr]
    return str.maketrans(dcct)
CLEANCHARS = getcleanchars()


def splitname(st):
    st = re.sub(r'\s*?\([^)]+\)$', '', re.sub(r'\s+', ' ', st).strip())

    # Hessenstein, Fredrik Vilhelm von
    m = re.match(r'^^(?P<family_name>[^,]+),\s+(?P<given_name>[^,]+)\s+((?:(?P<nobiliary_particle>af|av|da|Da|De|d[ae][nlmrs]*|de la|di|du|d.\s*[yä]\.|e|i|y|Natt|och|of|und|la|La|le|Le|las*|les*|sr|junior|[jJ]r.|van|von|Von|ten|yngre|zu|äldre)\s*)+)$', st) or \
        re.match(r'^(?P<family_name>[^,]+),\s+(?P<given_name>[^,]+)$', st) or \
        re.match(r'^(?P<given_name>.+?)\s+?(?P<family_name>(Svinhu\w+ a. Qval\w+|H.ort a. Ornäs|Boije a. Gen\w+|Munck a. Ful\w+|W.ede a. Elim.|Jäger\w+ a. Spu\w+|Cronh\w+ a. Hak\w+|Sparre a. Söfd\w+|Häste\w+ a. Målar\w+|Horn	a. [A-ZÖÄÅ]\w+|[CK]lodt v.n J.rgen\w+|Bernadotte a. [A-ZÖÄÅ]\w+))$', st) or \
        re.match(r'^(?P<given_name>.+?)\s+?((?:(?P<nobiliary_particle>af|av|da|Da|De|d[ae][nlmrs]*|de la|di|du|d.\s*[yä]\.|e|i|y|Natt|och|of|und|la|La|le|Le|las*|les*|sr|junior|[jJ]r.|van|von|Von|ten|yngre|zu|äldre)\s+)+)(?P<family_name>.+)$', st) or \
        re.match(r'^(?P<given_name>.+)\s+?(?P<family_name>\S+)$', st)
    if m:
        return m.groupdict()
    else:
        print(f"Not able to split '{st}'")
        return re.match(r'(?P<family_name>.+)$', st).groupdict()
    return None


def getInitials(st):
    return re.sub(r'(\w)\S*(\s|$)', r'\1', st)


def checkRealIdentiesInKanto(ids: list):
    arr = []
    requestDatabase(queryfnc = kantoredirect,
                    VALUES = [f'<{w}>' for w in ids],
                    arr = arr,
                    resultlimit = 20000,
                    endpoint = KANTOENDPOINT)
    if len(arr):
        return dict([(ob['kanto'], ob['kanto2']) for ob in arr])
    else:
        return {}


def kantoredirect(VALUES):
    return """
    PREFIX rdaa: <http://rdaregistry.info/Elements/a/>
    PREFIX dc: <http://purl.org/dc/terms/>
    PREFIX finaf: <http://urn.fi/URN:NBN:fi:au:finaf:>

    SELECT DISTINCT ?kanto ?kanto2
    WHERE {
    VALUES ?kanto { <VALUES> }
    { # 'henkilön todellinen identiteetti' ks. esim. https://finto.fi/finaf/fi/page/000078833
        ?kanto rdaa:P50316*/rdaa:P50429 ?kanto2 
    } 
    UNION
    {
        ?kanto dc:isReplacedBy ?kanto2
    }
    UNION
    { # 'henkilöön liittyvä henkilö' ks esim. https://finto.fi/finaf/fi/page/000111797
        ?kanto rdaa:P50316 ?kanto2 .
        FILTER (!(?kanto2 in (finaf:000061228, finaf:000196162))) # Tre Herrar, usean henkilön pseudonyymi
        FILTER(STR(?kanto2)<STR(?kanto))
    }
    FILTER NOT EXISTS { ?kanto2 rdaa:P50429 [] }
    } """.replace('<VALUES>', VALUES)


def checkFintoToKanto(ids: list):
    '''relink organizations from wikidata '''
    arr = []
    requestDatabase(queryfnc = finto_to_kanto_query, 
                    VALUES = [f'<{w}>' for w in ids], 
                    arr = arr,
                    resultlimit = 2000,
                    endpoint = KANTOENDPOINT)
    if len(arr):
      return dict([(ob['finto'], ob['kanto']) for ob in arr])
    else:
      return {}
    
def finto_to_kanto_query(VALUES):
   ''' https://api.triplydb.com/s/lX5n7By-J '''
   return """prefix cn: <http://urn.fi/URN:NBN:fi:au:cn:> 
    prefix dct: <http://purl.org/dc/terms/> 
    PREFIX finaf: <http://urn.fi/URN:NBN:fi:au:finaf:>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    SELECT DISTINCT ?finto ?kanto
    WHERE {
        VALUES ?finto { <VALUES> }
      
      ?finto owl:deprecated true ; 
        dct:isReplacedBy ?kanto .
    } """.replace('<VALUES>', VALUES)

def kantoredirect_OLD(VALUES):
  return """PREFIX rdaa: <http://rdaregistry.info/Elements/a/>
  SELECT DISTINCT ?kanto ?kanto2
  WHERE {
    VALUES ?kanto { <VALUES> }
    ?kanto rdaa:P50429 ?kanto2 
  } """.replace('<VALUES>', VALUES)


def checkOutdatedLinksInWikidata(wikis : list):
  '''Check possible outdated Wikidata links 

  http://www.wikidata.org/entity/Q105704780
  wd:OLD owl:sameAs wd:NEW
  '''
  wikires = []

  requestDatabase(queryfnc=wikiupdate, VALUES = [f'<{w}>' for w in wikis], arr = wikires, resultlimit=20000)

  if len(wikires):
    return dict([(ob['wiki'], ob['wiki2']) for ob in wikires])
  else:
    return {}


def wikiupdate(VALUES):
  return """PREFIX owl: <http://www.w3.org/2002/07/owl#>
  PREFIX wdt: <http://www.wikidata.org/prop/direct/> 
  SELECT DISTINCT ?wiki ?wiki2 WHERE {
    VALUES ?wiki { <VALUES> }
    ?wiki owl:sameAs ?wiki2 .
    FILTER(REGEX(STR(?wiki2), 'entity/Q') && STR(?wiki) != STR(?wiki2))
    ?wiki2 wdt:P31 [] ; rdfs:label [] .
  } """.replace('<VALUES>', VALUES)


def requestDatabase(VALUES, arr, queryfnc = wikiupdate, resultlimit=1000, endpoint=WIKIENDPOINT):
    '''Performs a SPARQL query to a given endpoint. In a case of timeout, divides the list VALUES into smaller chuncks.
    queryfnc: a function returning the SPARQL query based by value list VALUES
    VALUES: see above
    resultlimit: limit the size of values block
    endpoint: default to Wikidata server
    arr: a list where the results are collected
    return: None, however results collected to parameter list 'arr'
    '''
    if len(VALUES)==0: return
    try:
        if len(VALUES)>resultlimit:
            # if exceeded the 'resultlimit' value, chop the VALUES into smaller chunchs 
            LOGGER.info("data size {}".format(len(VALUES)))
            requestDatabase(VALUES[:len(VALUES)>>1], arr, queryfnc, resultlimit=resultlimit, endpoint=endpoint)
            requestDatabase(VALUES[len(VALUES)>>1:], arr, queryfnc, resultlimit=resultlimit, endpoint=endpoint)
        else:
            arr += makeSparqlQuery(queryfnc('\n'.join(list(VALUES))), endpoint)
            LOGGER.info("Currently {} results".format(len(arr)))
    except HTTPError as e:
        LOGGER.debug(str(e))
        if '413 Client Error' in str(e):
            # if query failed, chop the VALUES into smaller chunchs 
            LOGGER.info('Data size'+str(len(VALUES))+'trying with smaller requests')
            requestDatabase(VALUES[:len(VALUES)>>1], arr, queryfnc, resultlimit=resultlimit, endpoint=endpoint)
            requestDatabase(VALUES[len(VALUES)>>1:], arr, queryfnc, resultlimit=resultlimit, endpoint=endpoint)
        elif '500 Server Error' in str(e) or \
            '403 Client Error' in str(e):
            # sleep and retry
            if len(VALUES)>1:
                LOGGER.info('Server Error - retry in 3 seconds')
                time.sleep(3)
                requestDatabase(VALUES[:len(VALUES)>>1], arr, queryfnc, resultlimit=resultlimit, endpoint=endpoint)
                requestDatabase(VALUES[len(VALUES)>>1:], arr, queryfnc, resultlimit=resultlimit, endpoint=endpoint)
        else:
            # here, ignore other error types
            LOGGER.info("Error {} occured.".format(e))
            pass # raise e

def makeSparqlQuery(query, endpoint="http://ldf.fi/yoma/sparql"):
    try:
        r = requests.post(endpoint,
                      data = {'query': query, 'format': 'json'},
                      headers = {'Accept': 'application/sparql-results+json',
                                      'User-Agent': 'OpenAnything/1.0 +http://diveintopython.org/http_web_services/'})
        
        if r.status_code != requests.codes.ok:
            r.raise_for_status()
        try:
            cont = json.loads(r.text)
        except JSONDecodeError as e:
            print(f"Malformed answer: {e}")
            print(r.text)
            return []
        
        # json.decoder.JSONDecodeError
        fields = cont['head']['vars']
        
        bind = cont['results']['bindings']
        
        res = []
        for x in bind:
            row = {}
            for f in fields:
                if f in x and 'value' in x[f] and x[f]['value'] != "":
                    '''
                    if x[f].get('type') == 'literal' and 'xml:lang' in x[f]:
                      # String with langtag
                      row[f] = Literal(x[f].get('value').strip(), lang=x[f].get('xml:lang'))
                    else:
                    '''
                    row[f] = x[f]['value']
            res.append(row)
        return res
    
    except Exception as e:
        # KeyError: no result
        print(query)
        raise e
    return []


def unquoteWikipediaURL(s: str) -> str:
    '''For unquoting Wikipedia URL
    >>> encodeWikipediaURL('Valter_Nystr%C3%B6m_%28j%C3%A4%C3%A4k%C3%A4ri%29')
    "Valter_Nyström_(jääkäri)"
    '''
    return urllib.parse.unquote(s.split('#')[0])


@lru_cache(maxsize=200)
def checkWikipediaRedict(url, api = 'https://fi.wikipedia.org/w/api.php'):
    ''' Performs APi query:
    https://fi.wikipedia.org/w/api.php?action=query&titles=Johannes_V._Jensen&redirects&format=json
    returns:
    exists: bool if page exists
    s2: str URL of redirected page
    '''

    query = requests.get(api,
                        params=dict(action='query',
                            titles=url,
                            format='json',
                            redirects=True),
                        headers={"User-Agent": 'Chrome/77.0.3865.90'}) 
    try:
        data = json.loads(query.text)
        if (directs := data.get('query', {}).get('redirects', {})) and len(directs):
            to = directs[0].get('to')
            return True, to.replace(' ', '_')
        elif (pages := data.get('query', {}).get('pages', {})) and "-1" in pages:
            return False, None
    except Exception as e:
        print(f'Error "{e}" occured while quering {url}')
    return True, None


latin_letters= {}
def is_latin(uchr):
    try: return latin_letters[uchr]
    except KeyError:
         return latin_letters.setdefault(uchr, 'LATIN' in ud.name(uchr))


def only_roman_chars(unistr):
    '''check that labels contain only latin letters
    https://stackoverflow.com/questions/3094498/how-can-i-check-if-a-python-unicode-string-contains-non-western-letters
    '''
    return all(is_latin(uchr)
           for uchr in unistr
           if uchr.isalpha())


def qualifyName(st, verbose=False, stoplist=[]):
    if st and only_roman_chars(st):
        if re.search(r'\d',st):
            if verbose:
                print(f'Rejected "{st}"')
            return False
        elif re.match(r'[^()]+[)]',st) or re.search(r'[(][^)]+$',st):
            if verbose:
                print(f'Rejected "{st}"')
            return False
        elif st in stoplist:
            if verbose:
                print(f'Rejected "{st}"')
            return False
        return True
    if verbose:
        print(f'Rejected "{st}"')
    return False


def mapResults(res: list, keys: list = ['label', 'altLabel', 'label_sv', 'altLabel_sv', 'label_en', 'altLabel_en']):
    '''#
    '''
    dc = defaultdict(lambda: defaultdict(set))
    for ob in res:
        for k,v in ob.items():
            dc[ob.get('id')][k].add(v)

    for _, dct in dc.items():
        seen = []
        for key in keys:
            s, s2 = dct.get(key), []
            if s:
                # print('s',s)
                for st in dct.get(key, []):
                    if st.lower() in seen:
                        # print(f'del {key}: {st}')
                        ...
                    else:
                        seen.append(st.lower())
                        s2.append(st)
                
                # print('s2',s2)
                if s2:
                    dct[key] = s2
                else:
                    del dct[key]

    for _, dct in dc.items():
        yield dict((k,'|'.join((str(x) for x in v))) for k,v in dct.items())
        '''
        n = max((len(v) for v in dct.values()))
        for i in range(n):
            newob = dict((k,list(v)[min(i, len(v)-1)]) for k,v in dct.items())
            yield newob
        '''

from rdflib import Namespace
DC =    Namespace('http://purl.org/dc/elements/1.1/')
SNELLMAN = Namespace('http://ldf.fi/snellman/')
SCHEMA =Namespace('https://schema.org/')
SKOSXL =Namespace("http://www.w3.org/2008/05/skos-xl#")
TIME =  Namespace("http://www.w3.org/2006/time#")
SAMPO =  Namespace('http://ldf.fi/sampo/')
SAMPOS = Namespace('http://ldf.fi/schema/sampo/')
DATASETS = Namespace('http://ldf.fi/sampo/datasets/')
GROUPS = Namespace('http://ldf.fi/sampo/groups/')
PEOPLE = Namespace('http://ldf.fi/sampo/people/')
PLACES = Namespace('http://ldf.fi/sampo/places/')
PROXIES = Namespace('http://ldf.fi/sampo/proxies/')
LABELS = Namespace('http://ldf.fi/sampo/labels/')
TIMES = Namespace('http://ldf.fi/sampo/times/')
RELSE = Namespace('http://ldf.fi/relse/')

def initGraph() -> rdflib.Graph:
    import rdflib
    g = rdflib.Graph()
    g.bind('dc', rdflib.namespace.DC)
    g.bind('dcterms', rdflib.namespace.DCTERMS)
    g.bind('datasets', DATASETS)
    g.bind('foaf', rdflib.namespace.FOAF)
    g.bind('schema', SCHEMA)
    g.bind('skos', rdflib.namespace.SKOS)
    g.bind('xl', SKOSXL)
    g.bind('sampo', SAMPO)
    g.bind('sampos', SAMPOS)
    g.bind('time', TIME)
    g.bind('times', TIMES)
    g.bind('groups', GROUPS)
    g.bind('people', PEOPLE)
    g.bind('places', PLACES)
    g.bind('proxies', PROXIES)
    g.bind('time', TIME)
    g.bind('labels', LABELS)
    return g

def parseFiles(files):
    '''Parse a list of files into one rdflib.Graph object
    files: list a ttl/pickle -files
    return: rdflib.Graph
    '''
    g = initGraph()
    for f in files:
        g_add = initGraph()
        try:
            if re.search(r'\.ttl$', f):
                # read turtle file
                g_add.parse(f, format="turtle")
            elif re.search(r'pi*ckl*e*$', f):
                # read pickle file
                g_add = pickle.load(open( f, "rb" ))
        except Exception as e:
            print("Error {} while reading file {}.".format(e, f))
        print("Parsed {} triples from {}".format(len(g_add), f))
        g += g_add
    return g


def saveGraphs(tuples, silent=False):
    '''Writes multiple rdflib.Graphs to files
    tuples: a list of tuples in format (G: rdflib.Graph, file: str)
    silent: boolean for logging/not logging the process
    '''
    for g, outfile in tuples:
        
        if len(g):

            args = sys.argv

            if re.search(r'\.ttl$', outfile):
                # save turtle
                outf = codecs.open(outfile, encoding='utf-8', mode='w')

                # write header
                outf.write("# Created with script {}\n".format(args[0]))

                # command that created this file
                outf.write("# python {}\n".format(' '.join(args)))

                # date of writing file
                now = datetime.now()
                outf.write("# {}\n\n".format(now.strftime("%Y-%m-%d %H:%M")))

                # g.serialize(destination=outfile, format='turtle')
                try:
                    outf.write( g.serialize(format='turtle') )
                except AttributeError as e:
                    try:
                        # some differences in rdflib versions
                        outf.write( g.serialize(format='turtle').decode("utf-8") )
                        LOGGER.debug(f'Error {e} while writing {outfile}')
                        
                    except Exception as e:
                        LOGGER.error("Error {} occured while saving the output".format(e))

                outf.close()
            elif re.search(r'\.pi*ckl*e*$', outfile):
                # save as an pickle file
                pickle.dump(g, open( outfile, "wb" ) )

            if not silent:
                LOGGER.info("{} triples saved to {}".format(len(g),outfile))

            #if not checkSamplefile(g, outfile):
            #    saveSampleGraph(g, outfile, silent=True)

        elif not silent:
            LOGGER.info("No output to {}".format(outfile))


if __name__ == '__main__':
    #ids = ['<http://www.wikidata.org/entity/Q105705590>']
    #lookup = checkOutdatedLinksInWikidata(ids)
    #print(lookup)

    ids = ['http://urn.fi/URN:NBN:fi:au:finaf:000096713',
        'http://urn.fi/URN:NBN:fi:au:finaf:000096713',
        'http://urn.fi/URN:NBN:fi:au:finaf:000194255']
    lookup = checkRealIdentiesInKanto(ids)
    print(lookup)
