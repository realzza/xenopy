# birdData
BirdData is a python wrapper for [Xeno-canto API 2.0](https://xeno-canto.org/article/153). Enables user to download bird data with one command line. BirdData supports multithreading download.

## Environment
Download repo to local:
```
git clone git@github.com:realzza/birdData.git
```
Set up environment:
```python
pip install -r requirement.txt
```

## Download
### Single-thread
Download audio data for one bird species. Use ***scientific name*** starting with **lowercase**. e.g, *cettia cetti*.
```python
python download.py --name "cettia cetti"
```

Download audio data for a file of species names. Format requirement: names divided by "**\n**"
```python
python download.py --name name_file
```

General Usage:
```
usage: download.py [-h] --name NAME

download bird audios

optional arguments:
  -h, --help   show this help message and exit
  --name NAME  [1] name of one bird species; [2] file of bird species spaced
               by '\n'
```
### Multi-thread
#### Usage
Speed up downloading using multiple threads.
```python
python download-mult.py --name "cettia cetti" --process-ratio 0.6
```
Download multiple birds in a file, format requirement: names divided by "**\n**"
```python
python download-mult.py --name name_file --process-ratio 0.6
```
General Usage:
```
usage: download-mult.py [-h] --name NAME [--process-ratio PROCESS_RATIO]

download bird audios

optional arguments:
  -h, --help            show this help message and exit
  --name NAME           [1] name of one bird species; [2] file of bird species
                        spaced by '\n'
  --process-ratio PROCESS_RATIO
                        float[0~1], define cpu utilities in downloading audios
                        [default: 0.8]
```
#### Killing multiprocess
It would be hard to kill multiprocess programs manually. `download-mult.py` has a backdoor for this concern: it will automatically generate a `kill.sh` after downloading started. Kill program by
```
bash kill.sh
```

#### Badcase backup
Find download failure record at `bad_urls.txt` so that you can redownload afterwards if necessary.

## To-do
- [x] [12.29] multiprocess download
- [x] [1.1] Automated killing script for multiprocess program
- [x] [1.1] Bad url backup for trace back
- [ ] define sample rate prior to download

## Contact
Feel free to file an issue had you encountered any problems. Have fun!