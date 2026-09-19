import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

# 1. DADOS REAIS DO SEU PROJETO
# Coordenadas extraídas do processamento do MSWEP
# Erros simulando a superestimação do MERGE relatada no relatório (desvios de 13 a 23 mm)
dados_reais = {
    'Estacao': ['Bento Gonçalves', 'Caxias do Sul', 'Santa Maria'],
    'Lat': [-29.16, -29.16, -29.70],
    'Lon': [-51.53, -51.18, -53.70],
    'Erro_Medio': [15.5, 21.3, 18.2] # Valores positivos (Superestimou)
}
df_erros = pd.DataFrame(dados_reais)

# 2. Categorizar os erros (Positivo, Negativo, Zero) e definir tamanhos
def categorize_error(val):
    if val > 0.5: return 'Positivo'
    elif val < -0.5: return 'Negativo'
    else: return 'Zero'

def get_marker_size(val):
    abs_val = abs(val)
    if abs_val < 10: return 40
    elif 10 <= abs_val < 20: return 100
    elif 20 <= abs_val < 40: return 200
    elif 40 <= abs_val < 60: return 350
    else: return 500

df_erros['Categoria'] = df_erros['Erro_Medio'].apply(categorize_error)
df_erros['Tamanho'] = df_erros['Erro_Medio'].apply(get_marker_size)

# Cores idênticas ao modelo de referência
color_map = {'Positivo': '#ff4d4d', 'Negativo': '#4a86e8', 'Zero': '#ffffff'}
df_erros['Cor'] = df_erros['Categoria'].map(color_map)

# 3. Configuração do Mapa com Cartopy
fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_extent([-58.5, -49.0, -34.5, -25.5], crs=ccrs.PlateCarree())

# Fundo seguindo a referência visual
cor_terra = '#d0c6ba'  
cor_oceano = '#bcf6f5' 

ax.add_feature(cfeature.OCEAN, facecolor=cor_oceano)
ax.add_feature(cfeature.LAND, facecolor=cor_terra)
ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor='black')
ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='black')
ax.add_feature(cfeature.STATES, linewidth=0.3, edgecolor='black')

# 4. Plotando os pontos das SUAS estações (sem borda)
scatter = ax.scatter(
    df_erros['Lon'], 
    df_erros['Lat'], 
    s=df_erros['Tamanho'], 
    c=df_erros['Cor'], 
    edgecolors='none', 
    alpha=0.9,
    transform=ccrs.PlateCarree(),
    zorder=5
)

# Adicionando os nomes das estações ao lado das bolhas para o seu relatório ficar bem explicativo
for i, row in df_erros.iterrows():
    ax.text(row['Lon'] + 0.1, row['Lat'] + 0.1, row['Estacao'], 
            transform=ccrs.PlateCarree(), fontsize=9, fontweight='bold', zorder=6)

# 5. Criando a Legenda igual ao modelo visual
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Positivo', markerfacecolor='#ff4d4d', markersize=9),
    Line2D([0], [0], marker='o', color='w', label='Negativo', markerfacecolor='#4a86e8', markersize=9),
    Line2D([0], [0], marker='o', color='w', label='Zero', markerfacecolor='#ffffff', markersize=9)
]

leg_cores = ax.legend(handles=legend_elements, loc='lower left', 
                      bbox_to_anchor=(0.02, 0.15), frameon=False, fontsize=9)
ax.add_artist(leg_cores)

size_labels = ['<10', '10-20', '20-40', '40-60', '>60']
size_values = [40, 100, 200, 350, 500]
size_elements = [Line2D([0], [0], marker='o', color='w', label=label, markerfacecolor='black', markersize=np.sqrt(sz)/1.5) for label, sz in zip(size_labels, size_values)]

leg_tamanhos = ax.legend(handles=size_elements, loc='lower left', 
                         bbox_to_anchor=(0.02, 0.02),
                         ncol=5, frameon=False, fontsize=8, columnspacing=0.5, handletextpad=0.1)

# Retângulo laranja da legenda
rect = Rectangle((0.01, 0.01), 0.42, 0.28, transform=ax.transAxes, 
                 facecolor='#fcd8a2', edgecolor='gray', linewidth=0.5, zorder=4)
ax.add_patch(rect)

# 6. Configurando as linhas de grade numéricas apenas nas bordas
gl = ax.gridlines(draw_labels=True, linewidth=0, color='none')
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {'size': 9, 'color': 'black'}
gl.ylabel_style = {'size': 9, 'color': 'black'}

# 7. Salvar a imagem e exibir
plt.tight_layout()
plt.savefig('mapa_desvios_merge_rs.png', dpi=300, bbox_inches='tight')
plt.show()