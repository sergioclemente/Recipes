import json
import sys
from jinja2 import Environment, FileSystemLoader

# Example usage:
# python3 generate_recipes_tex.py recipes.json recipes.jinja2 recipes.tex
if len(sys.argv) != 4:
    print("Usage: python generate_recipes.py <input_json> <template_file> <output_tex>")
    sys.exit(1)

input_json_path = sys.argv[1]
template_file = sys.argv[2]
output_tex_path = sys.argv[3]

# Load the JSON data
with open(input_json_path) as f:
    recipes_data = json.load(f)

# Set up Jinja2 environment
env = Environment(
    block_start_string='((*',
    block_end_string='*))',
    variable_start_string='(((',
    variable_end_string=')))',
    loader=FileSystemLoader("."),
    autoescape=False
)

# Load the LaTeX template
template = env.get_template(template_file)
rendered_tex = template.render(data=recipes_data)

# Write to output .tex file
with open(output_tex_path, "w") as f:
    f.write(rendered_tex)

print(f"{output_tex_path} generated.")
