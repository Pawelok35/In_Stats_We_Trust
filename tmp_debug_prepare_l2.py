import polars as pl
from etl.mappers import canonicalize_l1, prepare_l2

l1 = pl.DataFrame({
    'season':[2025,2025,2025],
    'week':[1,1,1],
    'game_id':['G1','G1','G1'],
    'play_id':[1,1,2],
    'posteam':['WAS','WAS','SD'],
    'defteam':['NYG','NYG','DEN'],
    'drive':[1,1,2],
    'play_type':['run','run','pass'],
    'epa':[0.1,0.1,0.2],
    'success':[1.0,1.0,None],
    'yardline_100':[75.0,75.0,68.0],
    'down':[1,1,2],
    'distance':[10,10,8],
})

c = canonicalize_l1(l1,2025,1)
print(c.columns)
print(c)
try:
    l2 = prepare_l2(c,2025,1)
    print(l2.columns)
except Exception as exc:
    import traceback
    traceback.print_exc()
