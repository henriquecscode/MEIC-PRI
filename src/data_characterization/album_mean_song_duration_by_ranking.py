from sys import argv
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

filename = argv[1]

def aggr_func(data):
    return pd.Series({
        'mean_song_duration': data['track_duration (s)'].mean(),
        'ranking':  data['album_ranking'].iat[0]
    })


df = pd.read_csv(filename, sep=';')
album_data = df.groupby(['album', 'artist']).apply(aggr_func)
album_data_sort = album_data.sort_values('ranking')

x = album_data_sort['ranking']
y = album_data_sort['mean_song_duration'].apply(lambda x: x/60)
z = np.polyfit(x, y, 1)
p = np.poly1d(z)

plt.scatter(x, y)
plt.plot(x,p(x),"r--")
plt.title('Album mean song duration by ranking')
plt.xlabel('Ranking')
plt.ylabel('Album mean track duration (min)')

plt.savefig('analysis/album_mean_song_duration_by_ranking.svg')
