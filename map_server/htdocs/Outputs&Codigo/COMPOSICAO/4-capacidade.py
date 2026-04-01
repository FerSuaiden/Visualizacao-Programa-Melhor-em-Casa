import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import sys
from pathlib import Path

print("Iniciando análise de CAPACIDADE POTENCIAL (CHS SUS) das equipes...")

# --- Nomes dos arquivos ---
# Fonte: CNES/DataSUS (competência 2025/08)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
arquivo_estabelecimentos = PROJECT_ROOT / 'CNES_DATA' / 'tbEstabelecimento202508.csv'
arquivo_equipes = PROJECT_ROOT / 'CNES_DATA' / 'tbEquipe202508.csv'
arquivo_profissionais_equipe = PROJECT_ROOT / 'CNES_DATA' / 'rlEstabEquipeProf202508.csv'
arquivo_cargas_horarias = PROJECT_ROOT / 'CNES_DATA' / 'tbCargaHorariaSus202508.csv'

# --- Dicionários de Mapeamento ---
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
    # Fonte: CNES/DataSUS (competência 2025/08)
    df_estab = pd.read_csv(
        arquivo_estabelecimentos, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'CO_ESTADO_GESTOR']
    )
    df_estab = df_estab.rename(columns={'CO_ESTADO_GESTOR': 'CO_UF'})
    
    df_equipes = pd.read_csv(
        arquivo_equipes, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'TP_EQUIPE', 'DT_DESATIVACAO']
    )
    
    df_prof_equipe = pd.read_csv(
        arquivo_profissionais_equipe, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'CO_PROFISSIONAL_SUS', 'DT_DESLIGAMENTO']
    )
    
    df_chs = pd.read_csv(
        arquivo_cargas_horarias, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS',
                 'QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    )

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

    # Equipes -> Profissionais
    df_merge1 = pd.merge(
        df_equipes_filtradas,
        df_prof_ativos,
        on=['CO_UNIDADE', 'SEQ_EQUIPE'],
        how='inner'
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
    
    # Profissionais -> Cargas horárias
    df_completo = pd.merge(
        df_merge1,
        df_chs,
        on=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS'],
        how='left'
    )
    df_completo = pd.merge(
        df_completo,
        df_n_equipes_prof,
        on=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS'],
        how='left'
    )

    # Cálculo da Capacidade (Qk)
    # CHS por profissional é rateada entre equipes AD ativas na mesma unidade
    df_completo['CHS_TOTAL'] = df_completo['CHS_TOTAL'].fillna(0)
    df_completo['N_EQUIPE_PROF_UNIDADE'] = df_completo['N_EQUIPE_PROF_UNIDADE'].fillna(1)
    df_completo['CHS_PROFISSIONAL_TOTAL'] = (
        df_completo['CHS_TOTAL'] / df_completo['N_EQUIPE_PROF_UNIDADE']
    )

    # Agregação por equipe (CO_UNIDADE + SEQ_EQUIPE identificam uma equipe única)
    df_capacidade_equipe = df_completo.groupby(['CO_UNIDADE', 'SEQ_EQUIPE'])['CHS_PROFISSIONAL_TOTAL'].sum().reset_index()
    df_capacidade_equipe = df_capacidade_equipe.rename(columns={'CHS_PROFISSIONAL_TOTAL': 'Qk_CHS_Equipe'})

    # Junta de volta com df_equipes para saber o TP_EQUIPE de cada equipe
    df_capacidade_final = pd.merge(
        df_capacidade_equipe,
        df_equipes_filtradas,
        on=['CO_UNIDADE', 'SEQ_EQUIPE'],
        how='left'
    )

    # Junta com df_estab para saber o Estado (UF) de cada equipe
    df_dados_plot = pd.merge(
        df_capacidade_final,
        df_estab,
        on='CO_UNIDADE',
        how='left'
    )
    df_dados_plot['Estado_UF'] = df_dados_plot['CO_UF'].map(IBGE_UF_MAP)
    df_dados_plot = df_dados_plot.dropna(subset=['Estado_UF'])

    # Gráfico 1: Capacidade total por estado
    df_plot_chs_estado = df_dados_plot.groupby('Estado_UF')['Qk_CHS_Equipe'].sum().sort_values(ascending=False).head(15)
    
    fig, ax1 = plt.subplots(figsize=(18, 10))
    df_plot_chs_estado.sort_values(ascending=True).plot(
        kind='barh', 
        ax=ax1,
        color='darkgreen'
    )
    
    ax1.set_xlabel('Capacidade Potencial (Horas Semanais CHS SUS)', fontsize=14)
    ax1.set_ylabel('Estado (UF)', fontsize=14)
    
    # Formata o eixo X para milhares
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{int(x/1000)}k' if x > 0 else 0))
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    plt.tight_layout()
    
    nome_grafico_chs_estado = 'capacidade_total_chs_por_estado.png'
    plt.savefig(nome_grafico_chs_estado)

    # Gráfico 2: Histograma de distribuição de Qk
    # Inclui equipes com Qk=0 para manter consistência com as estatísticas globais
    Qk_valores = df_dados_plot['Qk_CHS_Equipe']
    
    fig, ax2 = plt.subplots(figsize=(12, 7))
    
    # Cria um histograma para ver a distribuição de Qk
    ax2.hist(Qk_valores, bins=50, edgecolor='black', color='lightblue')
    
    media_chs = Qk_valores.mean()
    ax2.axvline(media_chs, color='red', linestyle='dashed', linewidth=2)
    ax2.text(media_chs * 1.05, ax2.get_ylim()[1] * 0.9, f'Média: {media_chs:.1f} horas', color='red')

    ax2.set_xlabel('Capacidade Potencial (Qk) - Total de Horas Semanais CHS SUS da Equipe', fontsize=12)
    ax2.set_ylabel('Número de Equipes', fontsize=12)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    nome_grafico_histograma = 'distribuicao_capacidade_Qk_histograma.png'
    plt.savefig(nome_grafico_histograma)
    print(f"Gráficos salvos: {nome_grafico_chs_estado}, {nome_grafico_histograma}")

    # === SAÍDA DE VERIFICAÇÃO: Estatísticas de Qk ===
    Qk_todos = df_dados_plot['Qk_CHS_Equipe']  # Incluindo Qk=0
    print("\n" + "=" * 70)
    print("ESTATÍSTICAS DESCRITIVAS DE Qk (CHS SUS total por equipe)")
    print("=" * 70)
    print(f"  N (equipes com Qk calculado): {len(Qk_todos):,}")
    print(f"  Mínimo:         {Qk_todos.min():.0f} h/semana")
    print(f"  Máximo:         {Qk_todos.max():.0f} h/semana")
    print(f"  Mediana:        {Qk_todos.median():.0f} h/semana")
    print(f"  Média:          {Qk_todos.mean():.1f} h/semana")
    print(f"  Desvio Padrão:  {Qk_todos.std():.1f} h/semana")
    
    # === SAÍDA DE VERIFICAÇÃO: CHS total por estado (Top 15) ===
    print("\n" + "=" * 70)
    print("CAPACIDADE POTENCIAL TOTAL (CHS SUS) POR ESTADO - TOP 15")
    print("=" * 70)
    chs_por_estado = df_dados_plot.groupby('Estado_UF')['Qk_CHS_Equipe'].sum().sort_values(ascending=False)
    print(f"\n{'UF':<5} {'CHS Total (h)':>15}")
    print("-" * 25)
    for uf, chs in chs_por_estado.head(15).items():
        print(f"{uf:<5} {chs:>15,.0f}")
    print("-" * 25)
    print(f"{'BRASIL':<5} {chs_por_estado.sum():>15,.0f}")
    print("\nNOTA METODOLÓGICA: CHS SUS = Ambulatorial + Hospitalar + Outros no CNES.")
    print("Não representa, necessariamente, horas exclusivas dedicadas à Atenção Domiciliar.")

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