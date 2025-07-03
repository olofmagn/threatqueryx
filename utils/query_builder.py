
"""
Query builder
"""

def build_query(template: str, inputs: str, duration: int, platform: str) -> str:

    """
    Builds a query with a tempate, inputs, durations and the provided platform.

    Args:
    - template (str): A template string of a given threat search query.
    - inputs (str): A user-specified time-interval of the threat search.
    - duration (str): A duration entity to search for historical data.
    - platform (str): A platform for issueing the queries.

    Returns:
    - str: A query given all these above parameters.
    """

    # Safe access as it might be None
    base = template.get("base")
    conditions = list(template["required_fields"])

    for key, val in inputs.items():
        if key in template.get("optional_fields", {}):
            pattern = template["optional_fields"][key]["pattern"]
            conditions.append(pattern.format(value=val))

    match platform:
        case "qradar":
            query = f"{base} WHERE {' AND '.join(conditions)} LAST {duration}"

        case "defender":
            query = f"{base} \n | {' and '.join(conditions)} \n | where Timestamp > ago({duration})"

        case "elastic":
            query = f"{base}: and {' and '.join(conditions)} and @timestamp >= now-{duration}"

        case _:
            raise ValueError(
                    "Unsupported platform type. Must be elastic, defender or qradar")
    return query
