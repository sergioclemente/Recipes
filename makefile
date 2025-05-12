all: recipes.pdf

recipes.pdf: recipes.tex
	pdflatex -synctex=1 -interaction=nonstopmode recipes.tex

recipes.tex: recipes.json recipes.jinja2 generate_recipes_tex.py
	python3 generate_recipes_tex.py recipes.json recipes.jinja2 recipes.tex

clean:
	rm -f recipes.aux recipes.log recipes.out recipes.synctex.gz recipes.pdf recipes.tex
