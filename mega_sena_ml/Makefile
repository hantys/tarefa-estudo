.PHONY: atualizar gerar gerar-fixo tudo tudo-fixo

atualizar:
	python update_results.py

gerar: atualizar
	python main.py --csv resultados.csv --games 20

gerar-fixo: atualizar
	python main.py --csv resultados.csv --games 20 --seed 42

tudo:
	python update_results.py
	python main.py --csv resultados.csv --games 20

tudo-fixo:
	python update_results.py
	python main.py --csv resultados.csv --games 20 --seed 42
