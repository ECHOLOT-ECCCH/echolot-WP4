import json
import argparse
from inguma_recon import obtain_ids_from_wikidata

def main(input_file: str, kb_id: str, toy: bool):
    # READ THE JSON FILE
    with open(input_file, 'r', encoding='utf-8') as infile:
        data = json.load(infile)

    # filter the ones that do not have the wikidata in "identifiers"
    if kb_id:
        data = [
            r for r in data
            if kb_id in r.get("identifiers", {})
        ]

    if toy:
        data = data[:5]  # Process only the first 5 items for testing

    print(len(data))
    output_path = input_file.replace('.json', '') + '_results.jsonl'

    # CALL TO THE SYSTEM
    output_data = obtain_ids_from_wikidata(data, output_path=output_path)

    print(f"Results written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the reconciliation results.")
    parser.add_argument("--input_file", type=str, required=True, help="Path to the input JSON file.")
    parser.add_argument("--id", type=str, required=True, help="Knowledge base ID to evaluate against, if any.")
    parser.add_argument("--toy", action="store_true", help="Process only a small subset of data for testing.")

    args = parser.parse_args()

    main(args.input_file, args.id, args.toy)