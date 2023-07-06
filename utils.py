"""Utility functions."""

import re, json, os, time
import datetime as dt
from IPython import display

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter


def labels_match(original_labels: list[str], compared_labels: list[str], 
    match_thresh: float = 0.5):
    """
    A simple tool for matching the artist and the song labels.
    
    Parameters:
        - original_labels: The list of the original labels: [artist, song].
        - compared_labels: The list of the compared labels: [artist, song].
        - match_thresh: The match threshold; 0.5 by default.
    
    Returns:
        A Boolean value; True if the labels match and False otherwise.
    """
    
    match_thresh = match_thresh - 1e-5
    
    # the labels
    artist_0, song_0 = original_labels[0], original_labels[1]
    artist_1, song_1 = compared_labels[0], compared_labels[1]
    
    # return False if the compared labels are null
    if artist_1 == 'NaN' or song_1 == 'NaN':
        return False
    
    # evaluate the artist labels:
    # process the labels
    artist_0 = re.sub(r'’', '\'', artist_0)
    artist_0 = re.split(r', | | ', artist_0.lower())
    artist_1 = re.sub(r'’', '\'', artist_1)
    artist_1 = re.split(r', | | ', artist_1.lower())
    # calculate the match coefficient (in both ways)
    coef_a_01 = 0
    for word in artist_0:
        if word in artist_1:
            coef_a_01 += 1
    coef_a_10 = 0
    for word in artist_1:
        if word in artist_0:
            coef_a_10 += 1
    coef_a = max(coef_a_01 / len(artist_0), coef_a_10 / len(artist_1))
    
    # evaluate the song labels:
    # process the labels
    song_0 = re.sub(r'’', '\'', song_0)
    song_0 = re.sub(r'!|\[|\]|\(|\)', '', song_0)
    song_0 = re.split(r', | | ', song_0.lower())
    song_1 = re.sub(r'’', '\'', song_1)
    song_1 = re.sub(r'!|\[|\]|\(|\)', '', song_1)
    song_1 = re.split(r', | | ', song_1.lower())
    # calculate the match coefficient (in both ways)
    coef_s_01 = 0
    for word in song_0:
        if word in song_1:
            coef_s_01 += 1
    coef_s_10 = 0
    for word in song_1:
        if word in song_0:
            coef_s_10 += 1
    coef_s = max(coef_s_01 / len(song_0), coef_s_10 / len(song_1))
    
    # compare the coefficients to the match threshold
    if coef_a >= match_thresh and coef_s >= match_thresh:
        return True
    else:
        return False


