import pandas as pd
import folium
from folium.plugins import HeatMap
import sys
from pathlib import Path

print("Iniciando geração do MAPA DE CALOR de Capacidade Potencial (CHS SUS) - Brasil...")

# --- Nomes dos arquivos ---
# Fonte: CNES/DataSUS (competência 2025/08)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
arquivo_estabelecimentos = PROJECT_ROOT / 'CNES_DATA' / 'tbEstabelecimento202508.csv'
arquivo_equipes = PROJECT_ROOT / 'CNES_DATA' / 'tbEquipe202508.csv'
arquivo_profissionais_equipe = PROJECT_ROOT / 'CNES_DATA' / 'rlEstabEquipeProf202508.csv'
arquivo_cargas_horarias = PROJECT_ROOT / 'CNES_DATA' / 'tbCargaHorariaSus202508.csv'

# Códigos das equipes AD (EMAD I/II, EMAP, EMAP-R)
CODIGOS_RELEVANTES = ['22', '46', '23', '77']

try:
    # Carregamento das bases de dados
    # Fonte: CNES/DataSUS (competência 2025/08)
    df_estab = pd.read_csv(
        arquivo_estabelecimentos, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'NU_LATITUDE', 'NU_LONGITUDE']
    )
    
    # Base de Equipes (para filtrar EMAD/EMAP)
    df_equipes = pd.read_csv(
        arquivo_equipes, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'TP_EQUIPE', 'DT_DESATIVACAO']
    )
    
    # Base de Profissionais por Equipe
    df_prof_equipe = pd.read_csv(
        arquivo_profissionais_equipe, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'CO_PROFISSIONAL_SUS', 'DT_DESLIGAMENTO']
    )
    
    # Base de Carga Horária
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

    # Cálculo da CHS por profissional (rateada entre equipes AD ativas na mesma unidade)
    df_completo['CHS_TOTAL'] = df_completo['CHS_TOTAL'].fillna(0)
    df_completo['N_EQUIPE_PROF_UNIDADE'] = df_completo['N_EQUIPE_PROF_UNIDADE'].fillna(1)
    df_completo['CHS_PROFISSIONAL_TOTAL'] = (
        df_completo['CHS_TOTAL'] / df_completo['N_EQUIPE_PROF_UNIDADE']
    )

    # Agregação por estabelecimento
    df_capacidade_estab = df_completo.groupby('CO_UNIDADE')['CHS_PROFISSIONAL_TOTAL'].sum().reset_index()
    df_capacidade_estab = df_capacidade_estab.rename(columns={'CHS_PROFISSIONAL_TOTAL': 'CHS_TOTAL_ESTABELECIMENTO'})
    df_capacidade_estab = df_capacidade_estab[df_capacidade_estab['CHS_TOTAL_ESTABELECIMENTO'] > 0]

    # Merge com coordenadas
    df_heatmap_data = pd.merge(
        df_capacidade_estab,
        df_estab,
        on='CO_UNIDADE',
        how='left'
    )

    # Limpeza de coordenadas
    df_heatmap_data['NU_LATITUDE'] = pd.to_numeric(df_heatmap_data['NU_LATITUDE'].str.replace(',', '.'), errors='coerce')
    df_heatmap_data['NU_LONGITUDE'] = pd.to_numeric(df_heatmap_data['NU_LONGITUDE'].str.replace(',', '.'), errors='coerce')
    df_heatmap_data = df_heatmap_data.dropna(subset=['NU_LATITUDE', 'NU_LONGITUDE', 'CHS_TOTAL_ESTABELECIMENTO'])

    # Geração do mapa de calor
    mapa_calor = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)
    
    # Prepara a lista de dados no formato [latitude, longitude, peso]
    heatmap_list = df_heatmap_data[['NU_LATITUDE', 'NU_LONGITUDE', 'CHS_TOTAL_ESTABELECIMENTO']].values.tolist()
    
    # Adiciona a camada de Mapa de Calor
    HeatMap(
        heatmap_list,
        name='Capacidade Potencial (CHS SUS) de Atenção Domiciliar',
        min_opacity=0.2,
        radius=15,
        blur=10
    ).add_to(mapa_calor)

    # Legenda explicativa
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 380px; height: auto; 
                border:2px solid grey; z-index:9999; font-size:14px;
                background-color:white; opacity: .92; padding: 14px;
                line-height: 1.6;
                ">
                <b style="font-size:16px;">Mapa de Calor &mdash; Capacidade Potencial (CHS SUS)</b><br><br>
                <div style="display:flex; align-items:center; margin-bottom:8px;">
                    <div style="width:200px; height:18px; background: linear-gradient(to right, #0000ff, #00ff00, #ffff00, #ff0000); border-radius:3px;"></div>
                    <span style="margin-left:10px; font-size:13px;">Menor &rarr; Maior</span>
                </div>
                <span style="font-size:13px; line-height:1.7;">
                A intensidade da cor indica a <b>Carga Horária Semanal CHS SUS</b><br>
                total dos profissionais de Atenção Domiciliar vinculados<br>
                a cada estabelecimento de saúde (EMAD + EMAP).<br>
                <b>Azul:</b> Baixa capacidade &nbsp;|&nbsp; <b>Vermelho:</b> Alta capacidade<br>
                <hr style="margin: 8px 0;">
                <i>Nota: CHS SUS representa potencial de disponibilidade para atendimento domiciliar no SUS e não dedicação exclusiva à modalidade.</i>
                </span>
    </div>
    """
    mapa_calor.get_root().html.add_child(folium.Element(legend_html))

    nome_arquivo = 'mapa_calor_chs_brasil.html'
    mapa_calor.save(nome_arquivo)
    print(f"Mapa salvo: {nome_arquivo}")

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