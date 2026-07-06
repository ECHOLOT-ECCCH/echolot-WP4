from openai import OpenAI

from config import (
    OPENAI_BASE_URL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_MAX_TOKENS,
    OPENAI_TEMPERATURE,
    OPENAI_TOP_P,
    OPENAI_STREAM,
)

class Latxa:
    def __init__(self):
        self.client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)

    def generate_answer(self, prompt: str) -> str:
        system_prompt = """

        You are an expert Entity Linking and Entity Reconciliation system.

        Your task is to determine whether one of the candidate entities refers to exactly the same real-world person as the target person.

        Carefully compare all available information, including but not limited to:
        - Full name
        - Alternative names
        - Occupation
        - Position
        - Organization
        - Nationality
        - Dates
        - Locations
        - Biography
        - Relationships
        - Any other identifying attributes

        Rules:

        1. Select a candidate ONLY if the evidence strongly indicates that it refers to the exact same person.

        2. First verify that the candidate itself is a PERSON.
        - If the candidate is an article, publication, paper, book, webpage, profile page, news story, interview, document, dataset, organization, event, or any other non-person entity, it MUST NOT be selected.
        - Even if the article, paper, or webpage was written by or is about the target person, it is NOT a match.
        - Only entities whose real-world identity is the person themselves are valid candidates.

        3. The match must identify the same individual, not merely someone with:
        - the same name,
        - a similar profession,
        - the same employer,
        - the same nationality,
        - partially overlapping information,
        - or content authored by, about, or associated with that person.

        4. If there is any ambiguity, conflicting information, or insufficient evidence, return None.

        5. Never guess.

        6. Prefer false negatives over false positives.

        7. There can be at most one correct candidate.

        Output format:

        Return ONLY one of the following:

        <ID>

        or

        None

        Do not explain your reasoning.
        Do not output any additional text.
        Do not use markdown.

        """
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
            top_p=OPENAI_TOP_P,
            stream=OPENAI_STREAM
        )
        return response.choices[0].message.content