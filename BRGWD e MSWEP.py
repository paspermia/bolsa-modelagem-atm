import pandas as pd
import warnings
warnings.filterwarnings('ignore')

caminho_csv = "dados_A840_H_2023-09-01_2023-09-06.csv"

# 1. Leitura e limpeza do INMET
df_inmet = pd.read_csv(caminho_csv, sep=';', skiprows=10, encoding='latin1', decimal='.')
df_inmet.columns = df_inmet.columns.str.strip().str.upper()

col_data = [c for c in df_inmet.columns if 'DATA' in c][0]
col_hora = [c for c in df_inmet.columns if 'HORA' in c][0]
col_chuva = [c for c in df_inmet.columns if 'PRECIPITA' in c][0]

df_inmet['Hora_Limpa'] = df_inmet[col_hora].astype(str).str.replace('.0', '', regex=False).str.zfill(4)
df_inmet['Hora_Limpa'] = df_inmet['Hora_Limpa'].str.slice(0, 2) + ':00:00'
df_inmet['Datetime'] = pd.to_datetime(df_inmet[col_data] + ' ' + df_inmet['Hora_Limpa'], format='mixed')
df_inmet.set_index('Datetime', inplace=True)

# 2. Acumulado diário do INMET na janela específica do BR-DWGD (10h às 10h UTC)
mask_diario = (df_inmet.index > '2023-09-03 10:00:00') & (df_inmet.index <= '2023-09-04 10:00:00')
inmet_diario = df_inmet.loc[mask_diario, col_chuva].sum()

# 3. Valor extraído do BR-DWGD para Bento Gonçalves (substitua pelo valor interpolado obtido no seu script do Xavier)
br_dwgd_diario = 95.74 

# 4. Cálculo do Erro Absoluto
erro_br = abs(br_dwgd_diario - inmet_diario)

print(f"Acumulado INMET (10h-10h UTC): {inmet_diario:.2f} mm")
print(f"Acumulado BR-DWGD: {br_dwgd_diario:.2f} mm")
print(f"Erro Absoluto (MAE do BR-DWGD): {erro_br:.2f} mm")