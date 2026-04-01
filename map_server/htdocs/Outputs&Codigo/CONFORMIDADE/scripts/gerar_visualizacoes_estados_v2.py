#!/usr/bin/env python3
"""
===============================================================================
GERADOR DE VISUALIZAÇÕES POR ESTADO - V2 (CONFORMIDADE POR MUNICÍPIO)
===============================================================================

Para cada um dos 27 estados brasileiros, gera:
1. Top 15 municípios por número de equipes AD (horizontal)
2. Gráfico de conformidade por município - Top 15 com mais equipes (horizontal)

Também gera visualização nacional de conformidade e cobertura.

Fontes:
- CNES/DATASUS (competência 08/2025)
- Portaria GM/MS nº 3.005/2024

===============================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

BASE_DIR = '/home/fersuaiden/Área de trabalho/Faculdade/IC'
CNES_DIR = os.path.join(BASE_DIR, 'CNES_DATA')
IBGE_DIR = os.path.join(BASE_DIR, 'IBGE_DATA')
PARTE4_DIR = os.path.join(BASE_DIR, 'Outputs&Codigo/CONFORMIDADE')
OUTPUT_ESTADOS_DIR = os.path.join(PARTE4_DIR, 'visualizacoes/estados')
OUTPUT_NACIONAL_DIR = os.path.join(PARTE4_DIR, 'visualizacoes/nacional')
DADOS_CSV_DIR = os.path.join(PARTE4_DIR, 'dados_csv')

# Mapeamento UF
IBGE_UF_MAP = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
    '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',
    '28': 'SE', '29': 'BA',
    '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
    '41': 'PR', '42': 'SC', '43': 'RS',
    '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF',
}

# Nome completo dos estados
NOME_UF = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
    'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
    'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
    'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins',
}

UF_REGIAO = {
    'RO': 'Norte', 'AC': 'Norte', 'AM': 'Norte', 'RR': 'Norte', 
    'PA': 'Norte', 'AP': 'Norte', 'TO': 'Norte',
    'MA': 'Nordeste', 'PI': 'Nordeste', 'CE': 'Nordeste', 'RN': 'Nordeste',
    'PB': 'Nordeste', 'PE': 'Nordeste', 'AL': 'Nordeste', 'SE': 'Nordeste', 'BA': 'Nordeste',
    'MG': 'Sudeste', 'ES': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
    'PR': 'Sul', 'SC': 'Sul', 'RS': 'Sul',
    'MS': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'DF': 'Centro-Oeste',
}

CORES_REGIAO = {
    'Norte': '#1abc9c', 
    'Nordeste': '#f39c12', 
    'Sudeste': '#3498db', 
    'Sul': '#27ae60', 
    'Centro-Oeste': '#9b59b6'
}

# Total de municípios por UF (IBGE 2022)
MUNICIPIOS_POR_UF = {
    'RO': 52, 'AC': 22, 'AM': 62, 'RR': 15, 'PA': 144, 'AP': 16, 'TO': 139,
    'MA': 217, 'PI': 224, 'CE': 184, 'RN': 167, 'PB': 223, 'PE': 185, 'AL': 102, 'SE': 75, 'BA': 417,
    'MG': 853, 'ES': 78, 'RJ': 92, 'SP': 645,
    'PR': 399, 'SC': 295, 'RS': 497,
    'MS': 79, 'MT': 141, 'GO': 246, 'DF': 1,
}

TOTAL_MUNICIPIOS_BRASIL = sum(MUNICIPIOS_POR_UF.values())

TIPOS_EQUIPE_AD = {22: 'EMAD I', 46: 'EMAD II', 23: 'EMAP', 77: 'EMAP-R'}
CORES_TIPO = {'EMAD I': '#2ecc71', 'EMAD II': '#3498db', 'EMAP': '#e74c3c', 'EMAP-R': '#9b59b6'}


def extrair_uf(codigo_municipio):
    """Extrai sigla UF do código IBGE do município."""
    prefixo = str(codigo_municipio).strip()[:2]
    return IBGE_UF_MAP.get(prefixo, 'DESCONHECIDO')


def main():
    print("=" * 80)
    print("GERADOR DE VISUALIZAÇÕES POR ESTADO - V2 (COM CONFORMIDADE)")
    print("=" * 80)
    
    # =========================================================================
    # ETAPA 1: CARREGAR DADOS
    # =========================================================================
    
    print("\n[1] Carregando dados...")
    
    # Equipes AD
    df_equipes = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    
    df_equipes_ad = df_equipes[df_equipes['TP_EQUIPE'].isin(TIPOS_EQUIPE_AD.keys())].copy()
    df_equipes_ad['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes_ad['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce'
    )
    df_ativas = df_equipes_ad[df_equipes_ad['DT_DESATIVACAO'].isna()].copy()
    df_ativas['CO_MUNICIPIO'] = df_ativas['CO_MUNICIPIO'].astype(str)
    df_ativas['UF'] = df_ativas['CO_MUNICIPIO'].apply(extrair_uf)
    df_ativas['TIPO_NOME'] = df_ativas['TP_EQUIPE'].map(TIPOS_EQUIPE_AD)
    
    print(f"    Total de equipes AD ativas: {len(df_ativas):,}")
    
    # Carregar dados de conformidade
    arquivo_conformidade = os.path.join(DADOS_CSV_DIR, 'conformidade_legal_brasil_v2.csv')
    if os.path.exists(arquivo_conformidade):
        print("    Carregando dados de conformidade...")
        df_conformidade = pd.read_csv(arquivo_conformidade, sep=';')
        print(f"    Equipes com dados de conformidade: {len(df_conformidade):,}")
        
        # Adicionar informação de município ao df_conformidade
        # SEQ_EQUIPE no df_conformidade, cruzar com df_ativas
        # Primeiro criar mapeamento SEQ_EQUIPE -> CO_MUNICIPIO
        seq_to_mun = dict(zip(df_ativas['SEQ_EQUIPE'].astype(str), df_ativas['CO_MUNICIPIO']))
        df_conformidade['SEQ_EQUIPE'] = df_conformidade['SEQ_EQUIPE'].astype(str)
        df_conformidade['CO_MUNICIPIO'] = df_conformidade['SEQ_EQUIPE'].map(seq_to_mun)
        
        # Contagem de conformidade por município e UF
        conformidade_match = df_conformidade['CO_MUNICIPIO'].notna().sum()
        print(f"    Equipes de conformidade com município identificado: {conformidade_match:,}")
        tem_conformidade = True
    else:
        print("    AVISO: Arquivo de conformidade não encontrado.")
        print("    O script seguirá apenas com visualizações de cobertura/equipes.")
        df_conformidade = pd.DataFrame(columns=['SEQ_EQUIPE', 'UF', 'CONFORME', 'CO_MUNICIPIO'])
        tem_conformidade = False
    
    # Carregar tabela de municípios do IBGE
    arquivo_mun_ibge = os.path.join(IBGE_DIR, 'municipios_ibge.csv')
    df_municipios = None
    
    if os.path.exists(arquivo_mun_ibge):
        print("    Carregando tabela de municípios IBGE...")
        df_municipios = pd.read_csv(arquivo_mun_ibge, sep=';', dtype=str, encoding='utf-8')
    
    # =========================================================================
    # ETAPA 2: AGREGAR DADOS POR MUNICÍPIO
    # =========================================================================
    
    print("\n[2] Agregando dados por município...")
    
    # Contar equipes por município e tipo
    df_por_mun = df_ativas.groupby(['CO_MUNICIPIO', 'UF']).agg({
        'SEQ_EQUIPE': 'count',
        'TIPO_NOME': lambda x: ', '.join(sorted(x.unique()))
    }).reset_index()
    df_por_mun.columns = ['CO_MUNICIPIO', 'UF', 'N_EQUIPES', 'TIPOS']
    
    # Adicionar nome do município
    if df_municipios is not None and 'CO_MUNICIPIO' in df_municipios.columns:
        df_municipios['CO_MUNICIPIO_6'] = df_municipios['CO_MUNICIPIO'].astype(str).str[:6]
        nome_map = dict(zip(df_municipios['CO_MUNICIPIO_6'], df_municipios['NO_MUNICIPIO']))
        df_por_mun['NO_MUNICIPIO'] = df_por_mun['CO_MUNICIPIO'].astype(str).str[:6].map(nome_map)
        print(f"    Municípios com nome identificado: {df_por_mun['NO_MUNICIPIO'].notna().sum()}")
    else:
        df_por_mun['NO_MUNICIPIO'] = df_por_mun['CO_MUNICIPIO']
    
    print(f"    Municípios com equipes AD: {len(df_por_mun):,}")
    
    # =========================================================================
    # ETAPA 3: GERAR VISUALIZAÇÃO NACIONAL DE CONFORMIDADE
    # =========================================================================
    
    print("\n[3] Gerando visualização nacional de conformidade...")
    
    # Estatísticas nacionais
    total_equipes = len(df_conformidade)
    equipes_conformes = df_conformidade['CONFORME'].sum() if total_equipes > 0 else 0
    equipes_nao_conformes = total_equipes - equipes_conformes
    taxa_conformidade_equipes = 100 * equipes_conformes / total_equipes if total_equipes > 0 else 0
    
    total_municipios_brasil = TOTAL_MUNICIPIOS_BRASIL
    municipios_com_ad = len(df_por_mun)
    taxa_cobertura_municipal = 100 * municipios_com_ad / total_municipios_brasil
    
    # Criar 2 gráficos de donut separados
    resumo_dir = os.path.join(OUTPUT_NACIONAL_DIR, 'resumo')
    os.makedirs(resumo_dir, exist_ok=True)
    
    # ----- GRÁFICO 1: % Equipes Conformes -----
    if total_equipes > 0:
        fig1, ax1 = plt.subplots(figsize=(8, 7))
        
        sizes1 = [equipes_conformes, equipes_nao_conformes]
        labels1 = ['Conformes', 'Não Conformes']
        colors1 = ['#27ae60', '#e74c3c']
        explode1 = (0.03, 0)
        
        wedges1, texts1, autotexts1 = ax1.pie(
            sizes1, explode=explode1, labels=labels1, colors=colors1,
            autopct=lambda pct: f'{pct:.2f}%', startangle=90, pctdistance=0.75,
            wedgeprops=dict(width=0.5, edgecolor='white')
        )
        
        # Centro do donut
        ax1.text(0, 0, f'{taxa_conformidade_equipes:.2f}%\nConformes', 
                 ha='center', va='center', fontsize=14, fontweight='bold')
        
        ax1.legend([f'Conformes: {equipes_conformes:,}', f'Não Conformes: {equipes_nao_conformes:,}'],
                   loc='upper center', bbox_to_anchor=(0.5, -0.05), fontsize=10)
        
        plt.tight_layout()
        
        output_conformidade = os.path.join(resumo_dir, 'conformidade_nacional_donut.png')
        plt.savefig(output_conformidade, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig1)
        print(f"    Conformidade nacional: {output_conformidade}")
    else:
        print("    Sem dados de conformidade para donut nacional.")
    
    # ----- GRÁFICO 2: % Municípios com Cobertura -----
    fig2, ax2 = plt.subplots(figsize=(8, 7))
    
    municipios_sem_ad = total_municipios_brasil - municipios_com_ad
    sizes2 = [municipios_com_ad, municipios_sem_ad]
    labels2 = ['Com Equipes AD', 'Sem Cobertura']
    colors2 = ['#3498db', '#bdc3c7']
    explode2 = (0.03, 0)
    
    wedges2, texts2, autotexts2 = ax2.pie(
        sizes2, explode=explode2, labels=labels2, colors=colors2,
        autopct=lambda pct: f'{pct:.2f}%', startangle=90, pctdistance=0.75,
        wedgeprops=dict(width=0.5, edgecolor='white')
    )
    
    # Centro do donut
    ax2.text(0, 0, f'{taxa_cobertura_municipal:.2f}%\nCobertos', 
             ha='center', va='center', fontsize=14, fontweight='bold')
    
    ax2.legend([f'Com AD: {municipios_com_ad:,}', f'Sem AD: {municipios_sem_ad:,}'],
               loc='upper center', bbox_to_anchor=(0.5, -0.05), fontsize=10)
    
    plt.tight_layout()
    
    output_cobertura = os.path.join(resumo_dir, 'cobertura_nacional_donut.png')
    plt.savefig(output_cobertura, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig2)
    print(f"    Cobertura nacional: {output_cobertura}")
    
    # =========================================================================
    # ETAPA 4: GERAR VISUALIZAÇÕES POR ESTADO
    # =========================================================================
    
    print("\n[4] Gerando visualizações por estado...")
    
    ufs_ordenadas = sorted(df_por_mun['UF'].unique())
    print(f"    Estados a processar: {len(ufs_ordenadas)}")
    
    for uf in ufs_ordenadas:
        df_uf_mun = df_por_mun[df_por_mun['UF'] == uf].copy()
        df_uf_conf = df_conformidade[df_conformidade['UF'] == uf].copy()
        
        if len(df_uf_mun) == 0:
            print(f"    {uf}: Sem dados")
            continue
        
        # Criar pasta do estado
        pasta_uf = os.path.join(OUTPUT_ESTADOS_DIR, uf)
        os.makedirs(pasta_uf, exist_ok=True)
        
        nome_estado = NOME_UF.get(uf, uf)
        regiao = UF_REGIAO.get(uf, 'Desconhecida')
        cor_regiao = CORES_REGIAO.get(regiao, '#95a5a6')
        
        total_equipes_uf = df_uf_mun['N_EQUIPES'].sum()
        total_municipios_uf = len(df_uf_mun)
        
        # Conformidade do estado
        total_conf_uf = len(df_uf_conf)
        conformes_uf = df_uf_conf['CONFORME'].sum() if len(df_uf_conf) > 0 else 0
        taxa_conf_uf = 100 * conformes_uf / total_conf_uf if total_conf_uf > 0 else 0
        
        # Criar figura com 2 subplots lado a lado
        fig, axes = plt.subplots(1, 2, figsize=(16, 8))
        
        # ----- GRÁFICO 1: Top 15 municípios por número de equipes (HORIZONTAL) -----
        ax1 = axes[0]
        
        top_bruto = df_uf_mun.nlargest(min(15, len(df_uf_mun)), 'N_EQUIPES')
        
        if len(top_bruto) > 0:
            y_pos = np.arange(len(top_bruto))
            bars = ax1.barh(y_pos, top_bruto['N_EQUIPES'], color=cor_regiao, alpha=0.85)
            
            # Labels
            labels = top_bruto['NO_MUNICIPIO'].fillna(top_bruto['CO_MUNICIPIO']).tolist()
            labels = [l[:22] + '...' if len(str(l)) > 25 else str(l) for l in labels]
            
            ax1.set_yticks(y_pos)
            ax1.set_yticklabels(labels, fontsize=9)
            ax1.invert_yaxis()
            ax1.set_xlabel('Número de Equipes AD')
            
            # Anotações
            for i, (_, row) in enumerate(top_bruto.iterrows()):
                ax1.text(row['N_EQUIPES'] + 0.2, i, f"{int(row['N_EQUIPES'])}", 
                        va='center', fontsize=9, fontweight='bold')
            
            ax1.grid(True, alpha=0.3, axis='x')
            ax1.set_xlim(0, top_bruto['N_EQUIPES'].max() * 1.15)
        else:
            ax1.text(0.5, 0.5, 'Sem dados', ha='center', va='center', fontsize=14)
        
        # ----- GRÁFICO 2: Conformidade por Município (HORIZONTAL) -----
        ax2 = axes[1]
        
        # Filtrar conformidade do estado e agregar por município
        df_conf_uf_mun = df_uf_conf[df_uf_conf['CO_MUNICIPIO'].notna()].copy()
        
        if len(df_conf_uf_mun) > 0:
            # Agregar por município
            stats_mun = df_conf_uf_mun.groupby('CO_MUNICIPIO').agg({
                'CONFORME': ['count', 'sum']
            }).reset_index()
            stats_mun.columns = ['CO_MUNICIPIO', 'TOTAL', 'CONFORMES']
            stats_mun['NAO_CONFORMES'] = stats_mun['TOTAL'] - stats_mun['CONFORMES']
            stats_mun['TAXA_%'] = (100 * stats_mun['CONFORMES'] / stats_mun['TOTAL'])
            
            # Adicionar nome do município
            if df_municipios is not None:
                df_municipios['CO_MUNICIPIO_6'] = df_municipios['CO_MUNICIPIO'].astype(str).str[:6]
                nome_map = dict(zip(df_municipios['CO_MUNICIPIO_6'], df_municipios['NO_MUNICIPIO']))
                stats_mun['NO_MUNICIPIO'] = stats_mun['CO_MUNICIPIO'].astype(str).str[:6].map(nome_map)
            else:
                stats_mun['NO_MUNICIPIO'] = stats_mun['CO_MUNICIPIO']
            
            # Ordenar por total de equipes (top 15 com mais equipes)
            stats_mun = stats_mun.nlargest(min(15, len(stats_mun)), 'TOTAL')
            
            y_pos = np.arange(len(stats_mun))
            
            # Barras empilhadas horizontais
            bars_conf = ax2.barh(y_pos, stats_mun['CONFORMES'], color='#27ae60', 
                                  label='Conformes', alpha=0.85)
            bars_nconf = ax2.barh(y_pos, stats_mun['NAO_CONFORMES'], left=stats_mun['CONFORMES'],
                                   color='#e74c3c', label='Não Conformes', alpha=0.7)
            
            # Labels de municípios
            labels_mun = stats_mun['NO_MUNICIPIO'].fillna(stats_mun['CO_MUNICIPIO']).tolist()
            labels_mun = [l[:20] + '...' if len(str(l)) > 23 else str(l) for l in labels_mun]
            
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(labels_mun, fontsize=9)
            ax2.invert_yaxis()
            ax2.set_xlabel('Número de Equipes')
            ax2.legend(loc='lower right', fontsize=9)
            
            # Anotações
            for i, (_, row) in enumerate(stats_mun.iterrows()):
                ax2.text(row['TOTAL'] + 0.3, i, 
                        f"{int(row['TOTAL'])} eq. ({row['TAXA_%']:.2f}% conf.)", 
                        va='center', fontsize=9, fontweight='bold')
            
            ax2.grid(True, alpha=0.3, axis='x')
            ax2.set_xlim(0, stats_mun['TOTAL'].max() * 1.35)
        else:
            ax2.text(0.5, 0.5, 'Sem dados de conformidade', ha='center', va='center', fontsize=14)
        
        plt.tight_layout()
        
        # Salvar
        output_file = os.path.join(pasta_uf, f'{uf}_equipes_conformidade.png')
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        # Salvar CSV com dados de conformidade do estado
        df_uf_conf.to_csv(os.path.join(pasta_uf, f'{uf}_conformidade.csv'), sep=';', index=False)
        df_uf_mun.to_csv(os.path.join(pasta_uf, f'{uf}_dados_municipios.csv'), sep=';', index=False)
        
        print(f"    {uf}: {total_municipios_uf} mun., {total_equipes_uf} eq., {taxa_conf_uf:.2f}% conf. → {pasta_uf}/")
    
    # =========================================================================
    # ETAPA 5: GERAR RESUMO CONSOLIDADO
    # =========================================================================
    
    print("\n[5] Gerando resumo consolidado...")
    
    # Resumo por estado incluindo conformidade
    resumo_estados = []
    for uf in ufs_ordenadas:
        df_uf_mun = df_por_mun[df_por_mun['UF'] == uf]
        df_uf_conf = df_conformidade[df_conformidade['UF'] == uf]
        
        total_eq = df_uf_mun['N_EQUIPES'].sum()
        total_mun = len(df_uf_mun)
        total_conf = df_uf_conf['CONFORME'].sum() if len(df_uf_conf) > 0 else 0
        taxa_conf = 100 * total_conf / len(df_uf_conf) if len(df_uf_conf) > 0 else 0
        
        resumo_estados.append({
            'UF': uf,
            'NOME_ESTADO': NOME_UF.get(uf, uf),
            'REGIAO': UF_REGIAO.get(uf, ''),
            'TOTAL_EQUIPES': total_eq,
            'MUNICIPIOS_COM_AD': total_mun,
            'MUNICIPIOS_TOTAL': MUNICIPIOS_POR_UF.get(uf, 0),
            'COBERTURA_%': (100 * total_mun / MUNICIPIOS_POR_UF.get(uf, 1)),
            'EQUIPES_CONFORMES': total_conf,
            'TAXA_CONFORMIDADE_%': taxa_conf
        })
    
    df_resumo = pd.DataFrame(resumo_estados)
    df_resumo = df_resumo.sort_values('TOTAL_EQUIPES', ascending=False)
    df_resumo['COBERTURA_%'] = df_resumo['COBERTURA_%'].round(2)
    df_resumo['TAXA_CONFORMIDADE_%'] = df_resumo['TAXA_CONFORMIDADE_%'].round(2)
    df_resumo.to_csv(os.path.join(OUTPUT_ESTADOS_DIR, 'resumo_por_estado_v2.csv'), sep=';', index=False)
    
    print(f"    Resumo salvo em: {OUTPUT_ESTADOS_DIR}/resumo_por_estado_v2.csv")
    
    # =========================================================================
    # RESUMO FINAL
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("CONCLUÍDO!")
    print("=" * 80)
    
    print(f"""
    RESUMO NACIONAL:
    Equipes conformes: {equipes_conformes:,} de {total_equipes:,} ({taxa_conformidade_equipes:.2f}%)
    Municípios cobertos: {municipios_com_ad:,} de {total_municipios_brasil:,} ({taxa_cobertura_municipal:.2f}%)
    
    Visualizações geradas para {len(ufs_ordenadas)} estados.
    
    Arquivos em:
      Nacional: {OUTPUT_NACIONAL_DIR}/
      Estados:  {OUTPUT_ESTADOS_DIR}/[UF]/
    """)


if __name__ == '__main__':
    main()
