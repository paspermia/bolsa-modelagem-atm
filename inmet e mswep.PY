import os
import pandas as pd
import xarray as xr
import warnings

warnings.filterwarnings('ignore')

# 1. Configurações dos arquivos MSWEP
pasta_mswep = r"C:\Users\yasmi\Downloads\dados_mswep"
arquivos_janela = [
    "2023246.15.nc", "2023246.18.nc", "2023246.21.nc", "2023247.00.nc",
    "2023247.03.nc", "2023247.06.nc", "2023247.09.nc", "2023247.12.nc"
]
lat_bento, lon_bento = -29.16, -51.53

# Extração dos 8 valores de 3 em 3 horas do MSWEP
mswep_3h = []
for nome_arq in arquivos_janela:
    caminho = os.path.join(pasta_mswep, nome_arq)
    with xr.open_dataset(caminho) as ds:
        lat_coord = "lat" if "lat" in ds.coords else "latitude"
        lon_coord = "lon" if "lon" in ds.coords else "longitude"
        var_precip = [v for v in ds.data_vars if "precip" in v.lower()][0]
        ponto = ds[var_precip].interp({lat_coord: lat_bento, lon_coord: lon_bento}, method="linear")
        mswep_3h.append(float(ponto.values.item()))

# 2. Leitura e agrupamento do INMET de 3 em 3 horas
caminho_csv = "dados_A840_H_2023-09-01_2023-09-06.csv"
df_inmet = pd.read_csv(caminho_csv, sep=';', skiprows=10, encoding='latin1', decimal='.')
df_inmet.columns = df_inmet.columns.str.strip().str.upper()

col_data = [c for c in df_inmet.columns if 'DATA' in c][0]
col_hora = [c for c in df_inmet.columns if 'HORA' in c][0]
col_chuva = [c for c in df_inmet.columns if 'PRECIPITA' in c][0]

df_inmet['Hora_Limpa'] = df_inmet[col_hora].astype(str).str.replace('.0', '', regex=False).str.zfill(4)
df_inmet['Hora_Limpa'] = df_inmet['Hora_Limpa'].str.slice(0, 2) + ':00:00'
df_inmet['Datetime'] = pd.to_datetime(df_inmet[col_data] + ' ' + df_inmet['Hora_Limpa'], format='mixed')

mask = (df_inmet['Datetime'] > '2023-09-03 12:00:00') & (df_inmet['Datetime'] <= '2023-09-04 12:00:00')
df_evento = df_inmet.loc[mask].copy()
df_evento.set_index('Datetime', inplace=True)

df_3h = df_evento[col_chuva].resample('3h', closed='right', label='right').sum().reset_index()
df_3h.columns = ['Datetime', 'INMET_3h']
df_3h['MSWEP_3h'] = mswep_3h

# 3. Cálculo do Erro Absoluto e MAE
df_3h['Erro_Absoluto'] = abs(df_3h['MSWEP_3h'] - df_3h['INMET_3h'])
mae_mswep = df_3h['Erro_Absoluto'].mean()

print("\n--- Comparação MSWEP (3 em 3h) ---")
print(df_3h.round(2))
print(f"\nMAE do MSWEP: {mae_mswep:.2f} mm/3h")