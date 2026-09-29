from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import requests

SOURCE_URL = (
    "https://raw.githubusercontent.com/AlceuPantoni/loterrrias/"
    "main/data-raw/resultados_megasena.xlsx"
)
OUTPUT_FILE = Path(__file__).with_name("resultados.csv")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        str(c).strip().lower().replace(" ", "_")
        for c in df.columns
    ]
    return df


def to_wide(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)

    # Formato atual do projeto loterrrias: uma linha por dezena sorteada.
    if {"concurso", "numeros_sorteados"}.issubset(df.columns):
        date_col = "data_apuracao" if "data_apuracao" in df.columns else None
        sort_cols = ["concurso"]
        df["concurso"] = pd.to_numeric(df["concurso"], errors="raise").astype(int)
        df["numeros_sorteados"] = pd.to_numeric(
            df["numeros_sorteados"], errors="raise"
        ).astype(int)

        rows = []
        for concurso, group in df.sort_values(sort_cols).groupby("concurso", sort=True):
            numbers = group["numeros_sorteados"].tolist()
            if len(numbers) != 6:
                raise ValueError(
                    f"Concurso {concurso} possui {len(numbers)} dezenas; esperado: 6."
                )

            row = {"concurso": int(concurso)}
            if date_col:
                date_value = group.iloc[0][date_col]
                row["data"] = pd.to_datetime(date_value).date().isoformat()

            for i, number in enumerate(numbers, start=1):
                row[f"n{i}"] = int(number)
            rows.append(row)

        return pd.DataFrame(rows)

    # Caso a fonte passe a disponibilizar formato wide.
    candidate_sets = [
        [f"num_{i}" for i in range(1, 7)],
        [f"n{i}" for i in range(1, 7)],
        [f"dezena_{i}" for i in range(1, 7)],
    ]

    number_cols = next(
        (cols for cols in candidate_sets if all(c in df.columns for c in cols)),
        None,
    )
    if not number_cols or "concurso" not in df.columns:
        raise ValueError(
            "Formato da fonte mudou: não encontrei concurso + seis dezenas."
        )

    date_col = next(
        (c for c in ("data_apuracao", "data", "data_sorteio") if c in df.columns),
        None,
    )

    out = pd.DataFrame()
    out["concurso"] = pd.to_numeric(df["concurso"], errors="raise").astype(int)

    if date_col:
        out["data"] = pd.to_datetime(df[date_col]).dt.date.astype(str)

    for i, col in enumerate(number_cols, start=1):
        out[f"n{i}"] = pd.to_numeric(df[col], errors="raise").astype(int)

    return out


def validate(df: pd.DataFrame) -> pd.DataFrame:
    number_cols = [f"n{i}" for i in range(1, 7)]
    required = {"concurso", *number_cols}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes após conversão: {sorted(missing)}")

    df = (
        df.drop_duplicates(subset=["concurso"], keep="last")
        .sort_values("concurso")
        .reset_index(drop=True)
    )

    values = df[number_cols].to_numpy()
    if ((values < 1) | (values > 60)).any():
        raise ValueError("Há dezenas fora do intervalo 1..60.")

    for concurso, numbers in zip(df["concurso"], values):
        if len(set(map(int, numbers))) != 6:
            raise ValueError(f"Concurso {concurso} possui dezena repetida.")

    if len(df) < 1000:
        raise ValueError(
            f"A fonte retornou somente {len(df)} concursos; atualização cancelada."
        )

    return df


def main() -> None:
    print("Baixando histórico atualizado da Mega-Sena...")
    response = requests.get(
        SOURCE_URL,
        timeout=60,
        headers={"User-Agent": "mega-sena-ml/1.0"},
    )
    response.raise_for_status()

    raw = pd.read_excel(io.BytesIO(response.content), engine="openpyxl")
    result = validate(to_wide(raw))
    result.to_csv(OUTPUT_FILE, index=False)

    last = result.iloc[-1]
    date_text = f" em {last['data']}" if "data" in result.columns else ""
    print(f"OK: {len(result)} concursos salvos em {OUTPUT_FILE.name}.")
    print(f"Último concurso: {int(last['concurso'])}{date_text}.")


if __name__ == "__main__":
    main()
