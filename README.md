## The Music Project

In this project we investigate the most successful songs in the music industry over the last few decades.

### Description

Music is one of the most emotional and exciting form of art invented by human beings. This simple physical phenomenon, based on regular beats and frequencies co-existence, can make people laugh or cry, dance or relax. As Nietzsche once said, *'Without music, life would be a mistake.'*; to many of us, these words are more than true.

The times change, and so does the music. The development of technologies, the sociopolitical events occurring in the world or the new ways of expressing ourselves are only a few factors that contribute in the musical evolution. The methods of the data science allow us to study this evolution, contributing in better understanding of the history, but also in discovering current trends and moods.

Our research in this project involves the data on the most successful songs in the music industry. We get the latter ones using the [Billboard Hot 100 Ranking](https://www.billboard.com/charts/hot-100/), which reveals the best selling tracks (both physical and digital) on a weekly basis. The Billboard charts cover almost 65 years of the music history (the first ranking is dated on August 4, 1958), making it possible to compare whole musical generations.

To get the properties of the selected songs, we use the [Spotify Web API](https://developer.spotify.com/documentation/web-api) provided by the [Spotify Service](https://www.spotify.com). The Service is one of the leading providers of the music streaming nowadays, but is also supplies its users in various developers' tools for data querying and studying. In this research we will focus on the audio features and the genres of the songs, which can be easily obtained by the API.

### Tools and methods

The analysis discussed in this project has been conducted using the Python language (`ver. 3.11.2`) and split into the following Jupyter notebooks files:

* the <a href='0-data_collection.ipynb'>`0-data_collection.ipynb`</a> notebook, where we collect the music data and prepare it for further investigations,
* the <a href='1-billboard_analysis.ipynb'>`1-billboard_analysis.ipynb`</a> notebook, which contains the analysis of the Billboard Hot 100 data, and
* the <a href='2-audio_features_analysis.ipynb'>`2-audio_features_analysis.ipynb`</a> notebook, where one can find the study on the songs audio features and genres.

All the packages used within the research can be found in the <a href='requirements.txt'>`requirements.txt`</a> file, including the `scrapy` package for Billboard web scraping (see the <a href='0-data_collection.ipynb'>`0-data_collection.ipynb`</a> file for details). The data collected within the project has been stored in two catalogues, i.e., the <a href='music_data_scraper'>`music_data_scraper`</a> (for the Billboard data; the folder also contains all the necessary scraping files) and the <a href='spotify_API_logs'>`spotify_API_logs`</a> one, where the Spotify API data on the songs reside. Some of the results of the performed analysis can be also found in the <a href='Drake_stats'>`Drake_stats`</a> catalogue (includes the *Drake* statistics).

To work with the Spotify API, we can store the sensitive information in the <a href='spotify_credentials.json'>`spotify_credentials.json`</a> file (see the details in the <a href='0-data_collection.ipynb'>`0-data_collection.ipynb`</a> notebook). All the utility functions used within the research are defined in the <a href='utils.py'>`utils.py`</a> module.
