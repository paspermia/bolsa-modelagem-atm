import pandas as pd
import glob
import os
from geopy.distance import great_circle
import re
import warnings # Para desligar avisos

# Desliga avisos de "engine='python'" que podem aparecer
warnings.filterwarnings('ignore', message="Falling back to the 'python' engine")

# Regras de leitura do arquivo do INMET
LINHAS_PARA_PULAR_DADOS = 10
COLUNA_TEMP = 'TEMPERATURA DO AR - BULBO SECO, HORARIA(°C)'
COLUNA_PREC = 'PRECIPITACAO TOTAL, HORARIO(mm)'
VALORES_NULOS = [-9999, '-9999', 'null']
CODIFICACAO = 'utf-8'

# O Alvo da Análise
VALE_TAQUARI_COORDS = (-29.4669, -51.9608) # (Latitude, Longitude)

# Função Auxiliar
def extrair_metadados(arquivo_csv):
    try:
        with open(arquivo_csv, 'r', encoding=CODIFICACAO) as f:
            lat, lon, nome = None, None, None
            for i, line in enumerate(f):
                if i > LINHAS_PARA_PULAR_DADOS:
                    break

                numero_float = r"[-+]?\d*\.\d+|\d+"

# [-+]?\d*\.\d+ -> Procura por um número decimal
# | -> ou
# \d+ ->  Se o primeiro falhar, procura por um número inteiro


                if line.startswith("Nome:"):
                    nome = line.split(":", 1)[1].strip()
                elif line.startswith("Latitude:"):
                    match = re.search(numero_float, line)
                    if match:
                        lat = float(match.group(0))
                elif line.startswith("Longitude:"):
                    match = re.search(numero_float, line)
                    if match:
                        lon = float(match.group(0))

        if lat and lon and nome:
            return nome, lat, lon
        else:
            print(f"AVISO: Não foi possível ler Lat/Lon do arquivo {arquivo_csv}")
            return "Desconhecido", None, None

    except Exception as e:
        print(f"ERRO ao ler cabeçalho de {arquivo_csv}: {e}")
        return "Desconhecido", None, None

# Preparação da "Linha de Montagem"
# (Procura por arquivos CSV na MESMA pasta onde este script .py está)
padrao_arquivos = 'dados_*.csv'
lista_de_arquivos = glob.glob(padrao_arquivos)
resultados_completos = []

# Loop Principal
print(f"--- INICIANDO ANÁLISE COMPLETA (QC + Distância) ---")

if not lista_de_arquivos:
    print("ERRO: Nenhum arquivo 'dados_*.csv' foi encontrado.")
    print(f" Verifique se os 35 arquivos .csv estão na mesma pasta que este script.")
else:
    print(f"Encontrados {len(lista_de_arquivos)} arquivos para analisar.")
    print(f"Ponto de Referência (Vale do Taquari): Lajeado-RS {VALE_TAQUARI_COORDS}")
    print("-----------------------------------------------------------------")

    # Itera sobre cada arquivo encontrado
    for arquivo in lista_de_arquivos:
        nome_arquivo = os.path.basename(arquivo)
        nome_estacao, lat_estacao, lon_estacao = extrair_metadados(arquivo)

        distancia_km = None
        if lat_estacao and lon_estacao:
            ponto_estacao = (lat_estacao, lon_estacao)
            distancia_km = round(great_circle(VALE_TAQUARI_COORDS, ponto_estacao).kilometers, 2)

        try:
            df = pd.read_csv(
                arquivo, sep=';', skiprows=LINHAS_PARA_PULAR_DADOS,
                na_values=VALORES_NULOS, encoding=CODIFICACAO, engine='python'
            )

            # Garante que as colunas são numéricas
            if COLUNA_TEMP in df.columns:
                df[COLUNA_TEMP] = pd.to_numeric(df[COLUNA_TEMP], errors='coerce')
            if COLUNA_PREC in df.columns:
                df[COLUNA_PREC] = pd.to_numeric(df[COLUNA_PREC], errors='coerce')

            total_obs = len(df)
            perc_temp, perc_prec = 0, 0

            if total_obs > 0:
                if COLUNA_TEMP in df.columns:
                    validas_temp = df[COLUNA_TEMP].count()
                    perc_temp = (validas_temp / total_obs) * 100
                if COLUNA_PREC in df.columns:
                    validas_prec = df[COLUNA_PREC].count()
                    perc_prec = (validas_prec / total_obs) * 100

            # Guarda a "Ficha de Análise" na prancheta
            resultados_completos.append({
                'Arquivo': nome_arquivo,
                'Nome_Estacao': nome_estacao,
                'Latitude': lat_estacao,
                'Longitude': lon_estacao,
                'Distancia_km': distancia_km,
                'Perc_Temp': round(perc_temp, 2),
                'Perc_Prec': round(perc_prec, 2)
            })

        except Exception as e:
            print(f" ERRO GERAL ao processar QC do arquivo {arquivo}: {e}")

# Análise dos Resultados
print("-----------------------------------------------------------------")
print("\nRESULTADO FINAL DA ANÁLISE DE ESTAÇÕES:")

if not resultados_completos:
    print("Nenhuma estação foi processada com sucesso.")
else:
    df_completo = pd.DataFrame(resultados_completos)
    criterio_qc = (df_completo['Perc_Temp'] > 90) & (df_completo['Perc_Prec'] > 90)
    df_aprovadas = df_completo[criterio_qc].copy()
    df_rejeitadas = df_completo[~criterio_qc].copy()

    # O Relatório Final
    if not df_aprovadas.empty:
        print(f"\n {len(df_aprovadas)} Estações APROVADAS (QC > 90%):")

        df_aprovadas = df_aprovadas.sort_values(by='Distancia_km')

        # Imprime a tabela de aprovadas no terminal
        print(df_aprovadas[['Nome_Estacao', 'Distancia_km', 'Perc_Temp', 'Perc_Prec', 'Arquivo']])

        melhor_estacao = df_aprovadas.iloc[0]
        print("\n--- ESTAÇÃO SELECIONADA ---")
        print(f"Estação Aprovada Mais Próxima do Vale do Taquari é:")
        print(f"Nome: {melhor_estacao['Nome_Estacao']}")
        print(f"Arquivo: {melhor_estacao['Arquivo']}")
        print(f"Distância: {melhor_estacao['Distancia_km']} km")

    else:
        print("\nNenhuma estação foi APROVADA (> 90%).")

    if not df_rejeitadas.empty:
        print(f"\n {len(df_rejeitadas)} Estações REJEITADAS (QC < 90%):")

        print(df_rejeitadas[['Nome_Estacao', 'Distancia_km', 'Perc_Temp', 'Perc_Prec', 'Arquivo']])
    else:
        print("\nNenhuma estação foi REJEITADA.")

