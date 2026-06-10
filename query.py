import argparse
import json
import os
from urllib import error, parse, request

from tqdm import tqdm

from utils import chunks

try:
    from multiprocess import Process
except ImportError:  # pragma: no cover - exercised only when optional dep is absent
    from multiprocessing import Process

API_ENDPOINT = "https://xeno-canto.org/api/3/recordings"
API_KEY_ENV_VAR = "XENO_CANTO_API_KEY"

params = [
    "en",
    "sp",
    "gen",
    "ssp",
    "fam",
    "grp",
    "rec",
    "cnt",
    "loc",
    "rmk",
    "lat",
    "lon",
    "box",
    "also",
    "rec_type",
    "nr",
    "lic",
    "q",
    "q_lt",
    "q_gt",
    "length",
    "len_lt",
    "len_gt",
    "area",
    "since",
    "year",
    "month",
]


def _with_operator(operator, value):
    value = str(value)
    if value[:1] in ("<", ">", "="):
        return value
    return operator + value


def _format_query_value(value):
    value = str(value)
    if any(char.isspace() for char in value) and not (
        value.startswith('"') and value.endswith('"')
    ):
        value = '"' + value.replace('"', '\\"') + '"'
    return value


class Query:
    def __init__(
        self,
        name=None,
        en=None,
        sp=None,
        gen=None,
        ssp=None,
        fam=None,
        grp=None,
        rec=None,
        cnt=None,
        loc=None,
        rmk=None,
        lat=None,
        lon=None,
        box=None,
        also=None,
        rec_type=None,
        nr=None,
        lic=None,
        q=None,
        q_lt=None,
        q_gt=None,
        length=None,
        len_lt=None,
        len_gt=None,
        area=None,
        since=None,
        year=None,
        month=None,
        api_key=None,
        per_page=None,
    ):
        """
        params:
            name: Convenience alias for English species name. In xeno-canto API v3 this is sent as en:"...". str
            en: English species name.
            sp: Species. In API v3, quoted binomials such as sp='"Larus fuscus"' are supported.
            gen: Genus. Genus is part of a species' latin name, so it is searched by default when performing a basic search (as mentioned above).
            ssp: subspecies
            fam: family.
            grp: animal group, e.g. birds, grasshoppers, bats, frogs, land mammals.
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
            length: recording length control parameter.
            len_lt: recording length less than
            len_gt: recording length greater than
                Usage Examples:
                    length:10 will return recordings with a duration of 10 seconds (with a margin of 1%, so actually between 9.9 and 10.1 seconds)
                    length:10-15 will return recordings lasting between 10 and 15 seconds.
                    len_lt:30 will return recordings half a minute or shorter in length.
                    len_gt:120 will return recordings longer than two minutes in length.
            area: continents. Valid values for this tag: africa, america, asia, australia, europe.
            since:
                Usage Examples:
                    - since=3, since the past three days
                    - since=YYYY-MM-DD, since the particular date
            year: year
            month: month. year and month tags allow you to search for recordings that were recorded on a certain date.
            api_key: xeno-canto API v3 key. If omitted, retrieve_* reads XENO_CANTO_API_KEY from the environment.
            per_page: optional API v3 page size.
        """

        self.api_key = api_key
        self.per_page = per_page
        self.args = {}
        if name:
            self.args["en"] = name
        if en:
            self.args["en"] = en
        self.args["sp"] = sp
        self.args["gen"] = gen
        self.args["ssp"] = ssp
        self.args["fam"] = fam
        self.args["grp"] = grp
        self.args["rec"] = rec
        self.args["cnt"] = cnt
        self.args["loc"] = loc
        self.args["rmk"] = rmk
        self.args["lat"] = lat
        self.args["lon"] = lon
        self.args["box"] = box
        self.args["also"] = also
        self.args["type"] = rec_type
        self.args["nr"] = nr
        self.args["lic"] = lic
        self.args["q"] = q
        self.args["len"] = length
        self.args["area"] = area
        self.args["since"] = since
        self.args["year"] = year
        self.args["month"] = month

        query_options = {k: v for k, v in self.args.items() if v}
        if q_lt:
            query_options["q_lt"] = _with_operator("<", q_lt)
        if q_gt:
            query_options["q_gt"] = _with_operator(">", q_gt)
        if len_lt:
            query_options["len_lt"] = _with_operator("<", len_lt)
        if len_gt:
            query_options["len_gt"] = _with_operator(">", len_gt)
        assert query_options, "empty query, please add query options"
        query_terms = []
        for k, v in query_options.items():
            tag = (
                {"q_lt": "q", "q_gt": "q", "len_lt": "len", "len_gt": "len"}[k]
                if k in {"q_lt", "q_gt", "len_lt", "len_gt"}
                else k
            )
            query_terms.append("%s:%s" % (tag, _format_query_value(v)))
        self.query = " ".join(query_terms)
        self.args = query_options
        print("query:", self.query)

    def _get_args(self):
        return self.args

    def _init_dir(self, d):
        os.makedirs(d, exist_ok=True)

    def _get_api_key(self):
        api_key = self.api_key or os.environ.get(API_KEY_ENV_VAR)
        if not api_key:
            raise ValueError(
                "xeno-canto API v3 requires an API key. Pass api_key=... or set "
                f"{API_KEY_ENV_VAR}."
            )
        return api_key

    def _build_api_url(self, page):
        query_params = {
            "query": self.query,
            "key": self._get_api_key(),
            "page": page,
        }
        if self.per_page:
            query_params["per_page"] = self.per_page
        return API_ENDPOINT + "?" + parse.urlencode(query_params)

    def _redact_url(self, url):
        parsed = parse.urlsplit(url)
        query_params = parse.parse_qsl(parsed.query, keep_blank_values=True)
        redacted = [
            (k, "***" if k == "key" else v)
            for k, v in query_params
        ]
        return parse.urlunsplit(
            parsed._replace(query=parse.urlencode(redacted))
        )

    def _read_json_url(self, url, attempts):
        n_attempts = 0
        while n_attempts < attempts:
            try:
                r = request.urlopen(url)  # nosec
                break
            except error.HTTPError as e:
                body = e.read().decode("UTF-8", errors="replace")
                n_attempts += 1
                if n_attempts == attempts:
                    raise RuntimeError(
                        "xeno-canto API request failed: %s %s"
                        % (e, body.strip())
                    ) from e
            except error.URLError as e:
                n_attempts += 1
                if n_attempts == attempts:
                    raise RuntimeError(
                        "xeno-canto API request failed: %s" % e
                    ) from e
        data = json.loads(r.read().decode("UTF-8"))
        if "error" in data:
            raise RuntimeError("xeno-canto API returned an error: %s" % data)
        return data

    def _download_url(self, url):
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = "https://xeno-canto.org" + url

        parsed = parse.urlsplit(url)
        query_params = parse.parse_qsl(parsed.query, keep_blank_values=True)
        if not any(k == "key" for k, _ in query_params):
            query_params.append(("key", self._get_api_key()))
        return parse.urlunsplit(
            parsed._replace(query=parse.urlencode(query_params))
        )

    def retrieve_meta(self, recordings_only=False, verbose=False, attempts=10):
        """
        params:
            recordings_only: [Default:False] return metadata of recordings only
            verbose: [Default:False] flag to show query during metadata retrieval
            attempts: [Default:10] sometimes url requests may fail, upper threshold for reattempts.

        return:
            data_all: [dict] containing all metafiles from the query.
        """

        print("... retrieving metadata ...")

        page, page_num = 1, 1

        data_all = {}
        while page < page_num + 1:
            url = self._build_api_url(page)
            if verbose:
                print(self._redact_url(url))

            data = self._read_json_url(url, attempts)
            if not data_all:
                data_all = data
            else:
                data_all["recordings"] += data["recordings"]
            page_num = int(data["numPages"])
            page += 1

        data_all.pop("page", None)
        data_all.pop("numPages", None)
        data_all["numRecordings"] = len(data_all["recordings"])
        if recordings_only:
            return data_all["recordings"]
        return data_all

    def retrieve_recordings(
        self, multiprocess=False, nproc=5, attempts=10, outdir="datasets/"
    ):
        """
        params:
            multiprocess: [Default:False] use multiprocess in recordings retrieval.
            nproc: [Default:5] number of processes
            attempts: [Default:10] upper threshold for reattempts.
            outdir: [Default:datasets/] output directory of retrieved recordings. Categorized by species name.
        """
        outdir = outdir.rstrip("/") + "/"
        self._init_dir(outdir)
        if not multiprocess:
            all_recordings = self.retrieve_meta(recordings_only=True)
            all_recordings = [rec for rec in all_recordings if rec["file"]]

            downloaded = []
            problematic_urls = []
            for curr_rec in tqdm(all_recordings, desc="process %d" % os.getpid()):

                url = self._download_url(curr_rec["file"])
                name = (curr_rec["en"]).replace(" ", "")
                track_id = curr_rec["id"]

                audio_path = outdir + name + "/"
                audio_file = str(track_id) + ".mp3"

                if not os.path.exists(audio_path):
                    os.makedirs(audio_path, exist_ok=True)

                n_attempts = 0
                while n_attempts < attempts:
                    try:
                        request.urlretrieve(url, audio_path + audio_file)  # nosec
                        downloaded.append(url)
                        break
                    except error.HTTPError as e:
                        n_attempts += 1
                        if url and (n_attempts == attempts):
                            print("Bad url: %s" % url)
                            problematic_urls.append(url)

            # return downloaded, problematic_urls

        if multiprocess:
            self.__multi_dl(nproc=nproc, attempts=attempts, outdir=outdir)

    def __single_dl(self, pid, all_recordings, attempts=10, outdir="datasets/"):
        isFirst = True
        downloaded = []
        problematic_urls = []
        for curr_rec in tqdm(all_recordings, desc="process %d" % os.getpid()):
            if isFirst:
                with open("kill_multiprocess.sh", "a") as f:
                    f.write("kill -9 %d\n" % os.getpid())
                isFirst = False
            url = self._download_url(curr_rec["file"])
            name = (curr_rec["en"]).replace(" ", "")
            track_id = curr_rec["id"]

            audio_path = outdir + name + "/"
            audio_file = str(track_id) + ".mp3"

            if not os.path.exists(audio_path):
                os.makedirs(audio_path, exist_ok=True)

            n_attempts = 0
            while n_attempts < attempts:
                try:
                    request.urlretrieve(url, audio_path + audio_file)  # nosec
                    downloaded.append(url)
                    break
                except error.HTTPError as e:
                    n_attempts += 1
                    if url and (n_attempts == attempts):
                        print("Bad url: %s" % url)
                        with open("failed.txt", "a") as f:
                            f.write(url + "\n")
                        problematic_urls.append(url)

    def __multi_dl(self, nproc=5, attempts=10, outdir="datasets/"):

        all_recordings = self.retrieve_meta(recordings_only=True)
        if all_recordings:
            gen = all_recordings[0]["gen"]
            sp = all_recordings[0]["sp"]
        assert (
            len(all_recordings) != 0
        ), "No recordings for this bird species are recorded."
        all_recordings = [rec for rec in all_recordings if rec["file"]]

        assert (
            len(all_recordings) != 0
        ), f"Recordings of this species are currently restricted due to conservation concerns. If you would like access to this recording, you may contact the recordist directly. See more details at https://xeno-canto.org/species/{gen}-{sp}"

        with open("kill_multiprocess.sh", "w") as f:
            f.write("")
        with open("failed.txt", "w") as f:
            f.write("")

        nproc = min(len(all_recordings), nproc)
        recording_packs = list(chunks(all_recordings, nproc))

        worker_pool = []

        for i in range(nproc):
            p = Process(
                target=self.__single_dl, args=(i, recording_packs[i], attempts, outdir)
            )
            p.start()
            worker_pool.append(p)

        for p in worker_pool:
            p.join()

        self.__clean_up()
        print("... finished ...")

    def __clean_up(self):
        os.remove("kill_multiprocess.sh")
        with open("failed.txt", "r") as f:
            content = f.read()
        if not content:
            os.remove("failed.txt")
        else:
            print("... Some encountered failure to download, saved at failed.txt ...")
