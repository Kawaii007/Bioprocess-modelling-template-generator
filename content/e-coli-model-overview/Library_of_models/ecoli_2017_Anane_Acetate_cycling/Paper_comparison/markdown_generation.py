def generate_markdown_table(data_dict, title="Table"):
    """
    Automatically generates a Markdown table for any dictionary.
    Special handling:
        - 'boundaries' -> two columns: 'Lower boundary' and 'Upper boundary'
        - 'plotting' -> generates a separate table with its internal keys as columns
    """
    if not data_dict:
        return f"## {title}\n\n_No data available_"

    # Collect all columns except plotting
    columns = set()
    for props in data_dict.values():
        columns.update(k for k in props.keys() if k != "plotting")

    # Build final columns list
    final_columns = ["name"]
    for col in sorted(columns):
        if col.lower() == "boundaries":
            final_columns.extend(["Lower boundary", "Upper boundary"])
        elif col.lower() != "name":
            final_columns.append(col)

    # Create main table
    md = f"## {title}\n\n"
    md += "| " + " | ".join(final_columns) + " |\n"
    md += "| " + " | ".join(["---"] * len(final_columns)) + " |\n"

    # Fill main table rows
    for name, props in data_dict.items():
        row = [name]
        for col in final_columns[1:]:
            if col == "Lower boundary":
                val = props.get("boundaries", ["", ""])[0] if isinstance(props.get("boundaries"), list) else ""
            elif col == "Upper boundary":
                val = props.get("boundaries", ["", ""])[1] if isinstance(props.get("boundaries"), list) else ""
            else:
                val = props.get(col, "")
            row.append(str(val))
        md += "| " + " | ".join(row) + " |\n"

    # Create separate table for plotting
    plotting_columns = set()
    for props in data_dict.values():
        plotting_data = props.get("plotting", {})
        if isinstance(plotting_data, dict):
            plotting_columns.update(plotting_data.keys())

    if plotting_columns:
        md += f"\n## {title} - plotting specs\n\n"
        plot_cols_sorted = sorted(plotting_columns)
        md += "| Name | " + " | ".join(plot_cols_sorted) + " |\n"
        md += "| " + " | ".join(["---"] * (len(plot_cols_sorted) + 1)) + " |\n"

        for name, props in data_dict.items():
            plotting_data = props.get("plotting", {})
            row = [name] + [str(plotting_data.get(col, "")) for col in plot_cols_sorted]
            md += "| " + " | ".join(row) + " |\n"

    return md