.PHONY: atualizar gerar

atualizar:
	python update_results.py

gerar: atualizar
	python main.py --csv resultados.csv --games 20
