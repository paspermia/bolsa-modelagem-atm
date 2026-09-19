import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import xarray as xr
import glob
import warnings
import copy

try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False

warnings.filterwarnings('ignore')

# 1. PROCESSAMENTO DOS DADOS DO INMET (Múltiplos CSVs)
arquivos = glob.glob("dados_*.csv")
lista_estacoes = []

for arquivo in arquivos:
    try:
        sigla_estacao = arquivo.split('_')[1] if '_' in arquivo else "S/C"
        meta = {'lat': None, 'lon': None, 'nome': 'Desconhecida'}
        with open(arquivo, 'r', encoding='latin1') as f:
            for _ in range(12):
                linha = next(f)
                if 'Nome:' in linha: meta['nome'] = linha.split(':')[1].strip()
                if 'Latitude:' in linha: meta['lat'] = float(linha.split(':')[1].replace(',', '.'))
                if 'Longitude:' in linha: meta['lon'] = float(linha.split(':')[1].replace(',', '.'))

        # Leitura da tabela a partir da linha 10
        df_temp = pd.read_csv(arquivo, sep=';', skiprows=10, encoding='latin1', decimal=',', engine='python')
        col_chuva = [c for c in df_temp.columns if 'PRECIPITACAO' in c]

        if col_chuva and meta['lat'] is not None:
            total_chuva = df_temp[col_chuva[0]].fillna(0).sum()
            lista_estacoes.append({
                'Sigla': sigla_estacao,
                'Nome': meta['nome'].split()[0].title(), # Guarda apenas o primeiro nome capitalizado
                'Latitude': meta['lat'],
                'Longitude': meta['lon'],
                'Chuva': total_chuva
            })
    except Exception as e:
        print(f"Erro no ficheiro {arquivo}: {e}")

df_estacoes = pd.DataFrame(lista_estacoes)

# 2. CARREGAMENTO DO CONTORNO DO RS
url_br = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
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
    print(f'Aviso: Não foi possível processar o relevo ({e}).')

# 4. CONFIGURAÇÃO DA FIGURA (Alta Resolução)
fig, ax = plt.subplots(figsize=(12, 10), dpi=300)

# Camada 1: Relevo com transparência
if TEM_RELEVO and relevo_rs is not None:
    cmap_terrain = copy.copy(plt.get_cmap('terrain'))
    cmap_terrain.set_bad(color='white')
    relevo_rs.plot.imshow(
        ax=ax, cmap=cmap_terrain, vmin=0, vmax=1400, add_colorbar=False, alpha=0.35, zorder=1
    )

# Camada 2: Contorno do RS
rs_mapa.boundary.plot(ax=ax, color='#333333', linewidth=0.8, zorder=2)

# Camada 3: Bolhas de Precipitação
if not df_estacoes.empty:
    sc = ax.scatter(
        df_estacoes['Longitude'],
        df_estacoes['Latitude'],
        s=df_estacoes['Chuva'] * 2.0 + 20, # Fator de tamanho suave
        c=df_estacoes['Chuva'],
        cmap='Blues', # Paleta ideal para volume de chuva
        edgecolors='black', # Borda preta separa bem as bolhas azuis sobrepostas
        linewidths=0.6,
        alpha=0.9,
        zorder=3,
        vmin=0,
        vmax=max(df_estacoes['Chuva'].max(), 100)
    )

    cbar_chuva = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.04)
    cbar_chuva.set_label('Precipitação Acumulada (mm)', fontsize=11, fontweight='bold')

    # 5. RÓTULOS (COM ORGANIZAÇÃO AUTOMÁTICA)
    textos = []
    for _, row in df_estacoes.iterrows():
        # Exibe o nome e a chuva. Ex: "Caxias\n120 mm"
        t = ax.text(
            row['Longitude'], row['Latitude'], 
            f"{row['Nome']}\n{row['Chuva']:.0f} mm",
            fontsize=7, weight='bold', color='#001449', zorder=4,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2')
        )
        textos.append(t)
        
    if HAS_ADJUST_TEXT:
        # A magia acontece aqui: afasta os textos uns dos outros automaticamente
        adjust_text(textos, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5), ax=ax)

# 6. ESTÉTICA FINAL
ax.set_title('Precipitação Acumulada INMET - Rio Grande do Sul\n(Evento: 01/09 a 06/09/2023)', 
             fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Longitude', fontsize=10)
ax.set_ylabel('Latitude', fontsize=10)
ax.grid(color='grey', linestyle=':', linewidth=0.5, alpha=0.5, zorder=0)

plt.savefig('mapa_total_inmet_publicacao.png', dpi=300, bbox_inches='tight', transparent=False)
plt.show()