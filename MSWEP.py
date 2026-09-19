import glob
import os
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

# 1. Diretório onde estão os arquivos baixados pelo rclone
pasta_mswep = r"C:\Users\yasmi\Downloads\dados_mswep"

# 2. Defina as estações e suas coordenadas (INMET)
# Adicione ou ajuste as coordenadas conforme as suas estações analisadas:
estacoes = {
    "Bento Gonçalves": {"lat": -29.16, "lon": -51.53},
    "Caxias do Sul": {"lat": -29.16, "lon": -51.18},
    "Santa Maria": {"lat": -29.70, "lon": -53.70},
}

# 3. Lista exata dos 8 arquivos que formam a janela de 12 UTC (03/09) até 12 UTC (04/09)
arquivos_janela = [
    # Dia 03/09 (Juliano 246)
    "2023246.15.nc",
    "2023246.18.nc",
    "2023246.21.nc",
    # Dia 04/09 (Juliano 247)
    "2023247.00.nc",
    "2023247.03.nc",
    "2023247.06.nc",
    "2023247.09.nc",
    "2023247.12.nc",
]

resultados = {nome: 0.0 for nome in estacoes}

# 4. Extração arquivo por arquivo com interpolação bilinear
print("Processando os arquivos do MSWEP...")

for nome_arq in arquivos_janela:
    caminho = os.path.join(pasta_mswep, nome_arq)

    if not os.path.exists(caminho):
        print(f"Atenção: Arquivo {nome_arq} não encontrado.")
        continue

    with xr.open_dataset(caminho) as ds:
        # Padronização dos nomes das coordenadas
        nome_lat = "lat" if "lat" in ds.coords else "latitude"
        nome_lon = "lon" if "lon" in ds.coords else "longitude"

        # Identifica o nome da variável de precipitação (geralmente 'precipitation')
        var_precip = [v for v in ds.data_vars if "precip" in v.lower()][0]

        for estacao, coords in estacoes.items():
            # Interpolação bilinear nos pontos exatos das estações
            ponto_interpolado = ds[var_precip].interp(
                {nome_lat: coords["lat"], nome_lon: coords["lon"]},
                method="linear",
            )
            valor_chuva = float(ponto_interpolado.values.item())
            resultados[estacao] += valor_chuva

# 5. Organização dos resultados em DataFrame
df_mswep = pd.DataFrame(
    [
        {
            "Estacao": estacao,
            "Lat": coords["lat"],
            "Lon": coords["lon"],
            "Chuva_MSWEP_24h": round(resultados[estacao], 2),
        }
        for estacao, coords in estacoes.items()
    ]
)

print("\n--- Acumulado MSWEP (03/09 12 UTC a 04/09 12 UTC) ---")
print(df_mswep)


plt.savefig("mapa_diferenca_mswep.png", dpi=300, bbox_inches='tight')
