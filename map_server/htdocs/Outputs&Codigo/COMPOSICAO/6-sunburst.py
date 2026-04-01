import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Caminhos dos arquivos (Fonte: CNES/DataSUS - competência 2025/08)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
arquivo_estabelecimentos = PROJECT_ROOT / 'CNES_DATA' / 'tbEstabelecimento202508.csv'
arquivo_equipes = PROJECT_ROOT / 'CNES_DATA' / 'tbEquipe202508.csv'
arquivo_profissionais_equipe = PROJECT_ROOT / 'CNES_DATA' / 'rlEstabEquipeProf202508.csv'
arquivo_cargas_horarias = PROJECT_ROOT / 'CNES_DATA' / 'tbCargaHorariaSus202508.csv'
arquivo_cbo = PROJECT_ROOT / 'CBO_DATA' / 'CBO2002 - Ocupacao.csv'

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
        arquivo_equipes, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'TP_EQUIPE', 'DT_DESATIVACAO']
    )
    
    df_prof_equipe = pd.read_csv(
        arquivo_profissionais_equipe, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'CO_PROFISSIONAL_SUS', 'CO_CBO', 'DT_DESLIGAMENTO']
    )
    
    df_chs = pd.read_csv(
        arquivo_cargas_horarias, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS',
                 'QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    )
    
    # Carrega o dicionário de CBO. O '' indica problema de encoding. 'latin-1' ou 'cp1252' costumam resolver.
    df_cbo = pd.read_csv(
        arquivo_cbo, sep=';', encoding='latin-1', dtype=str,
        usecols=['CODIGO', 'TITULO']
    )
    df_cbo = df_cbo.rename(columns={'CODIGO': 'CO_CBO', 'TITULO': 'Profissao'})

    # Filtragem de atividade
    df_equipes['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce'
    )
    df_equipes_ativas = df_equipes[df_equipes['DT_DESATIVACAO'].isna()].copy()

    df_prof_equipe['DT_DESLIGAMENTO'] = pd.to_datetime(
        df_prof_equipe['DT_DESLIGAMENTO'], format='%d/%m/%Y', errors='coerce'
    )
    df_prof_ativos = df_prof_equipe[df_prof_equipe['DT_DESLIGAMENTO'].isna()].copy()

    # Filtragem e merge
    df_equipes_filtradas = df_equipes_ativas[df_equipes_ativas['TP_EQUIPE'].isin(CODIGOS_RELEVANTES)]

    df_merge1 = pd.merge(
        df_equipes_filtradas, df_prof_ativos,
        on=['CO_UNIDADE', 'SEQ_EQUIPE'], how='inner'
    )

    # Quantidade de equipes AD ativas por profissional na mesma unidade (para rateio de CHS)
    df_n_equipes_prof = (
        df_merge1.groupby(['CO_UNIDADE', 'CO_PROFISSIONAL_SUS'])['SEQ_EQUIPE']
        .nunique()
        .reset_index(name='N_EQUIPE_PROF_UNIDADE')
    )

    # CHS por profissional na unidade (mesma lógica da PARTE4)
    cols_chs = ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    for col in cols_chs:
        df_chs[col] = pd.to_numeric(df_chs[col], errors='coerce').fillna(0)
    df_chs['CHS_TOTAL'] = df_chs[cols_chs].sum(axis=1)
    df_chs = df_chs.groupby(['CO_UNIDADE', 'CO_PROFISSIONAL_SUS'])['CHS_TOTAL'].sum().reset_index()
    
    df_merge2 = pd.merge(
        df_merge1, df_chs,
        on=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS'], how='left'
    )
    df_merge2 = pd.merge(
        df_merge2, df_n_equipes_prof,
        on=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS'], how='left'
    )
    
    df_final = pd.merge(
        df_merge2, df_cbo,
        on='CO_CBO', how='left'
    )

    # Cálculo da CHS e limpeza de dados
    df_final['CHS_TOTAL'] = df_final['CHS_TOTAL'].fillna(0)
    df_final['N_EQUIPE_PROF_UNIDADE'] = df_final['N_EQUIPE_PROF_UNIDADE'].fillna(1)
    df_final['CHS_Profissional'] = (
        df_final['CHS_TOTAL'] / df_final['N_EQUIPE_PROF_UNIDADE']
    )
    df_final['Tipo_Equipe'] = df_final['TP_EQUIPE'].map(MAP_EQUIPES)
    
    df_final = df_final.dropna(subset=['CHS_Profissional', 'Profissao', 'Tipo_Equipe'])
    df_final = df_final[df_final['CHS_Profissional'] > 0]

    # Preparação dos dados para o Sunburst
    df_plot_data = df_final.groupby(['Tipo_Equipe', 'Profissao'])['CHS_Profissional'].sum().reset_index()
    
    # Agrupa profissões minoritárias (<0.5%)
    total_chs = df_plot_data['CHS_Profissional'].sum()
    limite = total_chs * 0.005
    df_plot_data.loc[df_plot_data['CHS_Profissional'] < limite, 'Profissao'] = 'Outras Profissões (<0.5%)'
    df_plot_data = df_plot_data.groupby(['Tipo_Equipe', 'Profissao'])['CHS_Profissional'].sum().reset_index()

    # Geração do gráfico Sunburst (sem plotly.express para evitar dependências opcionais)
    cores_tipo = {
        'EMAD I': '#006BA2',
        'EMAD II': '#5EBCD1',
        'EMAP': '#E5323B',
        'EMAP-R': '#F29C38',
        '(?)': 'grey'
    }

    ids = []
    labels = []
    parents = []
    values = []
    colors = []

    total_por_tipo = df_plot_data.groupby('Tipo_Equipe', as_index=False)['CHS_Profissional'].sum()
    for _, row in total_por_tipo.iterrows():
        tipo = row['Tipo_Equipe']
        tipo_id = f"TIPO::{tipo}"
        ids.append(tipo_id)
        labels.append(tipo)
        parents.append('')
        values.append(row['CHS_Profissional'])
        colors.append(cores_tipo.get(tipo, 'grey'))

    for _, row in df_plot_data.iterrows():
        tipo = row['Tipo_Equipe']
        profissao = row['Profissao']
        ids.append(f"PROF::{tipo}::{profissao}")
        labels.append(profissao)
        parents.append(f"TIPO::{tipo}")
        values.append(row['CHS_Profissional'])
        colors.append(cores_tipo.get(tipo, 'grey'))

    fig = go.Figure(go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        branchvalues='total',
        textinfo='label+percent parent',
        insidetextorientation='radial'
    ))
    
    # Melhora a legibilidade
    fig.update_layout(
        margin=dict(t=25, l=25, r=25, b=120),
        font_size=12,
        # Adiciona anotações como legenda
        annotations=[
            dict(
                text="<b>Legenda:</b><br>" +
                     "<span style='color:#006BA2'>●</span> EMAD I - Equipe Multiprofissional (maior porte)<br>" +
                     "<span style='color:#5EBCD1'>●</span> EMAD II - Equipe Multiprofissional (menor porte)<br>" +
                     "<span style='color:#E5323B'>●</span> EMAP - Equipe Multiprofissional de Apoio<br>" +
                     "<span style='color:#F29C38'>●</span> EMAP-R - Equipe Multiprofissional de Apoio para Reabilitação<br><br>" +
                     "<i>Nota: CHS SUS representa potencial de disponibilidade para atendimento domiciliar no SUS e não dedicação exclusiva à modalidade.</i>",
                align='left',
                showarrow=False,
                xref='paper', yref='paper',
                x=0, y=-0.08,
                font=dict(size=13)
            )
        ]
    )
    nome_grafico_sunburst = 'habilidades_sunburst.html'
    fig.write_html(nome_grafico_sunburst)
    print(f"Gráfico salvo: {nome_grafico_sunburst}")

    # === SAÍDA DE VERIFICAÇÃO: Composição profissional por vínculos profissional-CBO ===
    # Conta pares únicos profissional-CBO (captura profissionais com mais de um CBO)
    df_prof_unicos = df_merge1.drop_duplicates(subset=['CO_PROFISSIONAL_SUS', 'CO_CBO'])[['CO_PROFISSIONAL_SUS', 'CO_CBO']].copy()
    df_prof_unicos = pd.merge(df_prof_unicos, df_cbo, on='CO_CBO', how='left')
    
    # Agrupa profissões minoritárias
    contagem = df_prof_unicos['Profissao'].value_counts()
    total_prof = len(df_prof_unicos)
    limite_agrup = total_prof * 0.003  # <0.3%
    prof_minoritarias = contagem[contagem < limite_agrup].index
    df_prof_unicos.loc[df_prof_unicos['Profissao'].isin(prof_minoritarias), 'Profissao'] = 'Outras Profissões'
    contagem_final = df_prof_unicos['Profissao'].value_counts()
    
    print("\n" + "=" * 70)
    print("COMPOSIÇÃO PROFISSIONAL - VÍNCULOS ÚNICOS PROFISSIONAL-CBO")
    print("=" * 70)
    print(f"\n{'Categoria':<35} {'Qtde':>8} {'%':>8}")
    print("-" * 55)
    for prof, qtd in contagem_final.items():
        pct = 100 * qtd / total_prof
        print(f"{prof:<35} {qtd:>8} {pct:>7.1f}%")
    print("-" * 55)
    print(f"{'TOTAL VÍNCULOS':<35} {total_prof:>8} {'100.0%':>8}")

except FileNotFoundError as e:
    print(f"\nERRO: O arquivo '{e.filename}' não foi encontrado.")
    print("Por favor, verifique se os caminhos e nomes dos arquivos estão corretos.")
    sys.exit(1)
except KeyError as e:
    print(f"\nERRO: A coluna {e} não foi encontrada.")
    print("Verifique se os nomes das colunas estão corretos nos seus arquivos CSV.")
    sys.exit(1)
except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")
    sys.exit(1)