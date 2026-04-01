import pandas as pd
import folium
from folium.plugins import MarkerCluster
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
CNES_DIR = PROJECT_ROOT / 'CNES_DATA'

UF_BY_CODE = {
    '12': 'AC', '27': 'AL', '13': 'AM', '16': 'AP', '29': 'BA', '23': 'CE', '53': 'DF',
    '32': 'ES', '52': 'GO', '21': 'MA', '31': 'MG', '50': 'MS', '51': 'MT', '15': 'PA',
    '25': 'PB', '26': 'PE', '22': 'PI', '41': 'PR', '33': 'RJ', '24': 'RN', '11': 'RO',
    '14': 'RR', '43': 'RS', '42': 'SC', '28': 'SE', '35': 'SP', '17': 'TO'
}

MAPAS_DIR = SCRIPT_DIR / 'mapas_Equipes_Atencao_Domiciliar_por_estado'


def create_state_map(df_mapeamento_estado, cnes_com_atendimento, cnes_com_apoio, uf):
    centro_lat = df_mapeamento_estado['NU_LATITUDE'].mean()
    centro_lon = df_mapeamento_estado['NU_LONGITUDE'].mean()

    mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=7)
    marker_cluster = MarkerCluster(options={'disableClusteringAtZoom': 17, 'maxClusterRadius': 40}).add_to(mapa)

    for _, row in df_mapeamento_estado.iterrows():
        cnes_atual = row['CO_UNIDADE']
        tem_atendimento = cnes_atual in cnes_com_atendimento
        tem_apoio = cnes_atual in cnes_com_apoio

        cor = 'gray'
        categoria = 'Indefinido'

        if tem_atendimento and tem_apoio:
            cor = 'purple'
            categoria = 'Atendimento (EMAD) e Apoio (EMAP/EMAP-R)'
        elif tem_atendimento:
            cor = 'blue'
            categoria = 'Apenas Atendimento (EMAD I/II)'
        elif tem_apoio:
            cor = 'green'
            categoria = 'Apenas Apoio (EMAP/EMAP-R)'

        popup_text = (
            f"<b>{row.get('NO_FANTASIA', 'N/A')}</b><br>"
            f"<b>Equipes:</b> {categoria}<br>"
            f"<b>Endereço:</b> {row.get('NO_LOGRADOURO', '')}, {row.get('NU_ENDERECO', '')}<br>"
            f"<b>CNES:</b> {row.get('CO_CNES', 'N/A')}"
        )

        folium.Marker(
            location=[row['NU_LATITUDE'], row['NU_LONGITUDE']],
            popup=popup_text,
            icon=folium.Icon(color=cor, icon='plus-sign')
        ).add_to(marker_cluster)

    legend_html = f"""
    <div style="position: fixed;
                bottom: 50px; left: 50px; width: 420px; height: auto;
                border:2px solid grey; z-index:9999; font-size:14px;
                background-color:white; opacity: .92; padding: 14px;
                line-height: 1.6;
                ">
                <b style="font-size:16px;">Legenda - Programa Melhor em Casa ({uf})</b><br><br>
                <i class="fa fa-map-marker fa-2x" style="color:purple"></i>&nbsp; <b>Atendimento + Apoio</b> (EMAD + EMAP)<br>
                <i class="fa fa-map-marker fa-2x" style="color:blue"></i>&nbsp; <b>Apenas EMAD</b> (Equipe de Atendimento)<br>
                <i class="fa fa-map-marker fa-2x" style="color:green"></i>&nbsp; <b>Apenas EMAP</b> (Equipe de Apoio)<br>
                <hr style="margin: 10px 0;">
                <span style="line-height: 1.7; font-size: 13px;">
                <b>EMAD I/II:</b> Equipe Multiprofissional de Atenção Domiciliar<br>
                <b>EMAP:</b> Equipe Multiprofissional de Apoio<br>
                <b>EMAP-R:</b> Equipe Multiprofissional de Apoio para Reabilitação
                </span>
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(legend_html))

    return mapa

try:
    # Carregamento das bases de dados
    # Fonte: CNES/DataSUS (competência 2025/08)
    df_estabelecimentos = pd.read_csv(CNES_DIR / 'tbEstabelecimento202508.csv', sep=';', encoding='latin-1', dtype=str)
    df_equipes = pd.read_csv(CNES_DIR / 'tbEquipe202508.csv', sep=';', encoding='latin-1', dtype=str)

    # Filtrar apenas equipes ativas
    df_equipes['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce'
    )
    df_equipes = df_equipes[df_equipes['DT_DESATIVACAO'].isna()].copy()

    # Identificação das equipes AD por categoria
    codigos_atendimento = ['22', '46']  # EMAD I e EMAD II
    codigos_apoio = ['23', '77']        # EMAP e EMAP-R

    cnes_com_atendimento = set(df_equipes[df_equipes['TP_EQUIPE'].isin(codigos_atendimento)]['CO_UNIDADE'].unique())
    cnes_com_apoio = set(df_equipes[df_equipes['TP_EQUIPE'].isin(codigos_apoio)]['CO_UNIDADE'].unique())
    lista_cnes_total = list(cnes_com_atendimento.union(cnes_com_apoio))

    df_estabelecimentos_filtrados = df_estabelecimentos[df_estabelecimentos['CO_UNIDADE'].isin(lista_cnes_total)].copy()

    # Tratamento de coordenadas
    df_estabelecimentos_filtrados['NU_LATITUDE'] = pd.to_numeric(
        df_estabelecimentos_filtrados['NU_LATITUDE'].str.replace(',', '.'),
        errors='coerce'
    )
    df_estabelecimentos_filtrados['NU_LONGITUDE'] = pd.to_numeric(
        df_estabelecimentos_filtrados['NU_LONGITUDE'].str.replace(',', '.'),
        errors='coerce'
    )
    df_mapeamento = df_estabelecimentos_filtrados.dropna(subset=['NU_LATITUDE', 'NU_LONGITUDE']).copy()
    df_mapeamento = df_mapeamento[(df_mapeamento['NU_LATITUDE'] != 0) & (df_mapeamento['NU_LONGITUDE'] != 0)]

    MAPAS_DIR.mkdir(parents=True, exist_ok=True)

    mapas_gerados = 0
    for co_estado, uf in UF_BY_CODE.items():
        df_estado = df_mapeamento[df_mapeamento['CO_ESTADO_GESTOR'] == co_estado].copy()
        if df_estado.empty:
            print(f"Sem dados georreferenciados para {uf}, pulando.")
            continue

        mapa_estado = create_state_map(df_estado, cnes_com_atendimento, cnes_com_apoio, uf)
        nome_arquivo_estado = MAPAS_DIR / f'mapa_Equipes_Atencao_Domiciliar_{uf}.html'
        mapa_estado.save(nome_arquivo_estado)
        mapas_gerados += 1
        print(f"Mapa salvo: {nome_arquivo_estado}")

        # Compatibilidade com artefato histórico de SP
        if uf == 'SP':
            nome_arquivo_sp_legacy = SCRIPT_DIR / 'mapa_Equipes_Atencao_Domiciliar_SP.html'
            mapa_estado.save(nome_arquivo_sp_legacy)
            print(f"Mapa legado salvo: {nome_arquivo_sp_legacy}")

    print(f"Total de mapas gerados: {mapas_gerados}")

except FileNotFoundError as e:
    print(f"ERRO: O arquivo {e.filename} não foi encontrado.")
    raise SystemExit(1)
except KeyError as e:
    print(f"ERRO: A coluna {e} não foi encontrada.")
    raise SystemExit(1)
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
    raise SystemExit(1)