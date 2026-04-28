# XenoPy
![PyPI](https://img.shields.io/pypi/v/xenopy?color=df)&nbsp;
![GitHub](https://img.shields.io/github/license/realzza/xenopy?color=%23FFB6C1)&nbsp;
![GitHub last commit](https://img.shields.io/github/last-commit/realzza/xenopy?color=orange)&nbsp;
![GitHub top language](https://img.shields.io/github/languages/top/realzza/xenopy?color=%236495ed)&nbsp;
[![CodeFactor](https://www.codefactor.io/repository/github/realzza/xenopy/badge)](https://www.codefactor.io/repository/github/realzza/xenopy)&nbsp;
[![DOI](https://zenodo.org/badge/442515920.svg)](https://zenodo.org/badge/latestdoi/442515920)

**`XenoPy`** is a Python library for [xeno-canto API v3](https://xeno-canto.org/explore/api).
API v3 requires an API key for every request.

## Install
Install from `pip`.
```bash
pip install xenopy
```
Set your API key in environment variable `XENO_CANTO_API_KEY` (or pass `api_key=...` to `Query`):
```bash
export XENO_CANTO_API_KEY="your_xeno_canto_key"
```
Checkout the [**birdData**](https://github.com/realzza/xenopy/tree/birdData) branch to implement XenoPy from source. (ps: birdData is the former name of XenoPy)


## Usage
API v3 requires:
- tagged search terms (`sp:`, `gen:`, `en:`, etc.)
- an API key (`api_key` argument or `XENO_CANTO_API_KEY`)

### Basic Query
For exact species lookups, prefer `sp` over common-name `name`:
```python
from xenopy import Query

q = Query(
    api_key="your_xeno_canto_key",  # optional if XENO_CANTO_API_KEY is set
    sp="euodice cantans",
    grp="birds",
    q_gt="C",
    since="2020-01-01",
    per_page=100,  # optional, 50-500
)
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
As shown in the [Usage](#Usage) section, defining a query is the most important step in communicating with the API.
The v3 API no longer supports "tag-less" search terms, so each query term uses an explicit field tag.
```markdown
api_key: Required for API v3. You can pass it directly or via XENO_CANTO_API_KEY.
per_page: Optional page size for API v3, range 50-500.
name: Common-name search helper mapped to `en:` in API v3.
sp: Species field in API v3 (recommended for exact species lookups).
fam: Family field in API v3.
grp: Group field (birds, bats, frogs, etc.).
gen: Genus.
ssp: subspecies
rec: recordist. Search for all recordings from a particular recordist.
cnt: country. Search for all recordings from a particular country.
loc: location. Search for all recordings from a specific location.
rmk: remarks. Many recordists leave remarks about the recording,and this field can be searched using the rmk tag. For example, rmk:playback will return a list of recordings for which the recordist left a comment about the use of playback. This field accepts a 'matches' operator.
lat: latitude.
lon: longtitude
box: search for recordings that occur within a given rectangle. The general format of the box tag is as follows: box:LAT_MIN,LON_MIN,LAT_MAX,LON_MAX. Note that there must not be any spaces between the coordinates.
also: To search for recordings that have a given species in the background.
rec_type: Search for recordings of a particular sound type, e.g., rec_type='song'
nr: number. To search for a known recording number, use the nr tag: for example nr:76967. You can also search for a range of numbers as nr:88888-88890.
lic: license.
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
sex: animal sex.
stage: life stage.
method: recording method.
smp: sample rate.
```

### Common Patterns
```python
# common name search (mapped to en:)
Query(name="lesser black-backed gull", api_key="...")

# strict species search
Query(sp="larus fuscus", api_key="...")

# genus + species tags
Query(gen="larus", sp="fuscus", api_key="...")
```

## Citation
If `XenoPy` is helpful in your project or research in any form, you can cite this software as the following
```bibtex
@software{ziang_zhou_2022_6545294,
  author       = {Ziang Zhou},
  title        = {realzza/xenopy: XenoPy v0.0.4},
  month        = may,
  year         = 2022,
  publisher    = {Zenodo},
  version      = {v0.0.4},
  doi          = {10.5281/zenodo.6545294},
  url          = {https://doi.org/10.5281/zenodo.6545294}
}
```

## Update History

:tada: **v0.1.0** (planned)
- Migrate API integration to xeno-canto API v3.
- Add API key support and `per_page` support.
- Add first-class v3 tags (`sp`, `fam`, `grp`, `sex`, `stage`, `method`, `smp`).
- Improve query formatting for quoted values.
- Normalize download URLs and improve request error handling.

:tada: [**v0.0.4**](https://pypi.org/project/xenopy/0.0.4/)
- Support Query by bird `name`.
- Cut inessential processes in query traffic.
- Optimized query assignment strategy in recording retrieval.

## todo
- [x] create query object for single species, containing features like
    - [x] retrieve metedata
    - [x] retrieve bird songs
- [x] add multiprocessing downloading feature

## Open Source
The first generation of `xenocanto` [package](https://github.com/ntivirikin/xeno-canto-py) is hard to use also inefficient. Thus I wrapped the current [v3 API](https://xeno-canto.org/explore/api) in a straightforward interface.
Feel free to file an issue had you encountered any bugs, or prompt a PR to `XenoPy` to join me in maintenance and optimization.