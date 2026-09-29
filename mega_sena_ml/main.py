from __future__ import annotations

import argparse
import io
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

NUMBER_COLS = [f"n{i}" for i in range(1, 7)]
FEATURE_COLS = [
    "freq_total", "freq_10", "freq_20", "freq_50", "freq_100",
    "delay", "mean_gap", "hit_last_1", "hit_last_3", "hit_last_5",
    "number_norm", "is_even", "decade",
]

def load_history(csv_path: str | None, csv_url: str | None) -> pd.DataFrame:
    if not csv_path and not csv_url:
        raise SystemExit("Informe --csv ARQUIVO.csv ou --url URL_DO_CSV.")
    if csv_path:
        raw = pd.read_csv(csv_path)
    else:
        response = requests.get(csv_url, timeout=30)
        response.raise_for_status()
        raw = pd.read_csv(io.StringIO(response.text))

    columns = {str(c).strip().lower(): c for c in raw.columns}
    rename = {}
    aliases = {
        "concurso": ["concurso", "contest", "numero_concurso"],
        "data": ["data", "date", "data_sorteio"],
        "n1": ["n1", "bola1", "dezena1", "dezena_1"],
        "n2": ["n2", "bola2", "dezena2", "dezena_2"],
        "n3": ["n3", "bola3", "dezena3", "dezena_3"],
        "n4": ["n4", "bola4", "dezena4", "dezena_4"],
        "n5": ["n5", "bola5", "dezena5", "dezena_5"],
        "n6": ["n6", "bola6", "dezena6", "dezena_6"],
    }
    for target, names in aliases.items():
        for name in names:
            if name in columns:
                rename[columns[name]] = target
                break

    df = raw.rename(columns=rename).copy()
    required = {"concurso", *NUMBER_COLS}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV sem colunas obrigatórias: {sorted(missing)}")

    keep = ["concurso", *(["data"] if "data" in df.columns else []), *NUMBER_COLS]
    df = df[keep].copy()
    df["concurso"] = pd.to_numeric(df["concurso"], errors="raise").astype(int)
    for c in NUMBER_COLS:
        df[c] = pd.to_numeric(df[c], errors="raise").astype(int)

    values = df[NUMBER_COLS].to_numpy()
    if ((values < 1) | (values > 60)).any():
        raise ValueError("As dezenas devem estar entre 1 e 60.")
    if any(len(set(row)) != 6 for row in values):
        raise ValueError("Há concurso com dezenas repetidas no CSV.")

    df = (
        df.drop_duplicates(subset=["concurso"], keep="last")
        .sort_values("concurso")
        .reset_index(drop=True)
    )
    if len(df) < 120:
        raise ValueError("Histórico muito curto. Use pelo menos 120 concursos.")
    return df

def draw_sets(df: pd.DataFrame) -> list[set[int]]:
    return [set(map(int, row)) for row in df[NUMBER_COLS].to_numpy()]

def number_features(history: list[set[int]], number: int) -> dict[str, float]:
    n_draws = len(history)
    hits = np.array([number in draw for draw in history], dtype=np.int8)
    hit_idx = np.flatnonzero(hits)

    if len(hit_idx):
        delay = n_draws - 1 - int(hit_idx[-1])
        mean_gap = float(np.mean(np.diff(hit_idx))) if len(hit_idx) >= 2 else float(n_draws)
    else:
        delay = n_draws
        mean_gap = float(n_draws)

    def recent(window: int) -> float:
        size = min(window, n_draws)
        return float(hits[-size:].mean()) if size else 0.0

    return {
        "freq_total": float(hits.mean()),
        "freq_10": recent(10),
        "freq_20": recent(20),
        "freq_50": recent(50),
        "freq_100": recent(100),
        "delay": float(delay),
        "mean_gap": mean_gap,
        "hit_last_1": float(hits[-1]) if n_draws >= 1 else 0.0,
        "hit_last_3": float(hits[-3:].sum()) if n_draws >= 1 else 0.0,
        "hit_last_5": float(hits[-5:].sum()) if n_draws >= 1 else 0.0,
        "number_norm": number / 60.0,
        "is_even": float(number % 2 == 0),
        "decade": float((number - 1) // 10),
    }

def build_training_frame(df: pd.DataFrame, min_history: int = 100) -> pd.DataFrame:
    draws = draw_sets(df)
    rows = []
    for i in range(min_history, len(draws)):
        history = draws[:i]
        target = draws[i]
        target_contest = int(df.iloc[i]["concurso"])
        for number in range(1, 61):
            row = number_features(history, number)
            row["number"] = number
            row["target"] = int(number in target)
            row["target_concurso"] = target_contest
            rows.append(row)
    return pd.DataFrame(rows)

def current_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    history = draw_sets(df)
    rows = []
    for number in range(1, 61):
        row = number_features(history, number)
        row["number"] = number
        rows.append(row)
    return pd.DataFrame(rows)

def make_model() -> Pipeline:
    return Pipeline([
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=2000, solver="lbfgs", C=1.0, random_state=42)),
    ])

def temporal_split(frame: pd.DataFrame, train_ratio: float = 0.80):
    contests = np.array(sorted(frame["target_concurso"].unique()))
    cut = max(1, min(len(contests) - 1, int(len(contests) * train_ratio)))
    train_contests = set(contests[:cut])
    test_contests = set(contests[cut:])
    train = frame[frame["target_concurso"].isin(train_contests)].copy()
    test = frame[frame["target_concurso"].isin(test_contests)].copy()
    return train, test

