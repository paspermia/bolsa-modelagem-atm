# Seu código MAE corrigido sem formatação de dataframe

import pandas as pd
import warnings
import xarray as xr
import glob
import os

warnings.filterwarnings('ignore')

caminho_csv = "dados_A840_H_2023-09-01_2023-09-06.csv"

# 1. Leitura e limpeza do arquivo INMET
df_inmet = pd.read_csv(caminho_csv, sep=';', skiprows=10, encoding='latin1', decimal='.')
df_inmet.columns = df_inmet.columns.str.strip().str.upper()

col_data = [c for c in df_inmet.columns if 'DATA' in c][0]
col_hora = [c for c in df_inmet.columns if 'HORA' in c][0]
col_chuva = [c for c in df_inmet.columns if 'PRECIPITA' in c][0]

df_inmet['Hora_Limpa'] = df_inmet[col_hora].astype(str).str.replace('.0', '', regex=False).str.zfill(4)
df_inmet['Hora_Limpa'] = df_inmet['Hora_Limpa'].str.slice(0, 2) + ':00:00'
df_inmet['Datetime'] = pd.to_datetime(df_inmet[col_data] + ' ' + df_inmet['Hora_Limpa'], format='mixed')

# 2. Recortar a Janela de 24h (03/09 às 12:00 até 04/09 às 12:00)
mask = (df_inmet['Datetime'] > '2023-09-03 12:00:00') & (df_inmet['Datetime'] <= '2023-09-04 12:00:00')
df_merge_mae = df_inmet.loc[mask].copy()

df_merge_mae = df_merge_mae[['Datetime', col_chuva]].rename(columns={col_chuva: 'INMET_1h'})
df_merge_mae.reset_index(drop=True, inplace=True)

# 3. Extrair os valores horários do MERGE diretamente (sem lista manual)
pasta_merge = r"C:\Users\yasmi\Documents\Modelagem_RS" # Seu caminho correto
arquivos_grib = sorted(glob.glob(os.path.join(pasta_merge, "*.grib2")))

lat_bento = -29.16
lon_bento = -51.53

merge_1h = []
print("Carregando valores do MERGE para cálculo...")

for caminho in arquivos_grib:
    try:
        ds = xr.open_dataset(caminho, engine="cfgrib")
        nome_lat = "latitude" if "latitude" in ds.coords else "lat"
        nome_lon = "longitude" if "longitude" in ds.coords else "lon"
        
        ds = ds.assign_coords({nome_lon: (((ds[nome_lon] + 180) % 360) - 180)})
        var_precip = [v for v in ds.data_vars if "prec" in v.lower()][0]
        
        ponto = ds[var_precip].interp({nome_lat: lat_bento, nome_lon: lon_bento}, method="linear")
        valor = float(ponto.values.item())
        merge_1h.append(round(valor if valor == valor else 0.0, 2))
        ds.close()
    except Exception as e:
        print(f"Erro no arquivo {os.path.basename(caminho)}: {e}")
        merge_1h.append(0.0)

# Garantir que a lista tenha 24 itens (preenchendo com zero se faltar algum arquivo)
while len(merge_1h) < 24:
    merge_1h.append(0.0)

# Se extrair a mais (caso haja arquivos extras na pasta), corta nos 24
merge_1h = merge_1h[:24]

# 4. Inserir no DataFrame e Calcular o Erro Absoluto
df_merge_mae['MERGE_1h'] = merge_1h
df_merge_mae['Erro_Absoluto'] = abs(df_merge_mae['MERGE_1h'] - df_merge_mae['INMET_1h'])
mae_final = df_merge_mae['Erro_Absoluto'].mean()

print("\n--- Comparação (Hora a Hora) em Bento Gonçalves ---")
print(df_merge_mae.to_string(index=False)) # Imprime a tabela limpa
print(f"\nO Erro Médio Absoluto (MAE) do MERGE é: {mae_final:.2f} mm/1h")