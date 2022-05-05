# XenoPy
![PyPI](https://img.shields.io/pypi/v/xenopy?color=df)&nbsp;
![GitHub](https://img.shields.io/github/license/realzza/xenopy?color=%23FFB6C1)&nbsp;
![GitHub last commit](https://img.shields.io/github/last-commit/realzza/xenopy?color=orange)&nbsp;
![GitHub top language](https://img.shields.io/github/languages/top/realzza/xenopy?color=%236495ed)&nbsp;
[![CodeFactor](https://www.codefactor.io/repository/github/realzza/xenopy/badge)](https://www.codefactor.io/repository/github/realzza/xenopy)&nbsp;

**`XenoPy`** is a python library that builds upon [xeno-canto API 2.0](https://xeno-canto.org/article/153).

## Install
Install from `pip`.
```bash
pip install xenopy
```
Checkout the [**birdData**](https://github.com/realzza/xenopy/tree/birdData) branch to implement XenoPy from source. (ps: birdData is the former name of XenoPy)

## Usage Snippet
You can directly search for bird data for a specific species. For instance, we retrieve data for [*African Silverbill*](https://xeno-canto.org/species/Euodice-cantans) whom's `quality` better than `C` since `2020-01-01`.
```python
from xenopy import Query

q = Query(name="African silverbill", q_gt="C", since="2020-01-01")
```

### Retrieve Metafiles
```python
# retrieve metadata
metafiles = q.retrieve_meta(verbose=True)
```

### Retrieve Recordings
```python
# retrieve recordings
q.retrieve_recordings(multiprocess=True, nproc=10, attempts=10, outdir="datasets/")
```
The retrieved recordings will be located in `datasets/`, organized by bird species names.

The default downloading mode is single-threaded. `multiprocess` flag controls the usage of multiple downloading processes. `nproc` is only applicable when the `multiprocess` flag is on. The saving directory can be specified at `outDir`.

Two files will be generated while running `retrieve_recordings`, `kill_multiprocess.sh`, and `failed.txt`. To interrupt multiprocess data retrieval, one can run `bash kill_multiprocess.sh` in the terminal. 'failed.txt' contains recordings that failed the retrieval, if any. The two files will be removed automatically removed after downloading finishes. `failed.txt` will preserve if not empty so that you can check the failed recordings out.

## Define a `Query`
As you can tell from the [Usage Snippet](#Usage-Snippet), defining a query is the most important step in communicating with the API. We determined the following interface to form a query based on the xeno-canto [search tips](https://xeno-canto.org/help/search).
```markdown
name: Species Name. Specify the name of bird you intend to retrieve data from. Both English names and Latin names are acceptable.
gen: Genus. Genus is part of a species' latin name, so it is searched by default when performing a basic search (as mentioned above).
ssp: subspecies
rec: recordist. Search for all recordings from a particular recordist.
cnt: country. Search for all recordings from a particular country.
loc: location. Search for all recordings from a specific location.
rmk: remarks. Many recordists leave remarks about the recording,and this field can be searched using the rmk tag. For example, rmk:playback will return a list of recordings for which the recordist left a comment about the use of playback. This field accepts a 'matches' operator.
lat: latitude.
lon: longtitude
box: search for recordings that occur within a given rectangle. The general format of the box tag is as follows: box:LAT_MIN,LON_MIN,LAT_MAX,LON_MAX. Note that there must not be any spaces between the coordinates.
also: To search for recordings that have a given species in the background.
type: Search for recordings of a particular sound type, e.g., type='song'
nr: number. To search for a known recording number, use the nr tag: for example nr:76967. You can also search for a range of numbers as nr:88888-88890.
lc: license.
q: quality ratings. 
q_lt: quality ratings less than
q_gt: quality ratings better than
    Usage Examples:
          Recordings are rated by quality. Quality ratings range from A (highest quality) to E (lowest quality). To search for recordings that match a certain quality rating, use the q, q_lt, and q_gt tags. For example:
            - q:A will return recordings with a quality rating of A.
            - q:0 search explicitly for unrated recordings
            - q_lt:C will return recordings with a quality rating of D or E.
            - q_gt:C will return recordings with a quality rating of B or A.
len: recording length control parameter.
len_lt: recording length less than
len_gt: recording length greater than
    Usage Examples:
        len:10 will return recordings with a duration of 10 seconds (with a margin of 1%, so actually between 9.9 and 10.1 seconds)
        len:10-15 will return recordings lasting between 10 and 15 seconds.
        len_lt:30 will return recordings half a minute or shorter in length.
        len_gt:120 will return recordings longer than two minutes in length.
area: continents. Valid values for this tag: africa, america, asia, australia, europe.
since: 
    Usage Examples:
        - since=3, since the past three days
        - since=YYYY-MM-DD, since the particular date
year: year
month: month. year and month tags allow you to search for recordings that were recorded on a certain date. 
```

## todo
- [x] create query object for single species, containing features like
    - [x] retrieve metedata
    - [x] retrieve bird songs
- [x] add multiprocessing downloading feature

## Open Source
The first generation of `xenocanto` [package](https://github.com/ntivirikin/xeno-canto-py) is hard to use also inefficient. Thus I wrapped the [2.0 API](https://xeno-canto.org/article/153) version in a more straightforward and efficient interface.
Feel free to file an issue had you encountered any bugs, or prompt a PR to `XenoPy` to join me in maintenance and optimization.