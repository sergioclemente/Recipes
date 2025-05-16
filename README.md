# 🥘 Recipes Collection

This repository contains a structured and searchable collection of personal and family recipes, written in LaTeX and exported to PDF. Recipes are managed using a structured JSON format, rendered into LaTeX via Jinja2 templates, and compiled to a polished PDF document.

## 📁 Project Structure

```
.
├── recipes.json                # Source of truth for all recipes
├── recipes.jinja2              # Jinja2 template for LaTeX generation
├── generate_recipes_tex.py     # Python script to render recipes.tex
├── recipes.tex                 # Auto-generated LaTeX file
├── recipes.pdf                 # Final PDF output
├── Makefile                    # Build automation
└── .github/workflows/build.yml # GitHub Actions workflow for CI
```

## 🧰 Requirements

* Python 3.7+
* LaTeX (with `pdflatex`)
* Python packages:

  * `jinja2`

You can install the Python requirement via:

```bash
pip install jinja2
```

## 🔧 Build Instructions

To generate the PDF from the recipes:

```bash
make clean && make all
```

This will:

1. Render `recipes.tex` using `generate_recipes_tex.py`
2. Compile it to `recipes.pdf` using `pdflatex`

## 🥪 GitHub Actions

On every push, the workflow:

* Runs `make clean && make all`
* Builds `recipes.pdf`
* Uploads it as a downloadable artifact on the Actions tab

You can find it under the **Actions** section of this repo.

## 📖 How to Add a New Recipe

1. Open `recipes.json`
2. Add your recipe under the appropriate section like:

```json
{
  "My Section": {
    "My Recipe Title": {
      "ingredients": [...],
      "steps": [...],
      "notes": [...]
    }
  }
}
```

3. Run `make` to regenerate the PDF

## Prompt for AI

You are an OCR and recipe processing assistant. I will upload a PDF file/Link/PNG that contains a structured recipe (such as HelloFresh cards).

Your job is to extract and return a JSON object in the following format:

json
```
{
  "Root": {
    "<Recipe Title>": {
      "ingredients": [
        "...", 
        "..."
      ],
      "steps": [
        "...", 
        "..."
      ],
      "notes": [
        "..."
      ]
    }
  }
}
```

Instructions:
* Always use "Root" as the top-level section.
* The ingredients should be listed cleanly (no extra units like bullet marks or Unicode characters).
* In the steps, highlight ingredient mentions using \\textbf{...}. For example, “Add rice and butter” becomes “Add \\textbf{rice} and \\textbf{butter}.”
* Convert any special Unicode fractions (like ⅓, ½) into ASCII equivalents (1/3, 1/2, etc).
* Replace & with \\& (escaped for LaTeX).
* Normalize units (e.g., tbsp, tsp, oz, cups), and remove duplicates or ambiguous instructions.
* If notes like "Optional" or food safety info are present, place them under the notes field.
* If the original recipe is in another language, translate it to English during this process.
* If the source was a link please include note in the "notes" with "Original recipe from <link>"

https://www.jocooks.com/wprm_print/beef-empanadas

## 🧹 Cleaning Up

To remove all generated files:

```bash
make clean
```

---

## 📄 License

This project is private and for personal use. Feel free to fork and adapt the structure for your own recipe archive.

---

Maintained by [@sergioclemente](https://github.com/sergioclemente)
