import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path

# Caminhos dos arquivos (Fonte: CNES/DataSUS - competência 2025/08)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
arquivo_equipes = PROJECT_ROOT / 'CNES_DATA' / 'tbEquipe202508.csv'

# --- Dicionários de Mapeamento ---
MAP_EQUIPES = {
    '22': 'EMAD I',
    '46': 'EMAD II',
    '23': 'EMAP',
    '77': 'EMAP-R'
}
CODIGOS_RELEVANTES = ['22', '46', '23', '77']

try:
    # Carregamento das bases de dados
    df_equipes = pd.read_csv(
        arquivo_equipes, 
        sep=';', 
        encoding='latin-1', 
        dtype=str, 
        usecols=['CO_UNIDADE', 'TP_EQUIPE', 'DT_DESATIVACAO']
    )

    # Filtragem e mapeamento
    df_equipes['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce'
    )
    df_equipes_ativas = df_equipes[df_equipes['DT_DESATIVACAO'].isna()].copy()

    df_equipes_filtradas = df_equipes_ativas[df_equipes_ativas['TP_EQUIPE'].isin(CODIGOS_RELEVANTES)].copy()
    df_equipes_filtradas['Tipo_Equipe'] = df_equipes_filtradas['TP_EQUIPE'].map(MAP_EQUIPES)

    # Grafico de pizza (composicao nacional) no estilo donut com percentuais fora.
    df_composicao_nacional = df_equipes_filtradas['Tipo_Equipe'].value_counts()
    fig_pie, ax_pie = plt.subplots(figsize=(12.8, 8.8))
    
    # Define cores para consistência
    cores = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']
    
    total_equipes = int(df_composicao_nacional.sum())

    # Mostra percentual e quantidade diretamente no grafico para aliviar a legenda.
    def pct_e_qtd(pct):
        qtd = int(round(pct * total_equipes / 100.0))
        return f"{pct:.1f}%\n({qtd:,})".replace(',', '.')

    wedges, texts, autotexts = ax_pie.pie(
        df_composicao_nacional, 
        startangle=90,
        autopct=pct_e_qtd,
        radius=1.08,
        pctdistance=1.16,
        colors=cores[:len(df_composicao_nacional)],
        wedgeprops={'width': 0.45, 'edgecolor': 'white', 'linewidth': 2},
        textprops={'fontsize': 11, 'fontweight': 'bold'}
    )
    
    ax_pie.axis('equal')  # Garante que a pizza seja um círculo
    # Sem titulo superior para priorizar area util do grafico.
    
    # Legenda enxuta: apenas sigla e significado.
    siglas_equipe = {
        'EMAD I': 'Equipe Multiprofissional de Atencao Domiciliar - Tipo I',
        'EMAD II': 'Equipe Multiprofissional de Atencao Domiciliar - Tipo II',
        'EMAP': 'Equipe Multiprofissional de Apoio',
        'EMAP-R': 'Equipe Multiprofissional de Apoio para Reabilitacao',
    }
    detailed_labels = [
        f"{label}: {siglas_equipe.get(label, 'Sigla nao mapeada')}"
        for label in df_composicao_nacional.index
    ]
    
    ax_pie.legend(
        wedges, 
        detailed_labels, 
        title="Tipo de Equipe (Programa Melhor em Casa)",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=12,
        title_fontsize=14,
        frameon=False
    )

    ax_pie.text(0, 0, f"Total\n{total_equipes:,}".replace(',', '.'), ha='center', va='center', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    nome_grafico = SCRIPT_DIR / 'composicao_nacional_pizza.png'
    plt.savefig(nome_grafico, bbox_inches='tight')
    print(f"Gráfico salvo: {nome_grafico}")


except FileNotFoundError as e:
    print(f"\nERRO: O arquivo '{e.filename}' não foi encontrado.")
    print("Por favor, verifique se os caminhos e nomes dos arquivos estão corretos.")
    sys.exit(1)
except KeyError as e:
    print(f"\nERRO: A coluna {e} não foi encontrada.")
    print("Verifique se os nomes das colunas ('CO_UNIDADE', 'CO_UF', 'TP_EQUIPE') estão corretos nos seus arquivos CSV.")
    sys.exit(1)
except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")
    sys.exit(1)