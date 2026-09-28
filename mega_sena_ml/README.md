# Mega-Sena ML — regressão logística

Experimento em Python para analisar o histórico da Mega-Sena com **regressão logística**.

O modelo cria uma probabilidade relativa para cada dezena de 1 a 60 usando somente dados disponíveis antes do concurso previsto.

## Features

- frequência histórica total
- frequência nos últimos 10, 20, 50 e 100 concursos
- atraso desde a última aparição
- intervalo médio entre aparições
- presença no último concurso
- quantidade de aparições nos últimos 3 e 5 concursos
- paridade e faixa da dezena

O projeto também executa um **backtest temporal**: treina nos concursos mais antigos e testa nos concursos seguintes, evitando usar informação futura no treinamento.

## Importante

Se os sorteios forem independentes e justos, o histórico não muda a probabilidade matemática real de uma combinação específica.

A finalidade deste projeto é testar objetivamente se frequência, atraso e outros padrões históricos apresentam algum poder preditivo. O backtest compara a média de acertos do modelo com a referência aleatória esperada de **0,6 número por jogo de 6 dezenas**.

Não trate o resultado como garantia de ganho.

## Formato do CSV

O arquivo precisa ter:

```csv
concurso,data,n1,n2,n3,n4,n5,n6
1,11/03/1996,4,5,30,33,41,52
2,18/03/1996,9,37,39,41,43,49
```

A coluna `data` é opcional. Os nomes `bola1..bola6` e `dezena1..dezena6` também são reconhecidos.

## Instalação

```bash
cd mega_sena_ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar com CSV local

```bash
python main.py --csv resultados.csv
```

Gerar 50 jogos:

```bash
python main.py --csv resultados.csv --games 50
```

## Executar com CSV por URL

```bash
python main.py --url "https://exemplo.com/resultados.csv"
```

Existe um CSV público para testes neste projeto de terceiros:

```bash
python main.py \
  --url "https://raw.githubusercontent.com/rianbrrs/mega-gen/main/historico_megasena.csv"
```

Esse arquivo é apenas uma fonte de demonstração e pode estar desatualizado. Para prever o próximo concurso, use um histórico atualizado.

## Saída

O programa mostra no terminal:

- métricas do backtest
- média de acertos do top-6
- comparação com a referência aleatória
- quantidade de quadras, quinas e senas no período de teste
- Brier Score
- Log Loss
- ROC AUC
- ranking das 15 dezenas com maior score
- jogos gerados

Também cria:

```
output/ranking.csv
output/jogos.csv
```

## Geração dos jogos

O modelo não pega simplesmente as mesmas 6 dezenas em todos os jogos.

Ele transforma as probabilidades previstas em pesos e sorteia combinações sem repetição, permitindo alguma diversidade.

Parâmetros:

```bash
python main.py \
  --csv resultados.csv \
  --games 30 \
  --seed 42 \
  --temperature 1.0 \
  --uniform-blend 0.20
```

- `temperature < 1`: concentra mais nos números mais bem classificados.
- `temperature > 1`: espalha mais os jogos.
- `uniform-blend`: mistura o score do modelo com distribuição uniforme para reduzir excesso de confiança.

## Próximos experimentos

Uma evolução útil é comparar no mesmo backtest:

1. regressão logística
2. números totalmente aleatórios
3. Gradient Boosting
4. Random Forest
5. XGBoost/LightGBM
6. estratégias de frequência/atraso sem ML
7. walk-forward validation concurso a concurso

Assim dá para verificar se qualquer melhoria persiste fora da amostra em vez de confiar apenas em coincidências históricas.
