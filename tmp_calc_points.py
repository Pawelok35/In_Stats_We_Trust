import polars as pl
from etl.l3_aggregate import _aggregate

data = {
    'season': [2025]*6,
    'week': [8]*6,
    'game_id': ['G1']*6,
    'play_id': [1,2,3,4,5,6],
    'TEAM': ['BAL','BAL','BAL','MIA','MIA','MIA'],
    'OPP': ['MIA','MIA','MIA','BAL','BAL','BAL'],
    'drive': [1,1,2,1,1,2],
    'play_type': ['pass','run','interception','field_goal','pass','extra_point'],
    'epa': [-0.6,0.3,-2.0,0.8,-0.5,0.4],
    'success': [0.0,1.0,0.0,1.0,0.0,1.0],
    'yards_gained': [-7.0,4.0,-5.0,25.0,-3.0,10.0],
    'success_bin': [0,1,0,1,0,1],
    'is_turnover': [0,0,1,0,0,0],
    'is_offensive_td': [1,0,0,0,1,0],
    'play_description': [
        'Pass short left to WR for 10 yards, TOUCHDOWN.',
        'Run up the middle for 4 yards.',
        'Pass intercepted by defender, tackled.',
        'Field goal is GOOD.',
        'Pass to WR for 15 yards, TOUCHDOWN.',
        'extra point is GOOD.',
    ],
}

df = pl.DataFrame(data)
result = _aggregate(df)
subset = result.select(['TEAM','points_per_drive_off','points_per_drive_def','points_per_drive_diff']).to_dicts()
print(subset)