def backtest(frame: pd.DataFrame) -> dict[str, float | int]:
    train, test = temporal_split(frame)
    model = make_model()
    model.fit(train[FEATURE_COLS], train["target"])
    probs = model.predict_proba(test[FEATURE_COLS])[:, 1]
    test = test.copy()
    test["prob"] = probs

    hits_per_game = []
    for _, group in test.groupby("target_concurso", sort=True):
        top6 = set(group.nlargest(6, "prob")["number"].astype(int))
        actual = set(group.loc[group["target"] == 1, "number"].astype(int))
        hits_per_game.append(len(top6 & actual))

    hit_arr = np.array(hits_per_game, dtype=int)
    metrics = {
        "train_contests": int(train["target_concurso"].nunique()),
        "test_contests": int(test["target_concurso"].nunique()),
        "avg_hits_top6": float(hit_arr.mean()),
        "random_expected_hits": 0.6,
        "quadras_or_better": int((hit_arr >= 4).sum()),
        "quinas_or_better": int((hit_arr >= 5).sum()),
        "senas": int((hit_arr >= 6).sum()),
        "brier": float(brier_score_loss(test["target"], probs)),
        "log_loss": float(log_loss(test["target"], probs, labels=[0, 1])),
    }
    try:
        metrics["roc_auc"] = float(roc_auc_score(test["target"], probs))
    except ValueError:
        metrics["roc_auc"] = float("nan")
    return metrics

def fit_and_rank(frame: pd.DataFrame, df: pd.DataFrame):
    model = make_model()
    model.fit(frame[FEATURE_COLS], frame["target"])
    current = current_feature_frame(df)
    current["prob_model"] = model.predict_proba(current[FEATURE_COLS])[:, 1]
    current["prob_uniform"] = 0.10
    current = current.sort_values("prob_model", ascending=False).reset_index(drop=True)
    current["rank"] = np.arange(1, len(current) + 1)
    return model, current

def generate_games(ranking: pd.DataFrame, n_games: int, seed: int | None,
                   temperature: float = 1.0, uniform_blend: float = 0.20):
    rng = np.random.default_rng(seed)
    numbers = ranking["number"].to_numpy(dtype=int)
    model_probs = ranking["prob_model"].to_numpy(dtype=float)

    base = np.clip(model_probs, 1e-9, None)
    base = base ** (1.0 / max(temperature, 1e-6))
    base = base / base.sum()
    uniform = np.full_like(base, 1.0 / len(base))
    weights = (1.0 - uniform_blend) * base + uniform_blend * uniform
    weights = weights / weights.sum()

    games = set()
    max_attempts = max(500, n_games * 100)
    attempts = 0
    while len(games) < n_games and attempts < max_attempts:
        selected = rng.choice(numbers, size=6, replace=False, p=weights)
        games.add(tuple(sorted(map(int, selected))))
        attempts += 1
    return [list(game) for game in sorted(games)]

def save_outputs(ranking: pd.DataFrame, games, output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ranking[["rank", "number", "prob_model", "freq_total", "freq_20", "freq_50", "delay", "mean_gap"]].to_csv(
        out / "ranking.csv", index=False
    )
    pd.DataFrame([
        {"jogo": i + 1, **{f"n{j + 1}": n for j, n in enumerate(game)}}
        for i, game in enumerate(games)
    ]).to_csv(out / "jogos.csv", index=False)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mega-Sena com regressão logística e backtest temporal.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--csv")
    source.add_argument("--url")
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--seed", type=int, default=None, help="Seed opcional. Sem informar, os jogos variam a cada execução.")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--uniform-blend", type=float, default=0.20)
    parser.add_argument("--output", default="output")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    if args.games < 1:
        raise SystemExit("--games deve ser >= 1.")
    if not 0.0 <= args.uniform_blend <= 1.0:
        raise SystemExit("--uniform-blend deve ficar entre 0 e 1.")
    if args.temperature <= 0:
        raise SystemExit("--temperature deve ser > 0.")

    df = load_history(args.csv, args.url)
    frame = build_training_frame(df)
    metrics = backtest(frame)
    _, ranking = fit_and_rank(frame, df)
    games = generate_games(
        ranking, args.games, args.seed, args.temperature, args.uniform_blend
    )
    save_outputs(ranking, games, args.output)

    print(f"Concursos carregados: {len(df)}")
    print(f"Último concurso no CSV: {int(df.iloc[-1]['concurso'])}")
    print("\nBACKTEST TEMPORAL")
    print(f"  treino: {metrics['train_contests']} concursos")
    print(f"  teste:  {metrics['test_contests']} concursos")
    print(f"  média de acertos do top-6: {metrics['avg_hits_top6']:.3f}")
    print(f"  referência aleatória esperada: {metrics['random_expected_hits']:.3f}")
    print(f"  quadras ou melhor: {metrics['quadras_or_better']}")
    print(f"  quinas ou melhor: {metrics['quinas_or_better']}")
    print(f"  senas: {metrics['senas']}")
    print(f"  Brier: {metrics['brier']:.5f}")
    print(f"  Log loss: {metrics['log_loss']:.5f}")
    print(f"  ROC AUC: {metrics['roc_auc']:.5f}")

    print("\nTOP 15 DO MODELO")
    for row in ranking.head(15).itertuples():
        print(f"  {int(row.rank):02d}. {int(row.number):02d} p={row.prob_model:.4f} freq20={row.freq_20:.3f} atraso={int(row.delay)}")

    print("\nJOGOS GERADOS")
    for i, game in enumerate(games, start=1):
        print(f"  {i:02d}: " + " ".join(f"{n:02d}" for n in game))

    print("\nAviso: em sorteios independentes e justos, o histórico não altera a probabilidade real de cada combinação.")

if __name__ == "__main__":
    main()