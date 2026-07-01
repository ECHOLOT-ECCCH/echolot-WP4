"""
RuleBasedMatcher.py

A rule-based matcher for person register data across two datasheets (e.g. Wikidata CSV,
Getty ULAN TSV, or Echolot JSON). Uses phonetic blocking (Soundex) and a combination of
biographical field comparison plus fuzzy string similarity (Jaro-Winkler) to find matches.

Dependencies:
    pip install fuzzy textdistance

Usage:
    matcher = RuleBasedMatcher('datasheets/wikidata.csv')          # tab-separated CSV
    matcher = RuleBasedMatcher('datasheets/ulan.tsv', sep='\\t')   # explicit separator
    results = matcher.match_file('datasheets/source.csv')
    matcher.write_matches(results, 'datasheets/matches.tsv')
"""

import csv
import datetime
import json
import re
import unicodedata

from collections import defaultdict
import dataclasses
from dataclasses import dataclass, field
from functools import lru_cache
from math import isclose
from pathlib import Path
from typing import Optional

import fuzzy
import textdistance

# ---------------------------------------------------------------------------
# Phonetic blocking helper (module-level so lru_cache works across instances)
# ---------------------------------------------------------------------------

_soundex = fuzzy.Soundex(4)


@lru_cache(maxsize=1024)
def _get_blocking_id(label: str, use_soundex: bool = True) -> tuple:
    """
    Return a (first_token_code, last_token_code) tuple used to bucket records
    before comparing them in detail.  Uses Soundex by default; falls back to
    the first three characters (initials) when *use_soundex* is False.

    Results are cached so repeated calls with the same label are free.
    """
    def _initials(s: str) -> str:
        return s[:3]

    mapping_fn = _soundex if use_soundex else _initials
    tokens = clean_international_text(label).split()
    if tokens:
        try:
            return (mapping_fn(tokens[0]), mapping_fn(tokens[-1]))
        except UnicodeDecodeError as exc:
            print(f'Unable to decode "{label}": "{exc}"')
            # raise exc
    return (label,)


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def clean_international_text(text: str) -> str:
    """Normalise Unicode and strip non-ASCII characters."""
    normalized = unicodedata.normalize('NFKD', text)
    return normalized.encode('ASCII', 'ignore').decode('ASCII')


def _purge_row(row: dict) -> dict:
    """Strip whitespace and drop keys/values that are empty."""
    return {k.strip(): v.strip() for k, v in row.items() if k and v}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(unsafe_hash=True)
