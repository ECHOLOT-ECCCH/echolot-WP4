import json, time
from tqdm import tqdm
from latxa_recon import Latxa
from wikidata_tools import wikidata_description, wikidata_lexical_search

def latxa_desambiguation_answer(latxa: Latxa, querystring, information, context, results_descriptions):
    if not results_descriptions:
        return 'None'
        
    if context:
        context_text = f"\nThe name appears in the following context: {context}"
    else:
        context_text = ""

    if information:
        information = f"\nAdditional information about the person: {information}"
    else:        
        information = ""

    prompt = (
        f"Given the following name, identify the most relevant Wikidata QID for the name described.\n"
        f"Target person: {querystring}"
        f"{information}"
        f"{context_text}\n\n"
        f"\n\nCandidates:\n\n{results_descriptions}\n\n"
        f"Output only the QID or 'None'."
    )

    return latxa.generate_answer(prompt)


def latxa_desambiguation(latxa: Latxa, querystring, information, context, results, top_k=5):
    # Placeholder for the actual desambiguation logic
    if not results:
        print("No results to disambiguate.")
        return 'None'

    results_top_k = results[:top_k]

    # access to wikidata information (SPARQL) to get the description of each result
    for result in results_top_k:
        result['description'] = wikidata_description(result['QID'])

    results_descriptions = [{'QID': result['QID'], 'description': result['description']} for result in results_top_k]

    # with open("debug_results.json", "w", encoding="utf-8") as f:
    #     json.dump(results, f, ensure_ascii=False, indent=2)

    return latxa_desambiguation_answer(latxa, querystring, information, context, results_descriptions)


def obtain_correct_qid_lexical(latxa: Latxa, authorname: str, information: str = "", context: str = ""):

    results = wikidata_lexical_search(authorname, limit=50)

    desambiguation_result = latxa_desambiguation(latxa, authorname, information, context, results) # returns a QID or 'None'

    if desambiguation_result != 'None' and not any(result['QID'] == desambiguation_result for result in results):
        print(f"⚠️ Warning: Latxa returned {desambiguation_result} which is not in the results. Setting desambiguation result to 'None'.")
        desambiguation_result = 'None'

    if results:
        output = {
            "querystring": authorname,
            "desambiguation_result": desambiguation_result,
            "correct_qid": desambiguation_result,
            "position": next((i for i, result in enumerate(results) if result['QID'] == desambiguation_result), -1),
            "full_results": results,
            "results": results[:5]  # limit to top 5 results
        }
    else:
        output = {
            "querystring": authorname,
            "desambiguation_result": 'None',
            "correct_qid": 'None',
            "position": -1,
            "full_results": [],
            "results": []
        }

    return output


def obtain_ids_from_wikidata(data: list[dict], use_vector: bool = False, output_path: str = "results.jsonl"):
    
    latxa = Latxa()
    
    output_data = []

    with open(output_path, 'a', encoding='utf-8') as outfile:
        for row in tqdm(data):

            time.sleep(5)

            uri = row.get("uri", "")
            name = row.get("name", "")
            entity_type = row.get("entity_type", "")
            information = row.get("information", {})
            publication = information.get('publication', [])
            
            # LIMIT THE LENGTH OF PUBLICATIONS TO first 5
            information['publication'] = (publication[:5] if isinstance(publication, list) else publication)
            context = row.get("context", "")

            output = obtain_correct_qid_lexical(latxa, name, information=information, context=context)

            results = output['full_results']

            row['chosen_id'] = output['desambiguation_result']
            row['retrieval_results'] = results
            
            output_data.append(row) 

            outfile.write(json.dumps(row, ensure_ascii=False) + "\n")

            time.sleep(1)

    return output_data