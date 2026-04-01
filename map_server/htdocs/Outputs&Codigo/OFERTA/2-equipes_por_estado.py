import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path

# Caminhos dos arquivos (Fonte: CNES/DataSUS - competência 2025/08)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
arquivo_estabelecimentos = PROJECT_ROOT / 'CNES_DATA' / 'tbEstabelecimento202508.csv'
arquivo_equipes = PROJECT_ROOT / 'CNES_DATA' / 'tbEquipe202508.csv'

# --- Dicionários de Mapeamento ---
MAP_EQUIPES = {
    '22': 'EMAD I',
    '46': 'EMAD II',
    '23': 'EMAP',
    '77': 'EMAP-R'
}
CODIGOS_RELEVANTES = ['22', '46', '23', '77']
IBGE_UF_MAP = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
    '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE', '29': 'BA',
    '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
    '41': 'PR', '42': 'SC', '43': 'RS',
    '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
}

try:
    # Carregamento das bases de dados
    df_estabelecimentos = pd.read_csv(
        arquivo_estabelecimentos, 
        sep=';', 
        encoding='latin-1', 
        dtype=str, 
        usecols=['CO_UNIDADE', 'CO_ESTADO_GESTOR']
    )
    df_estabelecimentos = df_estabelecimentos.rename(columns={'CO_ESTADO_GESTOR': 'CO_UF'})

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
    
    df_merged = pd.merge(
        df_equipes_filtradas,
        df_estabelecimentos,
        on='CO_UNIDADE',
        how='left'
    )
    
    df_merged['Estado_UF'] = df_merged['CO_UF'].map(IBGE_UF_MAP)
    df_merged = df_merged.dropna(subset=['Estado_UF', 'Tipo_Equipe'])

    # Preparação dos dados (Top 15 estados)
    df_plot_data = pd.crosstab(df_merged['Estado_UF'], df_merged['Tipo_Equipe'])
    
    for col in MAP_EQUIPES.values():
        if col not in df_plot_data:
            df_plot_data[col] = 0
            
    df_plot_data = df_plot_data[['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R']]
    df_plot_data['Total'] = df_plot_data.sum(axis=1)
    df_plot_data = df_plot_data.sort_values(by='Total', ascending=False)
    df_plot_data_top15 = df_plot_data.head(15)

    # Gráfico de barras empilhadas por estado
    fig, ax_bar = plt.subplots(figsize=(18, 10))
    plot_cols = ['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R']
    
    df_plot_data_top15[plot_cols].plot(
        kind='bar', 
        stacked=True, 
        ax=ax_bar, 
        width=0.8
    )
    
    ax_bar.set_xlabel('Estado (UF)', fontsize=14, labelpad=10)
    ax_bar.set_ylabel('Número Total de Equipes', fontsize=14, labelpad=10)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    
    # Legenda com descrições detalhadas
    legend_labels = [
        'EMAD I - Equipe Multiprofissional (maior porte)',
        'EMAD II - Equipe Multiprofissional (menor porte)',  
        'EMAP - Equipe Multiprofissional de Apoio',
        'EMAP-R - Equipe Multiprofissional de Apoio para Reabilitação'
    ]
    handles, _ = ax_bar.get_legend_handles_labels()
    ax_bar.legend(handles, legend_labels, title='Tipo de Equipe', title_fontsize='13', fontsize='10', loc='upper right')
    
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)
    ax_bar.yaxis.grid(color='gray', linestyle='dashed', alpha=0.5)
    ax_bar.set_axisbelow(True)
    
    plt.tight_layout()
    nome_grafico = 'distribuicao_equipes_por_estado_empilhado.png'
    plt.savefig(nome_grafico, bbox_inches='tight')
    print(f"Gráfico salvo: {nome_grafico}")

    # === SAÍDA DE VERIFICAÇÃO: Tabela completa por estado e tipo ===
    print("\n" + "=" * 70)
    print("DISTRIBUIÇÃO DE EQUIPES POR ESTADO E TIPO (tbEquipe - sem filtro de profissionais)")
    print("=" * 70)
    print(f"\n{'UF':<5} {'EMAD I':>8} {'EMAD II':>8} {'EMAP':>8} {'EMAP-R':>8} {'TOTAL':>8}")
    print("-" * 50)
    for uf, row in df_plot_data.iterrows():
        print(f"{uf:<5} {int(row['EMAD I']):>8} {int(row['EMAD II']):>8} {int(row['EMAP']):>8} {int(row['EMAP-R']):>8} {int(row['Total']):>8}")
    print("-" * 50)
    total_row = df_plot_data[['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R', 'Total']].sum()
    print(f"{'TOTAL':<5} {int(total_row['EMAD I']):>8} {int(total_row['EMAD II']):>8} {int(total_row['EMAP']):>8} {int(total_row['EMAP-R']):>8} {int(total_row['Total']):>8}")
    print(f"\nNOTA: Este script usa tbEquipe diretamente (N={int(total_row['Total'])} equipes).")
    print("O relatório usa N=2.664 (equipes com profissionais vinculados via rlEstabEquipeProf).")


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
