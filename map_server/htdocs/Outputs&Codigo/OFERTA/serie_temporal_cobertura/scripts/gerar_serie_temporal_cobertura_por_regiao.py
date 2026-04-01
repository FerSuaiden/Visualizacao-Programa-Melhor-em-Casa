#!/usr/bin/env python3
"""
Gera serie temporal mensal da cobertura municipal por regiao (%)
do Programa Melhor em Casa.

Fonte principal: CNES_DATA/tbEquipe202508.csv
Regra de equipes AD: TP_EQUIPE em {22, 46, 23, 77}
"""

from __future__ import annotations

import argparse
import math
import os
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


IBGE_UF_MAP = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS",
    "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

UF_REGIAO = {
    "RO": "Norte", "AC": "Norte", "AM": "Norte", "RR": "Norte", "PA": "Norte", "AP": "Norte", "TO": "Norte",
    "MA": "Nordeste", "PI": "Nordeste", "CE": "Nordeste", "RN": "Nordeste", "PB": "Nordeste", "PE": "Nordeste", "AL": "Nordeste", "SE": "Nordeste", "BA": "Nordeste",
    "MG": "Sudeste", "ES": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "SC": "Sul", "RS": "Sul",
    "MS": "Centro-Oeste", "MT": "Centro-Oeste", "GO": "Centro-Oeste", "DF": "Centro-Oeste",
}

REGIOES_ORDENADAS = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
CORES_REGIAO = {
    "Norte": "#1f77b4",
    "Nordeste": "#ff7f0e",
    "Centro-Oeste": "#2ca02c",
    "Sudeste": "#d62728",
    "Sul": "#9467bd",
}
TIPOS_EQUIPE_AD = {22, 46, 23, 77}

MUNICIPIOS_POR_UF = {
    "RO": 52, "AC": 22, "AM": 62, "RR": 15, "PA": 144, "AP": 16, "TO": 139,
    "MA": 217, "PI": 224, "CE": 184, "RN": 167, "PB": 223, "PE": 185, "AL": 102, "SE": 75, "BA": 417,
    "MG": 853, "ES": 78, "RJ": 92, "SP": 645,
    "PR": 399, "SC": 295, "RS": 497,
    "MS": 79, "MT": 141, "GO": 246, "DF": 1,
}


def municipios_totais_por_regiao() -> Dict[str, int]:
    totais = {reg: 0 for reg in REGIOES_ORDENADAS}
    for uf, n_mun in MUNICIPIOS_POR_UF.items():
        reg = UF_REGIAO.get(uf)
        if reg:
            totais[reg] += n_mun
    return totais


def extrair_uf(codigo_municipio: str) -> str:
    prefixo = str(codigo_municipio).strip()[:2]
    return IBGE_UF_MAP.get(prefixo, "DESCONHECIDO")


def carregar_equipes_ad(cnes_dir: str) -> pd.DataFrame:
    caminho = os.path.join(cnes_dir, "tbEquipe202508.csv")
    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin-1",
        usecols=["TP_EQUIPE", "CO_MUNICIPIO", "DT_ATIVACAO", "DT_DESATIVACAO"],
        low_memory=False,
    )

    df = df[df["TP_EQUIPE"].isin(TIPOS_EQUIPE_AD)].copy()
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].astype(str).str.strip().str[:6]
    df["UF"] = df["CO_MUNICIPIO"].map(lambda x: extrair_uf(x))
    df["REGIAO"] = df["UF"].map(UF_REGIAO)

    df["DT_ATIVACAO"] = pd.to_datetime(df["DT_ATIVACAO"], format="%d/%m/%Y", errors="coerce")
    df["DT_DESATIVACAO"] = pd.to_datetime(df["DT_DESATIVACAO"], format="%d/%m/%Y", errors="coerce")

    # Remove registros sem data de ativacao ou com regiao desconhecida.
    df = df[df["DT_ATIVACAO"].notna() & df["REGIAO"].notna()].copy()
    return df


