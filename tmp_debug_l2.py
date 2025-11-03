import polars as pl
from etl.mappers import canonicalize_l1
from etl.l2_clean import prepare_l2

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
    'yards_gained':[4.0,6.0,12.0],
    'touchdown':[0,0,0],
    'interception':[0,0,1],
    'fumble_lost':[0,0,0],
    'play_description':[
        'Run for four yards.',
        'Run for six yards.',
        'Pass intercepted by defender.',
    ],
})

canon = canonicalize_l1(l1,2025,1)
prep = prepare_l2(canon,2025,1)
print(prep.to_dicts())