class PersonRecord:
    """Represents a single person entry from either datasheet."""
    fullname: str
    id: str = None
    matchlabel: str = field(init=False)
    gender: str = None
    wikidata: str = None
    ulan: str = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    floruit_start: Optional[int] = None
    floruit_end: Optional[int] = None

    def __post_init__(self):
        s = self.fullname.strip('"')
        if m := re.match(r'(.+), (.+)$', s):
            # Apply format "Givenname Familyname"
            s = f'{m.group(2)} {m.group(1)}'
        self.fullname = s

        self.matchlabel = clean_international_text(self.fullname).lower()

        self.wikidata = self.wikidata.strip('<>') if self.wikidata else None
        self.ulan = self.ulan.strip('<>') if self.ulan else None
        
        self.id = (self.id or '').strip('<>') or self.wikidata or self.ulan
        if self.birth_year:
            self.birth_year = int(self.birth_year)
            if not self.death_year:
                # estimated max age of 120 years
                self.death_year = self.birth_year + 120
        if self.death_year:
            self.death_year = int(self.death_year)
            # Ignore the future years used in Getty ULAN to approximate death years
            if self.death_year > datetime.datetime.now().year:
                self.death_year = None
            elif not self.birth_year:
                # estimated max age of 120 years
                self.birth_year = self.death_year - 120
        
        if self.floruit_start:
            self.floruit_start = int(self.floruit_start)
        if self.floruit_end:
            self.floruit_end = int(self.floruit_end)



    def __repr__(self) -> str:
        years = (
            f' ({self.birth_year or ""}–{self.death_year or ""})'
            if self.birth_year or self.death_year
            else ''
        )
        floruit = (
            f' (fl. {self.floruit_start or ""}–{self.floruit_end or ""})'
            if self.floruit_start or self.floruit_end
            else ''
        )
        links = (
            (f' <{self.id}>' if self.id else '') +
            (f' <{self.wikidata}>' if self.wikidata and self.wikidata != self.id else '') +
            (f' <{self.ulan}>' if self.ulan else '')
        )
        return self.fullname + (years or floruit) + links


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class RuleBasedMatcher:
    """
    Rule-based matcher for person register data.

    Parameters
    ----------
    target_file : str | Path
        Path to the *target* (reference) datasheet — e.g. ``wikidata.csv`` or
        ``ulan.tsv``.  The file is read once at construction time and indexed
        by phonetic blocking key.
    sep : str, optional
        Column separator used in *target_file*.  Defaults to ``'\\t'`` (TSV).
        Pass ``','`` for a standard CSV.
    use_soundex : bool, optional
        When *True* (default) Soundex(5) is used for phonetic blocking.
        Set to *False* to use simple 3-character initials instead.
    jaro_threshold : float, optional
        Minimum Jaro-Winkler similarity (0–1) for two name strings to be
        considered a fuzzy match.  Defaults to ``0.9``.
    score_threshold : float, optional
        Minimum combined score (name similarity + year bonuses, max ≈ 4.0)
        that a candidate pair must reach to be included in the output.
        Defaults to ``1.99`` (requires at least a near-identical name match).
    """

    def __init__(
        self,
        target_file: str | Path,
        sep: str = '\t',
        use_soundex: bool = True,
        jaro_threshold: float = 0.9,
        score_threshold: float = 1.99,
        year_tolerance: int = 0
    ):
        self.sep = sep
        self.use_soundex = use_soundex
        self.jaro_threshold = jaro_threshold
        self.score_threshold = score_threshold
        self.year_tolerance = year_tolerance
        self._dst = textdistance.JaroWinkler()

        self._target_index: dict[tuple, list[PersonRecord]] = defaultdict(list)
        self.load_target(Path(target_file))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _blocking_id(self, label: str) -> tuple:
        """Thin wrapper so instance can call the module-level cached fn."""
        return _get_blocking_id(label, self.use_soundex)

    def load_target(self, path: Path) -> None:
        """
        Read the reference/target datasheet and build the blocking index.

        Accepted columns (all optional except *id* and *fullname*):
            id, fullname, gender, wikidata, ulan, birth_year, death_year
        """
        with open(path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh, delimiter=self.sep)
            count = 0
            for raw_row in reader:
                row = _purge_row(raw_row)
                if not row.get('fullname'):
                    continue
                record = PersonRecord(**{
                    k: v for k, v in row.items()
                    if k in PersonRecord.__dataclass_fields__
                })
                
                key = self._blocking_id(record.matchlabel)
                self._target_index[key].append(record)
                count += 1

        print(f'[RuleBasedMatcher] Indexed {count} records '
              f'into {len(self._target_index)} blocking buckets from "{path}".')

    def _evaluate_match(self, a: PersonRecord, b: PersonRecord) -> bool:
        """
        Return True when records *a* and *b* are compatible according to the
        biographical rules defined in the original notebook.

        Elimination rules (any single failure → False):
            • Mismatching gender
            • Mismatching birth year
            • Mismatching death year
            • Impossible lifespan overlap (a died before b was born, or vice-versa)

        Acceptance rules (first hit → True):
            • Exact normalised label match
            • Jaro-Winkler similarity above *jaro_threshold*
        """
        if a.gender and b.gender and a.gender != b.gender:
            return False
        if a.birth_year and b.birth_year and not isclose(a.birth_year, b.birth_year, abs_tol=self.year_tolerance):
            return False
        if a.death_year and b.death_year and not isclose(a.death_year, b.death_year, abs_tol=self.year_tolerance):
            return False
        if a.death_year and b.birth_year and a.death_year <= b.birth_year:
            return False
        if a.birth_year and b.death_year and a.birth_year >= b.death_year:
            return False
        if a.floruit_end and b.birth_year and a.floruit_end <= b.birth_year+20:
            return False
        if a.floruit_start:
            if b.death_year and a.floruit_start >= b.death_year:
                return False
            if b.birth_year and a.floruit_start <= b.birth_year+20:
                return False
        if a.matchlabel == b.matchlabel:
            return True
        if self._dst(a.matchlabel, b.matchlabel) > self.jaro_threshold:
            return True
        return False

    def _evaluate_score(self, a: PersonRecord, b: PersonRecord) -> float:
        """
        Compute a numeric confidence score for a candidate pair.
        Name similarity contributes up to 2.0; each matching year adds 1.0.
        """
        score = self._dst(a.fullname, b.fullname) + self._dst(a.matchlabel, b.matchlabel)
        if a.birth_year and a.birth_year == b.birth_year:
            score += 1.0
        if a.death_year and a.death_year == b.death_year:
            score += 1.0
        return score

    def _parse_source_csv(self, path: Path) -> list[PersonRecord]:
        """Read a CSV/TSV source file and return a list of PersonRecords."""
        suffix = path.suffix.lower()
        sep = ',' if suffix == '.csv' else '\t'

        records = []
        with open(path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh, delimiter=sep)
            for raw_row in reader:
                row = _purge_row(raw_row)
                if row.get('fullname'):
                    record = {
                        k: v for k, v in row.items()
                        if k in PersonRecord.__dataclass_fields__
                    }
                    records.append(record)
        print(path, len(records), sep)
        return records

    def _parse_source_json(self, path: Path) -> list[PersonRecord]:
        """
        Read an Echolot-style JSON file and return a list of PersonRecords.

        Expected JSON structure: a list of objects, each with at least:
            uri, name, entity_type (optional, defaults to 'person'),
            information (dict or str), identifiers.wikidata (optional)
        """
        records = []
        with open(path, newline='', encoding='utf-8') as fh:
            data = json.load(fh)

        for ob in data:
            if ob.get('entity_type', 'person') != 'person':
                continue
            name = ob.get('name')
            if not name:
                continue

            record = dict(id=ob.get('uri', ''), fullname=name)

            info = ob.get('information', {})
            if isinstance(info, dict):
                if gender := info.get('gender'):
                    record['gender'] = gender.lower()
            elif isinstance(info, str):
                if m := re.search(r'Year of birth:\s*(\d+)\b', info):
                    record['birth_year'] = int(m.group(1))
                if m := re.search(r'Year of death:\s*(\d+)\b', info):
                    record['death_year'] = int(m.group(1))

            if wikidata_id := ob.get('identifiers', {}).get('wikidata'):
                record['wikidata'] = str(wikidata_id)

            records.append(record)
        return records

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match_record(self, **kwargs) -> dict[PersonRecord, list[tuple[float, PersonRecord]]]:
        matches: dict[PersonRecord, list[tuple[float, PersonRecord]]] = {}
        record = PersonRecord(**{
                    k: v for k, v in kwargs.items()
                    if k in PersonRecord.__dataclass_fields__
                })
        bucket_key = self._blocking_id(record.matchlabel)
        candidates = set()

        for target in self._target_index.get(bucket_key, []):
            if self._evaluate_match(record, target):
                candidates.add(target)

        if not candidates:
            return record, []

        scored = [
            (self._evaluate_score(record, t), t)
            for t in candidates
        ]
        # Keep only pairs above the score threshold
        scored = sorted(
            ((s, t) for s, t in scored if s > self.score_threshold),
            key=lambda x: x[0],
            reverse=True,
        )

        if not scored:
            return record, []

        # When the two top scores are virtually identical we keep both so
        # the caller can decide how to handle the ambiguity.
        if len(scored) > 1 and isclose(scored[0][0], scored[1][0]):
            return record, scored
            matches[record] = scored          # ambiguous — return all ties
        else:
            return record, [scored[0]]
            matches[record] = [scored[0]]     # clear winner


    def match_file(
        self, source_file: str | Path) -> dict[PersonRecord, list[tuple[float, PersonRecord]]]:
        """
        Match entries in *source_file* against the indexed target datasheet.

        Supported formats: ``.csv``, ``.tsv`` (tabular) and ``.json``
        (Echolot-style).

        Parameters
        ----------
        source_file : str | Path
            Path to the source datasheet whose entries should be resolved.

        Returns
        -------
        dict
            Maps each matched source ``PersonRecord`` to a list of
            ``(score, target_record)`` tuples, sorted by score (best first).
            Records with no match above *score_threshold* are omitted.
        """
        path = Path(source_file)
        if path.suffix.lower() == '.json':
            source_records = self._parse_source_json(path)
        else:
            source_records = self._parse_source_csv(path)

        matches: dict[PersonRecord, list[tuple[float, PersonRecord]]] = {}

        for record in source_records:
            key, arr = self.match_record(**record)
            if arr:
                matches[key] = arr

        return matches
    

    def write_matches(
        self,
        matches: dict[PersonRecord, list[tuple[float, PersonRecord]]],
        output_file: str | Path,
    ) -> None:
        """
        Write *matches* (as returned by :meth:`match_file`) to a TSV file.

        Columns
        -------
        source_id, source_label, source_birth, source_death,
        score,
        target_id, target_label, target_wikidata, target_ulan,
        target_birth, target_death
        """
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            'source_id', 'source_label', 'source_birth', 'source_death',
            'score',
            'target_id', 'target_label', 'target_wikidata', 'target_ulan',
            'target_birth', 'target_death',
        ]

        with open(path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            for source, scored_targets in matches.items():
                for score, target in scored_targets:
                    writer.writerow({
                        'source_id':      source.id,
                        'source_label':   source.fullname,
                        'source_birth':   source.birth_year or '',
                        'source_death':   source.death_year or '',
                        'score':          f'{score:.4f}',
                        'target_id':      target.id,
                        'target_label':   target.fullname,
                        'target_wikidata': target.wikidata or '',
                        'target_ulan':    target.ulan or '',
                        'target_birth':   target.birth_year or '',
                        'target_death':   target.death_year or '',
                    })

        print(f'[RuleBasedMatcher] Wrote {sum(len(v) for v in matches.values())} '
              f'match rows to "{path}".')


# ---------------------------------------------------------------------------
# Quick smoke-test (python RuleBasedMatcher.py)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print(
            'Usage: python RuleBasedMatcher.py <target_file> <source_file> [output_file]\n'
            'Example: python RuleBasedMatcher.py datasheets/wikidata.csv '
            'datasheets/source.tsv datasheets/matches.tsv'
        )
        sys.exit(1)

    target = sys.argv[1]
    source = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else 'matches.tsv'

    matcher = RuleBasedMatcher(target)
    results = matcher.match_file(source)
    matcher.write_matches(results, output)
