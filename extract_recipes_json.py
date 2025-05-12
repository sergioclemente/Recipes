import re
import json
import sys
from collections import defaultdict

parsed_recipes_data = defaultdict(dict)
parse_errors = 0
parsed_success = 0

def filter_nonempty_strings(string_list):
    return [s for s in string_list if len(s) > 0]

def warn_unparsed_paragraphs(recipe_string, title):
    paragraphs = re.findall(r"\\paragraph\{(.*?)\}", recipe_string)
    for para in paragraphs:
        if para not in ["Ingredients:", "Directions:", "Notes:"] and not re.match(r"(Ingredients|Directions) \(.*\):", para):
            print(f"WARNING: Unrecognized paragraph '{{{para}}}' in recipe '{title}'")

def warn_multiline_items(item_block, title):
    item_lines = [line for line in item_block.strip().splitlines()]
    collecting = False
    for i, line in enumerate(item_lines):
        if line.strip().startswith("\\item"):
            collecting = True
        elif collecting and line.strip():
            print(f"ERROR: Multiline item detected in recipe '{title}' near line: {item_lines[i-1].strip()}\n       -> {line.strip()}")
            collecting = False

def is_advanced_recipe(recipe_string):
    return bool(re.search(r"\\paragraph\{(Ingredients|Directions) \((.*?)\):\}", recipe_string))

def parse_recipe(recipe_string):
    global parse_errors, parsed_success

    title_match = re.search(r"\\subsection\{(.*?)\}", recipe_string)
    notes_itemized_match = re.search(r"\\paragraph\{Notes:\}.*?\\begin\{itemize\}(.*?)\\end\{itemize\}", recipe_string, re.DOTALL)
    notes_inline_match = re.search(r"\\paragraph\{Notes:\}(.*)$", recipe_string, re.DOTALL)

    notes = []
    if notes_itemized_match:
        notes_block = notes_itemized_match.group(1)
        notes = [line.strip()[6:].strip() for line in notes_block.strip().splitlines() if line.strip().startswith("\\item")]
    elif notes_inline_match:
        notes_text = notes_inline_match.group(1).strip()
        if notes_text:
            notes = [note.strip() for note in re.split(r'\n|\r', notes_text) if note.strip()]

    notes = filter_nonempty_strings(notes)

    if title_match:
        title = title_match.group(1).strip()
        warn_unparsed_paragraphs(recipe_string, title)

        if is_advanced_recipe(recipe_string):
            advanced_blocks = re.findall(r"\\paragraph\{(Ingredients|Directions) \((.*?)\):\}.*?\\begin\{itemize\}(.*?)\\end\{itemize\}", recipe_string, re.DOTALL)
            fallback_directions_match = re.findall(r"\\paragraph\{Directions:\}.*?\\begin\{itemize\}(.*?)\\end\{itemize\}", recipe_string, re.DOTALL)

            ingredients_parts = {}
            directions_parts = {}
            group_counts = defaultdict(lambda: {"Ingredients": 0, "Directions": 0})
            empty_blocks = []

            for kind, group, content in advanced_blocks:
                if "\\item" not in content:
                    msg = f"EMPTY BLOCK: {kind} group '{group}' in recipe '{title}' contains no \\item entries"
                    print(f"INFO: {msg}")
                    empty_blocks.append(msg)
                    continue

                warn_multiline_items(content, title)
                items = [line.strip()[6:].strip() for line in content.strip().splitlines() if line.strip().startswith("\\item")]
                group_counts[group][kind] += 1

                if kind == "Ingredients":
                    if group in ingredients_parts:
                        print(f"WARNING: Duplicate Ingredients for group '{group}' in '{title}'")
                    ingredients_parts[group] = filter_nonempty_strings(items)
                elif kind == "Directions":
                    if group in directions_parts:
                        print(f"WARNING: Duplicate Directions for group '{group}' in '{title}'")
                    directions_parts[group] = filter_nonempty_strings(items)

            ingredient_keys = set(ingredients_parts.keys())
            direction_keys = set(directions_parts.keys())

            if len(fallback_directions_match) == 1 and len(direction_keys) == 0:
                fallback_steps = fallback_directions_match[0]
                warn_multiline_items(fallback_steps, title)
                fallback_items = [line.strip()[6:].strip() for line in fallback_steps.strip().splitlines() if line.strip().startswith("\\item")]
                directions_parts["Main"] = fallback_items

            ingredient_keys = set(ingredients_parts.keys())
            direction_keys = set(directions_parts.keys())
            all_keys = ingredient_keys.union(direction_keys)

            if len(direction_keys) > 1 and direction_keys != ingredient_keys:
                for key in sorted(all_keys):
                    if key not in ingredient_keys:
                        print(f"WARNING: '{title}' is missing Ingredients for group '{key}'")
                    if key not in direction_keys:
                        print(f"WARNING: '{title}' is missing Directions for group '{key}'")

            if len(direction_keys) > 1:
                if direction_keys != ingredient_keys:
                    parse_errors += 1
                    print(f"ERROR:: Too many unmatched direction groups in '{title}'")
                    return None, None

            for k, v in directions_parts.items():
                if not v:
                    print(f"WARNING: '{title}' has empty steps for group '{k}'")

            parsed_success += 1
            return title, {
                "ingredients": ingredients_parts,
                "steps": directions_parts,
                "notes": notes
            }

        else:
            simple_ingredients_match = re.search(r"\\paragraph\{Ingredients:\}.*?\\begin\{itemize\}(.*?)\\end\{itemize\}", recipe_string, re.DOTALL)
            simple_directions_match = re.search(r"\\paragraph\{Directions:\}.*?\\begin\{itemize\}(.*?)\\end\{itemize\}", recipe_string, re.DOTALL)

            if simple_ingredients_match and simple_directions_match:
                ingredients_raw = simple_ingredients_match.group(1)
                directions_raw = simple_directions_match.group(1)

                warn_multiline_items(ingredients_raw, title)
                warn_multiline_items(directions_raw, title)

                ingredients = filter_nonempty_strings([line.strip()[6:].strip() for line in ingredients_raw.strip().splitlines() if line.strip().startswith("\\item")])
                directions = filter_nonempty_strings([line.strip()[6:].strip() for line in directions_raw.strip().splitlines() if line.strip().startswith("\\item")])

                if not ingredients or not directions:
                    print(f"WARNING: Empty ingredients or directions in simple recipe '{title}'")

                parsed_success += 1
                return title, {
                    "ingredients": ingredients,
                    "steps": directions,
                    "notes": notes
                }

        parse_errors += 1
        print(f"ERROR:: Can't parse '{title}' - no matching structure")
        return None, None

    else:
        parse_errors += 1
        print("ERROR:: Can't parse recipe (no title)")
        print(recipe_string)
        return None, None

