"""
Query builder
"""

from typing import Dict, Any


def build_query(template: Dict[str, Any], inputs: Dict[str, str], duration: str, platform: str,
                base_queries: Dict[str, str], include_post_pipeline: bool = False) -> str:
    """
    Builds a query with a template, inputs, duration and the provided platform

    Args:
        template (Dict[str, Any]): A template dictionary containing query structure
        inputs (Dict[str, str]): User-provided field values for optional parameters
        duration (str): A duration string for the time range (e.g., "1h", "30 MINUTES")
        platform (str): A platform for issuing the queries ("qradar", "defender", "elastic")
        base_queries (Dict[str, str]): A dictionary of base queries keyed by platform
        include_post_pipeline (bool): Whether to include post-processing pipeline (Defender only)

    Returns:
        str: A formatted query for the specified platform
    """

    if "base" not in template:
        raise KeyError("Template missing required 'base' field")

    base = template["base"]
    if base_queries and base.startswith("{") and base.endswith("}"):
        key_name = base[1:-1]
        if key_name in base_queries:
            base = base_queries[key_name]
        else:
            raise ValueError(f"Base query '{key_name}' not found in base_queries")

    conditions = list(template.get("required_fields", []))

    # Add optional field conditions
    for key, val in inputs.items():
        optional_fields = template.get("optional_fields", {})
        if key in optional_fields:
            field_config = optional_fields[key]
            if isinstance(field_config, dict) and "pattern" in field_config:
                pattern = field_config["pattern"]
                conditions.append(pattern.format(value=val))
            else:
                # Handle simple string patterns
                conditions.append(f"{key} = '{val}'")

    match platform:
        case "qradar":
            order_by = "devicetime DESC"
            condition_string = ' and '.join(conditions) if conditions else "true"
            query = f"{base} where {condition_string} ORDER BY {order_by} LAST {duration}"
        case "defender":
            condition_string = ' and '.join(conditions) if conditions else "true"
            query = f"{base} \n | where {condition_string} \n | where Timestamp > ago({duration})"
            # Add post-processing pipeline if requested
            if include_post_pipeline and "post_pipeline" in template:
                query += f"\n | {template['post_pipeline']}"
        case "elastic":
            condition_string = ' and '.join(conditions) if conditions else "*"
            query = f"{base} and {condition_string} and @timestamp >= now-{duration}"
        case _:
            raise ValueError(
                f"Unsupported platform '{platform}'. Must be 'elastic', 'defender', or 'qradar'"
            )
    return query
