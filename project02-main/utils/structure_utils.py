import json
from typing import List, Dict


def normalize_structure(structure: Dict) -> List[Dict]:
    """Flatten structure_json into a list of row dicts.

    Expected input shape:
    {
      "LABORATORY": [{"name": str, "weight": num, "assessments": [{"name": str, "max_score": num}]}],
      "LECTURE":    [{...}]
    }
    Returns list of dicts: {category, name, weight, assessment, max_score}
    """
    rows: List[Dict] = []
    if not isinstance(structure, dict):
        return rows

    for category_key in ["LABORATORY", "LECTURE"]:
        categories = structure.get(category_key, []) or []
        if not isinstance(categories, list):
            continue
        for cat in categories:
            if not isinstance(cat, dict):
                continue
            name = cat.get("name") or ""
            weight = cat.get("weight") or 0
            assessments = cat.get("assessments", []) or []
            if not isinstance(assessments, list):
                continue
            for a in assessments:
                if not isinstance(a, dict):
                    continue
                rows.append(
                    {
                        "category": category_key,
                        "name": name,
                        "weight": weight,
                        "assessment": a.get("name") or "",
                        "max_score": a.get("max_score") or 0,
                    }
                )
    return rows


def group_structure(normalized_rows: List[Dict]) -> Dict:
    """Split normalized rows into strings vs numbers collections.

    Input row shape: {category, name, weight, assessment, max_score}
    Output: { strings: [{category, name, assessment}, ...], numbers: [{weight, max_score}, ...] }
    """
    strings = []
    numbers = []
    if not isinstance(normalized_rows, list):
        return {"strings": strings, "numbers": numbers}

    for row in normalized_rows:
        if not isinstance(row, dict):
            continue
        strings.append(
            {
                "category": row.get("category"),
                "name": row.get("name"),
                "assessment": row.get("assessment"),
            }
        )
        numbers.append(
            {
                "weight": row.get("weight", 0),
                "max_score": row.get("max_score", 0),
            }
        )

    return {"strings": strings, "numbers": numbers}