def parse_and_group_by_section(input_path="recipes.tex", json_out_path="section_mapping_out.json"):
    with open(input_path, "r") as infile:
        lines = infile.readlines()

    recipe_blocks = defaultdict(list)
    current_section_title = None
    current_recipe_title = None
    current_recipe_lines = []
    inside_recipe = False

    for i, line in enumerate(lines):
        if i < 39:
            continue

        stripped = line.strip()

        if stripped.startswith("\\section"):
            if inside_recipe and current_section_title and current_recipe_title:
                full_recipe = "".join(current_recipe_lines)
                title, parsed = parse_recipe(full_recipe)
                if title and parsed:
                    parsed_recipes_data[current_section_title][title] = parsed
                inside_recipe = False
                current_recipe_lines = []
            match = re.match(r"\\section\*?\{(.*?)\}", stripped)
            if match:
                current_section_title = match.group(1)
            continue

        if stripped.startswith("\\subsection"):
            if inside_recipe and current_section_title and current_recipe_title:
                full_recipe = "".join(current_recipe_lines)
                title, parsed = parse_recipe(full_recipe)
                if title and parsed:
                    parsed_recipes_data[current_section_title][title] = parsed
            match = re.match(r"\\subsection\{(.*?)\}", stripped)
            if match:
                current_recipe_title = match.group(1)
                current_recipe_lines = [line]
                inside_recipe = True
            continue

        if inside_recipe:
            current_recipe_lines.append(line)

    if inside_recipe and current_section_title and current_recipe_title:
        full_recipe = "".join(current_recipe_lines)
        title, parsed = parse_recipe(full_recipe)
        if title and parsed:
            parsed_recipes_data[current_section_title][title] = parsed

    with open(json_out_path, "w") as jout:
        json.dump(parsed_recipes_data, jout, indent=2)

    print("Finished parsing. Also wrote structured JSON to", json_out_path)
    print(f"Number of recipes successfully parsed: {parsed_success}")
    print(f"Number of recipes that could not be parsed: {parse_errors}")

# Example usage: python3 extract_recipes_json.py recipes.tex recipes.json
if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "recipes_out.tex"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "recipes_out.json"
    parse_and_group_by_section(input_file, output_file)
