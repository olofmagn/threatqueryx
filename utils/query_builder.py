
"""
Query builder
"""

def build_query(template: str, inputs: str, duration: int, platform: str, include_post_pipeline=False) -> str:

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

    base = template.get("base")
    conditions = list(template["required_fields"])

    for key, val in inputs.items():
        if key in template.get("optional_fields", {}):
            pattern = template["optional_fields"][key]["pattern"]
            conditions.append(pattern.format(value=val))

    match platform:
        case "qradar":
            query = f"{base} where {' and '.join(conditions)} LAST {duration}"

        case "defender":
            condition_string = ' and '.join(conditions) if conditions else "true"
            query = f"{base} \n | where {condition_string} \n | where Timestamp > ago({duration})"
            # Allow the possibility to search for both structured/raw events depending on user input
            if include_post_pipeline and "post_pipeline" in template:
                query += f"\n | {template['post_pipeline']}"

        case "elastic":
            query = f"{base}: and {' and '.join(conditions)} and @timestamp >= now-{duration}"

        case _:
            raise ValueError(
                    "Unsupported platform type. Must be elastic, defender or qradar")
    return query
