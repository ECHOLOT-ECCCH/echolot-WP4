import requests
import time

def safe_request(url, params, headers, max_retries=3, delay=1):
    """
    Hace una request con reintentos si falla o no devuelve JSON válido
    """
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)

            # errores HTTP
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")

            # intentar parsear JSON
            return r.json()

        except Exception as e:
            print(f"[WARN] Description: intento {attempt+1} fallido: {e}")

            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))  # backoff progresivo
            else:
                print("[ERROR] Description: todos los intentos fallaron")
                return None


def wikidata_description(QID):

    URL = "https://query.wikidata.org/sparql"

    HEADERS = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "MiAppPython/1.0 (adrian.cuadron@ehu.eus)"
    }


    query2 = f"""

    SELECT  ?item 
        ?itemLabel
        (group_concat(distinct ?label; SEPARATOR="|") as ?aliases)
        (YEAR(?birth) as ?birthDate) (YEAR(?death) as ?deathDate)
        (group_concat(distinct ?nationalityLabel; SEPARATOR="|") as ?nationalities)
        (group_concat(distinct ?occupationLabel; SEPARATOR="|") as ?occupations)
        (group_concat(distinct ?genderLabel; SEPARATOR="|") as ?genders)
        (group_concat(distinct ?birthPlaceLabel; SEPARATOR="|") as ?birthplaces)
        (sample(?image) as ?image_link)
        ?itemDescription

    WHERE {{
    BIND(wd:{QID} AS ?item)
    values ?language {{"en" "es" "fr" "eu" "mul"}}
    ?item rdfs:label|skos:altLabel ?lang_label.
      filter(lang(?lang_label) = ?language)
      bind(str(?lang_label) as ?label)
    
     OPTIONAL {{ ?item wdt:P569 ?birth. }}
     OPTIONAL {{ ?item wdt:P570 ?death. }}
     OPTIONAL {{ ?item wdt:P27 [rdfs:label ?nationalityLabel]. filter(lang(?nationalityLabel)="en") }}
     OPTIONAL {{ ?item wdt:P106 [rdfs:label ?occupationLabel]. filter(lang(?occupationLabel)="en") }}
     OPTIONAL {{ ?item wdt:P21 [rdfs:label ?genderLabel]. filter(lang(?genderLabel)="en") }}
     OPTIONAL {{ ?item wdt:P19 [rdfs:label ?birthPlaceLabel]. filter(lang(?birthPlaceLabel)="en") }}
     OPTIONAL {{ ?item wdt:P18 ?image. }}

    SERVICE wikibase:label {{bd:serviceParam wikibase:language "en,es,eu,fr,mul".}}
    }} group by ?item ?itemLabel ?aliases ?birth ?death ?nationalities ?occupations ?genders ?birthplaces ?image_link ?itemDescription"""

    data2 = safe_request(URL, {"query": query2}, HEADERS)

    info = {
        "nombre": None,
        "alias": set(),
        "descripcion": None,
        "fecha_nacimiento": None,
        "fecha_muerte": None,
        "nacionalidad": set(),
        "ocupacion": set(),
        "genero": None,
        "lugar_nacimiento": None,
        "imagen": None
    }

    if data2:
        for item in data2.get("results", {}).get("bindings", []):

            if "itemLabel" in item:
                info["nombre"] = item["itemLabel"]["value"]

            if "aliases" in item:
                info["alias"] = set(item["aliases"]["value"].split("|"))
            
            if "itemDescription" in item:
                info["descripcion"] = item["itemDescription"]["value"]

            if "birthDate" in item:
                info["fecha_nacimiento"] = item["birthDate"]["value"]

            if "deathDate" in item:
                info["fecha_muerte"] = item["deathDate"]["value"]

            if "nationalities" in item:
                info["nacionalidad"].add(item["nationalities"]["value"])

            if "occupations" in item:
                info["ocupacion"].add(item["occupations"]["value"])

            if "genders" in item:
                info["genero"] = item["genders"]["value"]

            if "birthplaces" in item:
                info["lugar_nacimiento"] = item["birthplaces"]["value"]

            if "image_link" in item:
                info["imagen"] = item["image_link"]["value"]



    resultado = {
        "name": info["nombre"],
        "alias": list(info["alias"]),
        "info": {
            "description": info["descripcion"],
            "birth_date": info["fecha_nacimiento"],
            "death_date": info["fecha_muerte"],
            "nationality": list(info["nacionalidad"]),
            "occupation": list(info["ocupacion"]),
            "gender": info["genero"],
            "birth_place": info["lugar_nacimiento"],
            "image": info["imagen"]
        }
    }

    return resultado


def wikidata_lexical_search(query, limit=10, max_retries=3):
    URL = "https://www.wikidata.org/w/api.php"

    HEADERS = {
        "User-Agent": "MyBotNEL/1.0 (adrian.cuadron@ehu.eus)"
    }

    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit
    }

    for attempt in range(max_retries):
        try:
            r = requests.get(URL, params=params, headers=HEADERS, timeout=10)

            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")

            data = r.json()

            results = []
            for item in data.get("query", {}).get("search", []):
                results.append({
                    "QID": item["title"],  # esto ya es el QID
                    "snippet": item.get("snippet")
                })

            return results

        except Exception as e:
            print(f"[WARN] intento {attempt+1} fallido: {e}")
            time.sleep(5 + attempt)

    return []