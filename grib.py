import xarray as xr

merge_arquivo = "MERGE_CPTEC_20230903.grib2" 

#abre o arquivo merge
ds_merge = xr.open_dataset(merge_arquivo, engine='cfgrib')

print(ds_merge)

#corrige longitude para o RS funcionar
ds_merge.coords['longitude'] = (ds_merge.coords['longitude'] + 180) % 360 - 180
ds_merge = ds_merge.sortby(ds_merge.longitude)

print(ds_merge)