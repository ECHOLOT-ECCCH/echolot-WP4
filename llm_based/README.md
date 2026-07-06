# Entity Linking and Reconciliation via LLMs

This project retrieves and ranks candidate **Wikidata entities** for records from a knowledge base. Given an input entity (typically a person) and its metadata, the system performs lexical retrieval over Wikidata and resolves entity ambiguities to identify the correct Wikidata entity.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

Run the system with:

```bash
python3 main.py data/20k_authors_v2_toy.json --id=wikidata --toy
```

### Arguments

| Argument     | Description                                         |
| ------------ | --------------------------------------------------- |
| `--input_file` | JSON file containing the input entities.            |
| `--id`       | Identifier to use for retrieval (e.g. `wikidata`).  |
| `--toy`      | Runs the system on a small toy dataset for testing. |

---

## Input Format

Each input entity must follow the structure below:

```json
{
  "uri": "https://wikibase.inguma.eus/entity/Q1265",
  "name": "Estibaliz Rodriguez Nuñez",
  "entity_type": "person",
  "identifiers": {
    "wikidata": "http://www.wikidata.org/entity/Q130759789"
  },
  "information": {
    "gender": "female",
    "publication": "(2020) Familia-enpresen orientazio ekintzailea Mendebaldeko Saharan: testuinguruaren garrantzia",
    "affiliation": "Euskal Herriko Unibertsitatea"
  }
}
```

---

## Output Format

For each input entity, the system returns:

* the selected Wikidata identifier by the LLM (`chosen_id`)
* a ranked list of retrieved candidates
* a structured description for every candidate

Example:

```json
{
  **,
  "chosen_id": "Q130759789",
  "retrieval_results": [
    {
      "QID": "Q130759789",
      "snippet": "researcher",
      "description": {
        "name": "Estibaliz Rodriguez Nuñez",
        "alias": [
          "Estibaliz Rodriguez Nuñez"
        ],
        "info": {
          "description": "researcher",
          "birth_date": null,
          "death_date": null,
          "nationality": [""],
          "occupation": [
            "researcher"
          ],
          "gender": "female",
          "birth_place": "",
          "image": null
        }
      }
    },
    {
      "QID": "Q126809450",
      "snippet": "scholarly article",
      "description": {
        "name": null,
        "alias": [],
        "info": {
          "description": null,
          "birth_date": null,
          "death_date": null,
          "nationality": [],
          "occupation": [],
          "gender": null,
          "birth_place": null,
          "image": null
        }
      }
    }
  ]
}
```

---

## Project Structure

```text
.
├── data/
│   └── 20k_authors_v2_toy.json
├── main.py
├── inguma_recon.py
├── latxa_recon.py
├── wikidata_tools.py
├── requirements.txt
└── README.md
```

---

## Requirements

The project depends on:

* Python 3.10+
* requests
* tqdm
* openai
* python-dotenv

Install them with:

```bash
pip install -r requirements.txt
```

---