def spotify_audio_features(df: pd.DataFrame, 
    client_id: str, client_secret: str):
    """
    Collect the audio features and genres of selected tracks 
    using the Spotify API.
    
    Parameters:
        - df: The data frame with chosen songs.
        - client_id: The client ID for the authorization.
        - client_secret: The client secret credential for the authorization.

    Returns:
        A Boolean value; True if all the tracks were examined and False 
        otherwise (can raise possible exceptions).
        The function saves the results into the 
        `spotify_API_logs\spotify_audio_features_log.csv` file.
    """
    
    # the API parameters
    api_search = 'https://api.spotify.com/v1/search'
    api_features = 'https://api.spotify.com/v1/audio-features/'
    api_artists = 'https://api.spotify.com/v1/artists/'
    
    token_body = {'grant_type': 'client_credentials', 
        'client_id': client_id, 'client_secret': client_secret}
    token_header = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    # local function to update API authorization
    def auth_update(header_auth: dict):
        token_resp = requests.post('https://accounts.spotify.com/api/token', 
            data=token_body, headers=token_header)
        if token_resp.status_code != 200:
            raise Exception(f'Token exception: {token_resp.json()}')
        token = token_resp.json()
        header_auth['Authorization'] = f'Bearer {token["access_token"]}'
        return True
    
    # local function to save the batch data
    def save_batch(batch_list: list[dict], header_auth: dict):
        
        # get the tracks and the artists IDs for the matched songs
        batch_df = pd.DataFrame(batch_list)
        
        song_IDs = batch_df.query('match == 1').song_spot_id.tolist()
        song_IDs_str = ','.join(song_IDs)
        payload_feat = {'ids': f'{song_IDs_str}'}
        
        artist_IDs = batch_df.query('match == 1').artist_spot_id.tolist()
        artist_IDs_str = ','.join(artist_IDs)
        payload_artist = {'ids': f'{artist_IDs_str}'}
        
        # request for the audio features and the artists stats
        while True:
            spot_feat_resp = requests.get(api_features, 
                params=payload_feat, headers=header_auth)
            spot_artist_resp = requests.get(api_artists, 
                params=payload_artist, headers=header_auth)
            
            feat_sc = spot_feat_resp.status_code
            feat_json = spot_feat_resp.json()
            artist_sc = spot_artist_resp.status_code
            artist_json = spot_artist_resp.json()
            
            if feat_sc == 429:  # rate limit error
                raise Exception('Audio features rate limit exceeded: '
                    f'{feat_json}')
            elif artist_sc == 429:  # rate limit error
                raise Exception('Artists rate limit exceeded: '
                    f'{artist_json}')
            elif feat_sc == 401 or artist_sc == 401:  # expired token error
                auth_update(header_auth)
            elif feat_sc != 200:
                print(f'Audio features exception: {feat_json}')
                print('Trying to postpone the request for 5 seconds...')
                time.sleep(5)
            elif artist_sc != 200:
                print(f'Artists exception: {artist_json}')
                print('Trying to postpone the request for 5 seconds...')
                time.sleep(5)
            else:
                break
        
        # collect the song features and the artists genres
        spot_feat = feat_json['audio_features']
        for i, feat in enumerate(spot_feat):
            if feat is None:
                del spot_feat[i]
        features_df = pd.DataFrame(spot_feat)\
            .rename({'id': 'song_spot_id'}, axis=1)
        
        spot_artist = artist_json['artists']
        for i, artist in enumerate(spot_artist):
            if artist['genres'] is None:
                del spot_artist[i]
        genres_df = pd.DataFrame(spot_artist)[['id', 'genres']]\
            .rename({'id': 'artist_spot_id'}, axis=1)
        
        # merge the genres and the features with the original records
        batch_merged_df = batch_df.merge(genres_df, how='left', 
            on='artist_spot_id').merge(features_df, how='left', 
            on='song_spot_id')
        
        # remove duplicated merges; duplicates occur when a song was present 
        # in two (or more) consecutive years
        batch_merged_df.drop_duplicates(
            subset=['date', 'artist_orig', 'song_orig'], inplace=True
        )
        
        return batch_merged_df
    
    # get the API authorization
    header_auth = {'Authorization': ''}
    auth_update(header_auth)
    
    # declare the batches container and counters
    batch_list = []
    batch_size = 50
    
    batch_i = 0
    no_batches = (df.shape[0] // batch_size) + 1
    no_batches = no_batches if df.shape[0] % batch_size != 0 else no_batches-1
    
    hot_i = 0
    no_hot = df.shape[0]
    
    # collect the batches, examine matching and get the features and genres
    for date, df_y in df.groupby(level='date'):
        for _, hot in df_y.iterrows():
            
            hot_i += 1
            display.clear_output()
            display.display('requesting ' + str(date) + '; ' + 
                'matching ' + str(hot_i) + '/' + str(no_hot) + '; ' + 
                'batches collected: ' + str(batch_i) + '/' + str(no_batches))
            
            # grab the original labels and transform them for Spotify search
            artist_orig = hot['artist']
            song_orig = hot['song']
            
            artist_search = artist_orig.split(',')[0]\
                .replace('The', '')\
                .replace('.', '').strip()
            song_search = song_orig.replace('\'', '')
            
            # find the song
            payload_search = {
                'q': f'artist:{artist_search} track:{song_search}', 
                'type': 'track', 'market': 'US'
            }
            
            while True:
                spot_q_resp = requests.get(api_search, 
                    params=payload_search, headers=header_auth)
                spot_q_sc = spot_q_resp.status_code
                
                if spot_q_sc == 429:  # rate limit error
                    retry = dt.datetime.today() + dt.timedelta(
                        seconds=int(spot_q_resp.headers['retry-after'])
                    )
                    print('Search rate limit exceeded!\n' + 
                        f'Retry on: {retry.strftime("%d-%m-%Y, %H:%M:%S")}')
                    return False
                elif spot_q_sc == 401:  # expired token error
                    auth_update(header_auth)
                elif spot_q_sc != 200:
                    print(f'Search exception: {spot_q_resp.json()}')
                    print('Trying to postpone the request for 5 seconds...')
                    time.sleep(5)
                else:
                    break
            
            spot_q = spot_q_resp.json()['tracks']['items']
            
            if spot_q:
                for item in spot_q:
                    artist_spot = song_spot = 'NaN'
                    artist_spot_id = song_spot_id = 'NaN'
                    
                    if item['artists'] is not None:
                        artist_spot = item['artists'][0]['name']
                        artist_spot_id = item['artists'][0]['id']
                    song_spot = item['name']
                    song_spot_id = item['id']
                    
                    # check the labels compatibility
                    if labels_match([artist_orig, song_orig], 
                            [artist_spot, song_spot]):
                        matched = 1
                        break
                    else:
                        matched = 0
            else:
                artist_spot = song_spot = artist_spot_id = song_spot_id = 'NaN'
                matched = 0
            
            # update the batch container
            batch_list.append({
                'date': str(date), 
                'artist_orig': artist_orig, 
                'song_orig': song_orig, 
                'artist_spot': artist_spot, 
                'song_spot': song_spot, 
                'artist_spot_id': artist_spot_id, 
                'song_spot_id': song_spot_id, 
                'match': matched
            })
            
            # save the batch when it gets full
            if len(batch_list) == batch_size:
                batch_feat_df = save_batch(batch_list, header_auth)
                
                if batch_i == 0:
                    batch_feat_df.to_csv(
                        'spotify_API_logs/spotify_audio_features_log.csv', 
                        index=False, sep=';'
                    )
                else:
                    batch_feat_df.to_csv(
                        'spotify_API_logs/spotify_audio_features_log.csv', 
                        mode='a', header=False, index=False, sep=';'
                    )
                
                batch_i += 1
                batch_list[:] = []
    
    # save the remaining data
    if batch_list:
        batch_feat_df = save_batch(batch_list, header_auth)
        batch_feat_df.to_csv(
            'spotify_API_logs/spotify_audio_features_log.csv', 
            mode='a', header=False, index=False, sep=';'
        )

    display.clear_output()
    display.display('All the batches collected!')
    
    return True


def artist_stats(artist: str, hot_100: pd.DataFrame | None = None):
    """
    Collect the artist's statistics (based on the Billboard Hot 100 Ranking).
    
    Parameters:
        - artist: The name of the artist (as string).
        - hot_100: The original data frame of the Billboard Hot 100 Ranking; 
          None by default (if this case, the ranking is loaded from 
          the `billboard_data.json` file).
        
    Returns:
        A Boolean value if all the statistics were collected.
    """
    
    # load the data if not provided
    if hot_100 is None:
        hot_100 = pd.read_json('music_data_scraper/billboard_data.json')\
            .drop_duplicates()
    
    # prepare the artist's catalogue
    artist_cat = artist.replace(' ', '_') + '_stats'
    os.system(f'mkdir {artist_cat}')
    
    # grab the artist's songs (solo and in collaborations)
    solo_df = hot_100.query(f'artist == "{artist}"')\
        .assign(score=lambda x: 101 - x.pos)
    colab_df = hot_100[
        hot_100.artist.str.startswith(artist) & (hot_100.artist != artist)
    ].assign(score=lambda x: 101 - x.pos)
    
    # save the songs data into json files
    for df, songs_type in zip(
        [solo_df, colab_df], ['solo_songs', 'collab_songs']
    ):
        song_dict = {}
        for song, song_stats in df.groupby('song', sort=False):
            song_stats = song_stats.drop(columns=['song'])\
                .astype({'date': 'str'})
            song_dict[song] = song_stats.to_dict('records')
        
        with open(f'{artist_cat}/{songs_type}.json', 'w') as file:
            json.dump(song_dict, file, indent=4)
    
    # save the artist's basic statistics
    with open(f'{artist_cat}/{artist_cat}.txt', 'w') as file:
        file.write(f'{artist} basic statistics')
        
        stat = solo_df.song.nunique()
        file.write(f'\n\n\nNumber of solo songs: {stat}.')
        
        stat = colab_df.song.nunique()
        file.write('\nNumber of songs in collaboration (as leading artist): '
            f'{stat}.')
        
        stat = np.union1d(solo_df.date.values, colab_df.date.values).size
        file.write(f'\n\nNumber of weeks on the Billboard Chart: {stat}.')
        
        stat = solo_df.score.sum()
        file.write(f'\n\nThe total score based on solo songs only: {stat}.')
        
        stat = stat + colab_df.score.sum()
        file.write('\nThe total score including collaborations '
            f'(as leading artist): {stat}.')
        
        stat = solo_df.set_index('date').first('1D').sort_values('pos').iloc[0]
        file.write('\n\nThe very first song on the Billboard List: '
            f'\'{stat.song}\' (on {stat.name.date()} ranking, '
            f'pos: {stat.pos}).')  # includes solo songs only!
        
        stat = solo_df.set_index('date').last('1D').sort_values('pos').iloc[0]
        file.write('\nThe very last song on the Billboard List: '
            f'\'{stat.song}\' (on {stat.name.date()} ranking, '
            f'pos: {stat.pos}).')  # includes solo songs only!
        
        stat = solo_df.groupby('song')\
            .agg({'score': 'sum', 'wks_on_chart': 'max', 'peak_pos': 'min'})\
            .sort_values('score', ascending=False).iloc[0]
        file.write('\n\nThe most successful solo song: '
            f'\'{stat.name}\' (score: {stat.score}, weeks on Chart: '
            f'{stat.wks_on_chart}, peak position: {stat.peak_pos}).')
    
        stat = colab_df.groupby('song')\
            .agg({'artist': 'first', 'score': 'sum', 'wks_on_chart': 'max', 
                'peak_pos': 'min'})\
            .sort_values('score', ascending=False).iloc[0]
        file.write('\nThe most successful song in collaboration (as leading '
            f'artist): \'{stat.name}\' by \'{stat.artist}\' '
            f'(score: {stat.score}, weeks on Chart: {stat.wks_on_chart}, '
            f'peak position: {stat.peak_pos}).')
    
    # produce the score plot
    ax = solo_df.groupby('date').score.sum().cumsum()\
        .plot(lw=3, figsize=(10, 5))
        
    pd.concat([solo_df, colab_df]).sort_values('date')\
        .groupby('date').score.sum().cumsum()\
        .plot(xlabel='year', ylabel='score', lw=3, ax=ax)
    
    plt.xticks(rotation=0, ha='center')
    ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
    plt.title(r'$\bf{' + f'{artist}' + r'}$ score evolution')
    
    handles, _ = ax.get_legend_handles_labels()
    plt.legend(reversed(handles), 
        ['score including collaborations', 'solo score'])
    
    plt.tight_layout()
    
    # save the plot to a pdf file
    plt.gcf().savefig(f'{artist_cat}/{artist}_score.pdf')
    
    return True


def genres_popul(genres: list, genres_src: pd.Series, decades: bool = False):
    """
    Evaluate the popularity of chosen genres.
    
    Parameters:
        - genres: The list of genres to examine 
          (strings and/or lists of strings).
        - genres_src: The source of genres data (as Series).
        - decades: True for aggregating the results using decades; 
          False by default (yearly schedule).
    
    Returns:
        A pandas `DataFrame` object.
    """
    
    # remove empty genres and set the aggregation frequency
    genres_src = genres_src.loc[lambda x: x != '[]']
    freq = 'Y' if not decades else '10Y'
    
    # count the songs within years/decades
    if not decades:
        songs_no = genres_src.groupby(level=0).count()
    else:
        genres_src = genres_src.loc[lambda x: (x.index >= '1960') 
            & (x.index < '2020')]
        songs_no = genres_src.groupby(pd.Grouper(freq='10Y')).count()
    
    # local function for evaluating genre popularity
    def genre_popul(genre: str, /, freq: str):
        return genres_src.apply(lambda x: bool(re.search(genre, x)))\
            .groupby(pd.Grouper(freq=freq)).sum() / songs_no
    
    # evaluate popularities
    genres_agg = pd.DataFrame()
    
    for genre in genres:
        if isinstance(genre, str):
            genre_ = genre.replace(' ', '_')
            genres_agg[genre_] = genre_popul(genre, freq=freq)
        if isinstance(genre, list):
            genre_ = genre[0].replace(' ', '_')
            genres_agg[genre_] = genre_popul(r'|'.join(genre), freq=freq)
    
    # improve the labels for the decades aggregation
    if decades:
        genres_agg.index = np.vectorize(lambda x: x + 's')\
            (genres_agg.index.astype('str'))
        genres_agg.index.name = 'decade'
    
    return genres_agg
