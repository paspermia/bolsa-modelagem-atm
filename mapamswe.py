import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import xarray as xr
import warnings

# Desliga avisos visuais no terminal
warnings.filterwarnings('ignore')

# 1. Estruturação dos dados e cálculo da diferença (MSWEP - INMET)
dados = {
    'Estacao': ['Bento Gonçalves', 'Caxias do Sul', 'Santa Maria'],
    'Lat': [-29.16, -29.16, -29.70],
    'Lon': [-51.53, -51.18, -53.70],
    'INMET_mm': [74.4, 76.2, 85.8],
    'MSWEP_mm': [70.55, 87.18, 105.09],
}
df_mapa = pd.DataFrame(dados)
df_mapa['Diferenca'] = df_mapa['MSWEP_mm'] - df_mapa['INMET_mm']

# 2. Carregamento do contorno do RS
url_br = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
brasil = gpd.read_file(url_br)
rs_mapa = brasil[brasil['sigla'] == 'RS']

# 3. Carregamento do relevo com a ordem correta do slice (do menor para o maior)
ds_relevo = xr.open_dataset("relevo_rs.nc")
lat_coord = 'latitude' if 'latitude' in ds_relevo.coords else 'lat'
lon_coord = 'longitude' if 'longitude' in ds_relevo.coords else 'lon'
var_alt = [v for v in ds_relevo.data_vars if 'alt' in v.lower() or 'elev' in v.lower()][0]

# Ajustado para slice(-34.0, -27.0) para garantir que encontre os dados numéricos
relevo_rs = ds_relevo[var_alt].sel(
    {lat_coord: slice(-34.0, -27.0), lon_coord: slice(-58.0, -49.0)}
).clip(min=0)

# 4. Configuração da figura
fig, ax = plt.subplots(figsize=(12, 10))

# Camada 1: Relevo suave
relevo_plot = relevo_rs.plot.imshow(
    ax=ax, cmap='terrain', vmin=0, vmax=1400, add_colorbar=False, alpha=0.4
)

# Camada 2: Contorno do RS
rs_mapa.boundary.plot(ax=ax, color='black', linewidth=1.0, zorder=2)

# Camada 3: Bolinhas com escala travada no zero e borda preta
limite_erro = max(df_mapa['Diferenca'].abs().max(), 1.0)
norma_cores = colors.TwoSlopeNorm(
    vcenter=0.0, vmin=-limite_erro, vmax=limite_erro
)

sc = ax.scatter(
    df_mapa['Lon'], df_mapa['Lat'],
    c=df_mapa['Diferenca'], cmap='coolwarm', norm=norma_cores,
    s=180, edgecolors='black', linewidths=1.5, zorder=3
)

# 5. Legendas e Rótulos
cbar_chuva = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.04)
cbar_chuva.set_label('Diferença de Precipitação: MSWEP - INMET (mm)', fontsize=12, fontweight='bold')

for idx, row in df_mapa.iterrows():
    ax.text(
        row['Lon'] + 0.05, row['Lat'] + 0.03,
        f"{row['Estacao']}\n({row['Diferenca']:+.1f} mm)",
        fontsize=10, weight='bold', zorder=4,
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='gray', boxstyle='round,pad=0.3')
    )

ax.set_title('Diferença de Precipitação (MSWEP - INMET)\nSetembro de 2023', fontsize=15, fontweight='bold', pad=15)
ax.set_axis_off()

# Salvar a imagem e exibir
plt.tight_layout()
plt.savefig("mapa_diferenca_mswep.png", dpi=300, bbox_inches='tight')
plt.show()


import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import xarray as xr
import warnings
import copy

warnings.filterwarnings('ignore')

# 1. CARREGAMENTO E RECORTE DO MAPA (FRONTEIRAS RS)
url_br = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
brasil = gpd.read_file(url_br)
rs_mapa = brasil[brasil['sigla'] == 'RS']

# 2. CARREGAMENTO DO RELEVO 
ds_relevo = xr.open_dataset('relevo_rs.nc')
lat_coord = 'latitude' if 'latitude' in ds_relevo.coords else 'lat'
lon_coord = 'longitude' if 'longitude' in ds_relevo.coords else 'lon'
var_alt = [v for v in ds_relevo.data_vars if 'alt' in v.lower() or 'elev' in v.lower()][0]

relevo_rs = ds_relevo[var_alt].sel(
    {lat_coord: slice(-34.0, -27.0), lon_coord: slice(-58.0, -49.0)}
).clip(min=0)

# 3. DADOS INMET vs BR-DWGD (Xavier)
# Insira aqui os dados REAIS da diferença (Xavier - INMET) que você tinha calculado antes
dados = {
    'Estacao': ['Bento Gonçalves', 'Caxias do Sul', 'Santa Maria'],
    'Lat': [-29.16, -29.16, -29.70],
    'Lon': [-51.53, -51.18, -53.70],
    'Diferenca': [-3.4, +11.0, +19.3] # Valores que aparecem na imagem de exemplo
}
df_mapa = pd.DataFrame(dados)

# 4. PLOTAGEM DO MAPA
fig, ax = plt.subplots(figsize=(12, 10))

cmap_terrain = copy.copy(plt.get_cmap('terrain'))
cmap_terrain.set_bad(color='none')

relevo_plot = relevo_rs.plot.imshow(
    ax=ax, cmap=cmap_terrain, vmin=0, vmax=1400, add_colorbar=False, alpha=0.4
)

rs_mapa.boundary.plot(ax=ax, color='black', linewidth=1.0, zorder=2)

limite_erro = max(df_mapa['Diferenca'].abs().max(), 1.0)
norma_cores = colors.TwoSlopeNorm(vcenter=0.0, vmin=-limite_erro, vmax=limite_erro)

sc = ax.scatter(
    df_mapa['Lon'], df_mapa['Lat'],
    c=df_mapa['Diferenca'], cmap='coolwarm', norm=norma_cores,
    s=180, edgecolors='black', linewidths=1.5, zorder=3
)

cbar_chuva = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.04)
cbar_chuva.set_label('Diferença de Precipitação: BR-DWGD - INMET (mm)', fontsize=12, fontweight='bold')

for idx, row in df_mapa.iterrows():
    ax.text(
        row['Lon'] + 0.05, row['Lat'] + 0.03,
        f"{row['Estacao']}\n({row['Diferenca']:+.1f} mm)",
        fontsize=10, weight='bold', zorder=4,
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='gray', boxstyle='round,pad=0.3')
    )

cbar_top = plt.colorbar(relevo_plot, ax=ax, orientation='horizontal', fraction=0.05, pad=0.08)
cbar_top.set_label('Altitude do Relevo (metros)', fontsize=11)

ax.set_title("Análise de Precipitação: BR-DWGD vs INMET\nSetembro de 2023", fontsize=16, fontweight='bold', pad=15)
ax.set_axis_off()

plt.tight_layout()
plt.savefig("mapa_diferenca_xavier.png", dpi=300, bbox_inches='tight')
plt.show()