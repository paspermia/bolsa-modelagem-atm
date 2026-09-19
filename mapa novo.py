import copy
import geopandas as gpd
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr

# Tenta importar o adjustText para evitar sobreposição de nomes
try:
  from adjustText import adjust_text

  HAS_ADJUST_TEXT = True
except ImportError:
  HAS_ADJUST_TEXT = False

# 1. DADOS DE ENTRADA (Janela de 24h: 03/09 12 UTC a 04/09 12 UTC)
dados = {
    'Estacao': ['Bento Gonçalves', 'Caxias do Sul', 'Santa Maria'],
    'Lat': [-29.16, -29.16, -29.70],
    'Lon': [-51.53, -51.18, -53.70],
    'INMET_mm': [74.40, 76.20, 85.80],  # Observado INMET
    'MSWEP_mm': [70.55, 87.18, 105.09],  # Calculado MSWEP
}

df_mapa = pd.DataFrame(dados)

# Cálculo da Diferença (MSWEP - INMET)
df_mapa['Diferenca'] = df_mapa['MSWEP_mm'] - df_mapa['INMET_mm']

# 2. CARREGAMENTO DO CONTORNO DO RS
url_br = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
brasil = gpd.read_file(url_br)
rs_mapa = brasil[brasil['sigla'] == 'RS']

# 3. CARREGAMENTO E CORTE DO RELEVO DO RS
caminho_relevo = 'relevo_rs.nc'
TEM_RELEVO = False
relevo_rs = None

try:
  ds_relevo = xr.open_dataset(caminho_relevo)

  # Pega o nome da variável como texto simples (STRING) para garantir um DataArray
  var_nomes = [
      v
      for v in ds_relevo.data_vars
      if any(t in v.lower() for t in ['alt', 'elev', 'z', 'topo'])
  ]
  nome_var = (
      var_nomes[0] if var_nomes else list(ds_relevo.data_vars)[0]
  )  # ex: 'z' ou 'elevation'

  da_relevo = ds_relevo[nome_var]  # <--- Retorna DataArray puro

  # Identifica coordenadas de latitude e longitude
  lat_coord = 'latitude' if 'latitude' in da_relevo.coords else 'lat'
  lon_coord = 'longitude' if 'longitude' in da_relevo.coords else 'lon'

  # Ordena coordenadas antes do corte
  da_relevo = da_relevo.sortby(lat_coord).sortby(lon_coord)

  # Recorta para a região do RS
  relevo_rs = da_relevo.sel(
      {lat_coord: slice(-34.0, -27.0), lon_coord: slice(-58.0, -49.0)}
  ).clip(min=0)

  TEM_RELEVO = True
except Exception as e:
  print(f'Aviso: Não foi possível processar o relevo ({e}). Plotando sem ele.')

# 4. CONFIGURAÇÃO DA FIGURA E PLOTAGEM
fig, ax = plt.subplots(figsize=(12, 10))

# Camada 1: Relevo suave ao fundo
if TEM_RELEVO and relevo_rs is not None:
  cmap_terrain = copy.copy(plt.get_cmap('terrain'))
  cmap_terrain.set_bad(color='none')
  relevo_plot = relevo_rs.plot.imshow(
      ax=ax, cmap=cmap_terrain, vmin=0, vmax=1400, add_colorbar=False, alpha=0.4
  )
  cbar_top = plt.colorbar(
      relevo_plot, ax=ax, orientation='horizontal', fraction=0.05, pad=0.08
  )
  cbar_top.set_label('Altitude do Relevo (metros)', fontsize=11)

# Camada 2: Contorno do estado do RS
rs_mapa.boundary.plot(ax=ax, color='black', linewidth=1.0, zorder=2)

# Camada 3: Marcadores com escala 'coolwarm' travada no ZERO
limite_erro = max(df_mapa['Diferenca'].abs().max(), 10.0)
norma_cores = colors.TwoSlopeNorm(
    vcenter=0.0, vmin=-limite_erro, vmax=limite_erro
)

sc = ax.scatter(
    df_mapa['Lon'],
    df_mapa['Lat'],
    c=df_mapa['Diferenca'],
    cmap='coolwarm',
    norm=norma_cores,
    s=200,
    edgecolors='black',
    linewidths=1.5,
    zorder=5,
)

# Barra de cores para a diferença de precipitação
cbar_chuva = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.04)
cbar_chuva.set_label(
    'Diferença de Precipitação: MSWEP - INMET (mm)',
    fontsize=12,
    fontweight='bold',
)

# Camada 4: Rótulos das estações e valores da diferença
textos = []
for idx, row in df_mapa.iterrows():
  t = ax.text(
      row['Lon'] + 0.05,
      row['Lat'] + 0.03,
      f"{row['Estacao']}\n({row['Diferenca']:+.1f} mm)",
      fontsize=10,
      weight='bold',
      zorder=6,
      bbox=dict(
          facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.3'
      ),
  )
  textos.append(t)

if HAS_ADJUST_TEXT:
  adjust_text(
      textos, arrowprops=dict(arrowstyle='->', color='black', lw=0.8), ax=ax
  )

ax.set_title(
    'Diferença de Precipitação Acumulada em 24h: MSWEP vs INMET\n(03/09 12h'
    ' UTC a 04/09 12h UTC)',
    fontsize=15,
    fontweight='bold',
    pad=15,
)
ax.set_axis_off()

plt.tight_layout()
plt.savefig('mapa_diferenca_mswep.png', dpi=300, bbox_inches='tight')
plt.show()
print('Mapa gerado e salvo com sucesso como mapa_diferenca_mswep.png!')