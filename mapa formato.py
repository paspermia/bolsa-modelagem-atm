import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import xarray as xr
import warnings
import copy

try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False

warnings.filterwarnings('ignore')

# 1. DADOS DE ENTRADA (Janela de 24h: 03/09 12 UTC a 04/09 12 UTC)
dados = {
    'Estacao': ['Bento Gonçalves', 'Caxias do Sul', 'Santa Maria'],
    'Lat': [-29.16, -29.16, -29.70],
    'Lon': [-51.53, -51.18, -53.70],
    'INMET_mm': [74.40, 76.20, 85.80],
    'MSWEP_mm': [70.55, 87.18, 105.09],
}

df_mapa = pd.DataFrame(dados)
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
    var_nomes = [v for v in ds_relevo.data_vars if any(t in v.lower() for t in ['alt', 'elev', 'z', 'topo'])]
    nome_var = var_nomes[0] if var_nomes else list(ds_relevo.data_vars)[0]
    
    da_relevo = ds_relevo[nome_var].sortby(
        'latitude' if 'latitude' in ds_relevo[nome_var].coords else 'lat'
    ).sortby(
        'longitude' if 'longitude' in ds_relevo[nome_var].coords else 'lon'
    )
    
    lat_coord = 'latitude' if 'latitude' in da_relevo.coords else 'lat'
    lon_coord = 'longitude' if 'longitude' in da_relevo.coords else 'lon'

    relevo_rs = da_relevo.sel(
        {lat_coord: slice(-34.0, -27.0), lon_coord: slice(-58.0, -49.0)}
    ).clip(min=0)
    TEM_RELEVO = True
except Exception as e:
    print(f'Aviso: Não foi possível processar o relevo ({e}). Plotando sem ele.')

# 4. CONFIGURAÇÃO DA FIGURA (Alta Resolução para LaTeX)
fig, ax = plt.subplots(figsize=(10, 8), dpi=300)

# Camada 1: Relevo com transparência
if TEM_RELEVO and relevo_rs is not None:
    cmap_terrain = copy.copy(plt.get_cmap('terrain'))
    cmap_terrain.set_bad(color='white')
    relevo_plot = relevo_rs.plot.imshow(
        ax=ax, cmap=cmap_terrain, vmin=0, vmax=1400, add_colorbar=False, alpha=0.35, zorder=1
    )

# Camada 2: Contorno do RS refinado
rs_mapa.boundary.plot(ax=ax, color='#333333', linewidth=0.8, zorder=2)

# Camada 3: Marcadores das Estações com paleta divergente
limite_erro = max(df_mapa['Diferenca'].abs().max(), 10.0)
norma_cores = colors.TwoSlopeNorm(vcenter=0.0, vmin=-limite_erro, vmax=limite_erro)

# O tamanho da bolha reflete a precipitação real do INMET; a cor reflete a diferença
sc = ax.scatter(
    df_mapa['Lon'], df_mapa['Lat'],
    s=df_mapa['INMET_mm'] * 3.5, 
    c=df_mapa['Diferenca'],
    cmap='RdBu', # Vermelho (Subestimado) / Azul (Superestimado)
    norm=norma_cores,
    edgecolors='white', # Borda branca destaca os pontos contra o terreno
    linewidths=1.2,
    zorder=3
)

# 5. AJUSTES ESTÉTICOS E EIXOS
cbar_chuva = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.04)
cbar_chuva.set_label('Viés do MSWEP (mm): Positivo=Superestimou | Negativo=Subestimou', fontsize=10, fontweight='bold')

# Rótulos limpos com ajuste de colisão manual
for idx, row in df_mapa.iterrows():
    # Deslocamento padrão
    offset_x = 0.05
    offset_y = 0.05
    
    # Ajuste específico para separar estações muito próximas
    if row['Estacao'] == 'Caxias do Sul':
        offset_y = -0.15 # Empurra o texto para baixo
    elif row['Estacao'] == 'Bento Gonçalves':
        offset_y = 0.12  # Empurra o texto para cima
        offset_x = -0.10 # Puxa um pouco para a esquerda
        
    ax.text(
        row['Lon'] + offset_x, row['Lat'] + offset_y,
        f"{row['Estacao']}\n{row['Diferenca']:+.1f} mm",
        fontsize=8, weight='bold', color='#1a1a1a', zorder=4,
        bbox=dict(facecolor='white', alpha=0.85, edgecolor='none', boxstyle='round,pad=0.2')
    )

# Formatação limpa de título e remoção das bordas grossas
ax.set_title('Desempenho do Modelo MSWEP vs Estações INMET\nAcumulado 24h (Setembro 2023)', 
             fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Longitude', fontsize=10)
ax.set_ylabel('Latitude', fontsize=10)
ax.grid(color='grey', linestyle=':', linewidth=0.5, alpha=0.5, zorder=0)

plt.savefig('mapa_mswep_inmet_publicacao.png', dpi=300, bbox_inches='tight', transparent=False)
plt.show()