def construir_serie_mensal(df: pd.DataFrame, inicio: str, fim: str | None) -> pd.DataFrame:
    inicio_ts = pd.Period(inicio, freq="M").to_timestamp("M")
    if fim:
        fim_ts = pd.Period(fim, freq="M").to_timestamp("M")
    else:
        fim_ts = df["DT_ATIVACAO"].max().to_period("M").to_timestamp("M")

    meses = pd.date_range(start=inicio_ts, end=fim_ts, freq="ME")
    totais_regiao = municipios_totais_por_regiao()
    total_brasil = int(sum(totais_regiao.values()))
    linhas: List[Dict[str, object]] = []

    for mes in meses:
        ativas = df[(df["DT_ATIVACAO"] <= mes) & (df["DT_DESATIVACAO"].isna() | (df["DT_DESATIVACAO"] > mes))]
        mun_reg = ativas[["CO_MUNICIPIO", "REGIAO"]].drop_duplicates()
        por_regiao = mun_reg.groupby("REGIAO")["CO_MUNICIPIO"].nunique().to_dict()

        linha = {"MES": mes.strftime("%Y-%m"), "DATA_REFERENCIA": mes.date().isoformat()}
        total_ativos_brasil = 0
        for reg in REGIOES_ORDENADAS:
            val = int(por_regiao.get(reg, 0))
            linha[f"MUNICIPIOS_{reg.upper()}"] = val
            linha[f"COBERTURA_PCT_{reg.upper()}"] = round((val / totais_regiao[reg]) * 100, 4)
            total_ativos_brasil += val

        linha["MUNICIPIOS_BRASIL"] = total_ativos_brasil
        linha["COBERTURA_PCT_BRASIL"] = round((total_ativos_brasil / total_brasil) * 100, 4)
        linhas.append(linha)

    return pd.DataFrame(linhas)


def salvar_grafico_cobertura(df_serie: pd.DataFrame, caminho_saida: str) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(16, 9))

    x = pd.to_datetime(df_serie["DATA_REFERENCIA"])
    for regiao in REGIOES_ORDENADAS:
        col = f"COBERTURA_PCT_{regiao.upper()}"
        ax.plot(
            x,
            df_serie[col],
            label=regiao,
            linewidth=2.4,
            color=CORES_REGIAO[regiao],
        )

    ax.set_xlabel("Ano", fontsize=24)
    ax.set_ylabel("% dos municípios da região com AD", fontsize=24)
    ax.tick_params(axis="both", labelsize=20)

    # Escala dinamica: teto no multiplo de 5 imediatamente acima do maximo observado.
    cols_cob = [f"COBERTURA_PCT_{reg.upper()}" for reg in REGIOES_ORDENADAS]
    max_cob = float(df_serie[cols_cob].max().max())
    y_max = max(5, int(math.ceil(max_cob / 5.0) * 5))
    ax.set_ylim(0, y_max)

    ax.legend(title="Regiao", ncol=3, fontsize=18, title_fontsize=19)
    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(caminho_saida, dpi=220)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera serie temporal da cobertura municipal por regiao (%)."
    )
    parser.add_argument(
        "--base-dir",
        default="/home/fersuaiden/Área de trabalho/Faculdade/IC",
        help="Diretorio base do projeto.",
    )
    parser.add_argument(
        "--inicio",
        default="2011-01",
        help="Mes inicial no formato YYYY-MM (padrao: 2011-01).",
    )
    parser.add_argument(
        "--fim",
        default=None,
        help="Mes final no formato YYYY-MM. Se omitido, usa o ultimo mes com ativacao.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    cnes_dir = os.path.join(args.base_dir, "CNES_DATA")
    serie_dir = os.path.join(args.base_dir, "Outputs&Codigo", "OFERTA", "serie_temporal_cobertura")

    df_equipes = carregar_equipes_ad(cnes_dir)
    df_serie = construir_serie_mensal(df_equipes, inicio=args.inicio, fim=args.fim)

    fig_cobertura_saida = os.path.join(serie_dir, "evolucao_cobertura_percentual_por_regiao.png")

    salvar_grafico_cobertura(df_serie, fig_cobertura_saida)

    print(f"Registros de equipes AD usados: {len(df_equipes):,}")
    print(f"Periodo da serie: {df_serie['MES'].iloc[0]} ate {df_serie['MES'].iloc[-1]}")
    print(f"Grafico cobertura: {fig_cobertura_saida}")


if __name__ == "__main__":
    main()
