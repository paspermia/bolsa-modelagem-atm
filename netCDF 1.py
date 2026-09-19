# PASSO 1 - abrir netCDF

import xarray as xr

ds = xr.open_dataset("pr_20010101_20240320_BR-DWGD_UFES_UTEXAS_v_3.2.3.nc")

print(ds) #mostra tabela

print(ds.pr) #mostra variavel pr - precipitação

# PASSO 2 - definir area de interesse (vale do taquari) e data
# (-29.4669, -51.9608) (lat, lon) -> analise estacoes.py

lat_vale_taquari = -29.4669
lon_vale_taquari = -51.9608
data = '2023-09-04'

latitude = lat_vale_taquari
longitude = lon_vale_taquari

# PASSO 3 - selecionar dados 

net_chuva = ds.pr.sel(time = data, latitude = lat_vale_taquari, longitude = lon_vale_taquari, method ='nearest') # method='nearest' - pega o ponto mais perto das coord

valor_chuva = net_chuva.values.item() # .values.item() - pega o valor numerico

print(f'precipitação no vale do taquari em {data}: {valor_chuva} mm') 

# PASSO 4 - lista de estações do analise estacoes.py

import pandas as pd

lista_estacoes = [
    {"nome": "Bento Gonçalves", "lat": -29.1642, "lon": -51.5312},
    {"nome": "Caxias do Sul", "lat": -29.1764, "lon": -51.1767},
    {"nome": "Santa Maria", "lat": -29.7114, "lon": -53.7144}
] 

# periodo de inundação
data_inicio = "2023-09-01"
data_fim = "2023-09-07"
 
print(f"extraindo dados (Padrão 10 UTC às 10 UTC)")
print("-" * 50) #separador

# PASSO 5 - loop de extração

todos_resultados = [] #lista para guardar resultados

for estacao in lista_estacoes: 
    recorte_temporal = ds.pr.sel(time=slice(data_inicio, data_fim)) #seleciona intervalo de tempo

# nao se pode usar slice e latitude/longitude juntos

    serie_chuva = recorte_temporal.sel(
        latitude=estacao['lat'],
        longitude=estacao['lon'],
        method='nearest'
    ) #seleciona ponto mais próximo das coordenadas da estação

    #transforma em dataframe e adiciona coluna com nome da estação
    df_temp = serie_chuva.to_dataframe().reset_index() #reset_index() - transforma index em coluna normal
    df_temp['Estacao'] = estacao['nome'] #adiciona coluna com nome da estação

    todos_resultados.append(df_temp) #adiciona dataframe na lista

    print(f"dados extraídos para {estacao['nome']}.")
    print("-" * 50)

# PASSO 6 - juntar todos dataframes e salvar em csv (SEPARADO DO LOOP)

df_netcdf_final = pd.concat(todos_resultados) #junta todos dataframes da lista
    
df_netcdf_final.to_csv("confronto_netcdf_setembro.csv", index=False) #salva em csv sem index
# index é a numeração das linhas, se não quiser salvar, index=False

print("\nO arquivo 'confronto_netcdf_setembro.csv' foi criado com todas as estações")

print(df_netcdf_final.head(10)) #head - mostra as primeiras linhas do dataframe

# PASSO 7 - lógica para ajuste da precipitação do INMET (10 UTC às 10 UTC)
# x > 10h = hoje 
# x < 10h = ontem 

df_inmet = pd.read_csv('dados_A840_H_2023-09-01_2023-09-06.csv', sep=';', encoding='latin-1', skiprows=10) 
# lê o arquivo
# sep=';' - separador ponto e vírgula
# encoding='latin-1' - codificação do arquivo

df_inmet.columns = df_inmet.columns.str.strip() # limpa espaços nos nomes

df_inmet['hora_str'] = df_inmet['Hora Medicao'].astype(str).str.zfill(4) # cria coluna datetime combinando data e hora
# zfill(4) - garante que a hora tenha 4 dígitos (ex: 900 vira 0900)
#astype(str) - transforma em string

df_inmet['datetime'] = pd.to_datetime(df_inmet['Data Medicao'] + ' ' + df_inmet['hora_str'], format='%Y-%m-%d %H%M')
# junta data e hora e transforma em datetime
# %Y - ano com 4 dígitos
# %m - mês com 2 dígitos
# %d - dia com 2 dígitos
# %H - hora com 2 dígitos
# %M - minutos com 2 dígitos

df_inmet['data_ref_netcdf'] = (df_inmet['datetime'] - pd.Timedelta(hours=10)).dt.date # cria coluna com data de referência do netCDF (10 UTC às 10 UTC)
# timedelta(hours=10) - subtrai 10 horas
# .dt.date - pega só a parte da data

col_chuva = 'PRECIPITACAO TOTAL, HORARIO(mm)' # nome da coluna de precipitação

chuva_diaria = df_inmet.groupby('data_ref_netcdf')[col_chuva].sum().reset_index()
#groupby - agrupa por data de referência
# sum() - soma os valores de precipitação por dia

print(chuva_diaria[chuva_diaria['data_ref_netcdf'] == pd.to_datetime('2023-09-04').date()])
# == - filtra para data específica

# 96,35 mm (NetCDF) − 75,00 mm (INMET) = 21,35 mm
# volume de chuva bem alto nos dois datasets, mas o NetCDF indicou mais chuva que o INMET