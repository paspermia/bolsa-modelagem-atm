import xarray as xr
import pandas as pd

# Abre o arquivo do Xavier explicitando o motor que instalamos
ds = xr.open_dataset("pr_20010101_20240320_BR-DWGD_UFES_UTEXAS_v_3.2.3.nc", engine="netcdf4")

# COMENTE OU APAGUE essas duas linhas abaixo para o bug não travar seu código:
# print(ds) 
# print(ds.pr)

print("--- Arquivo carregado com sucesso na memória! Processando dados... ---")


# PASSO 2 - definir area de interesse (vale do taquari) e data

lat_vale_taquari = -29.4669
lon_vale_taquari = -51.9608
data = '2023-09-04'

latitude = lat_vale_taquari
longitude = lon_vale_taquari

# PASSO 3 - selecionar dados - com interpolaçao bilinear

net_chuva_bilinear = ds.pr.sel(time=data).interp(
    latitude=lat_vale_taquari, 
    longitude=lon_vale_taquari, 
    method='linear'
) 

valor_chuva = net_chuva_bilinear.values.item()

print(f'precipitação no vale do taquari em {data}: {valor_chuva} mm') 

# PASSO 4 - lista de estações do analise estacoes.py

lista_estacoes = [
    {"nome": "Bento Gonçalves", "lat": -29.1642, "lon": -51.5312},
    {"nome": "Caxias do Sul", "lat": -29.1764, "lon": -51.1767},
    {"nome": "Santa Maria", "lat": -29.7114, "lon": -53.7144}
] 

data_inicio = "2023-09-01"
data_fim = "2023-09-07"
 
print(f"extraindo dados (Padrão 10 UTC às 10 UTC)")
print("-" * 50) 

# PASSO 5 - loop de extração

todos_resultados = [] 

recorte_temporal = ds.pr.sel(time=slice(data_inicio, data_fim)) #fora do loop

for estacao in lista_estacoes:  

    serie_chuva = recorte_temporal.interp(
        latitude=estacao['lat'],
        longitude=estacao['lon'],
        method='linear' #troca pra interp bilinear
    ) 

    df_temp = serie_chuva.to_dataframe().reset_index() 
    df_temp['Estacao'] = estacao['nome'] 

    todos_resultados.append(df_temp) 

    print(f"dados extraídos para {estacao['nome']}.")
    print("-" * 50)

# PASSO 6 - juntar todos dataframes e salvar em csv (SEPARADO DO LOOP)

df_netcdf_final = pd.concat(todos_resultados) 
    
df_netcdf_final.to_csv("confronto_netcdf_setembro.csv", index=False)

print("\nO arquivo 'confronto_netcdf_setembro.csv' foi criado com todas as estações")

print(df_netcdf_final.head(10))

# PASSO 7 - lógica para ajuste da precipitação do INMET (10 UTC às 10 UTC) - corrigido

df_inmet = pd.read_csv('dados_A840_H_2023-09-01_2023-09-06.csv', sep=';', encoding='latin-1', skiprows=10) 
df_inmet.columns = df_inmet.columns.str.strip()

# Converte apenas a coluna de data 
df_inmet['data_ref_netcdf'] = pd.to_datetime(df_inmet['Data Medicao'], format='%Y-%m-%d') 

#Se a hora for 0, 100, 500, 900 (até as 09:00), ela marca como verdadeiro
#Se a hora for 1000, 1500, 2300, ela marca como falso
horas_madrugada = df_inmet['Hora Medicao'] < 1000

# Se a hora for menor que 10:00, subtrai um dia da data de referência 
df_inmet.loc[horas_madrugada, 'data_ref_netcdf'] -= pd.Timedelta(days=1)

# Transforma em formato de data pura para o agrupamento
df_inmet['data_ref_netcdf'] = df_inmet['data_ref_netcdf'].dt.date

# Agrupamento e soma
col_chuva = 'PRECIPITACAO TOTAL, HORARIO(mm)' 
chuva_diaria = df_inmet.groupby('data_ref_netcdf')[col_chuva].sum().reset_index()

# PASSO 8 - verificar tudo 

data_teste = pd.to_datetime('2023-09-04').date()
resultado_filtrado = chuva_diaria[chuva_diaria['data_ref_netcdf'] == data_teste]

print(f"\nResultado da chuva acumulada (INMET) para o dia de referência {data_teste}:")
print(resultado_filtrado)

print("\nComparando com os primeiros dados do NetCDF salvos:")
print(df_netcdf_final.head())