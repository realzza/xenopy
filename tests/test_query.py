import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock
from urllib import error, parse

from query import API_ENDPOINT, API_KEY_ENV_VAR, Query


def quiet_call(func, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        with contextlib.redirect_stderr(io.StringIO()):
            return func(*args, **kwargs)


def quiet_query(*args, **kwargs):
    return quiet_call(Query, *args, **kwargs)


class FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("UTF-8")

    def read(self):
        return self._payload


def parsed_query(url):
    parsed = parse.urlsplit(url)
    return parsed, dict(parse.parse_qsl(parsed.query))


class QueryConstructionTests(unittest.TestCase):
    def test_name_builds_tagged_v3_english_name_query(self):
        q = quiet_query(name="African silverbill", q_gt="C", since="2020-01-01")

        self.assertEqual(
            q.query, 'en:"African silverbill" since:2020-01-01 q:>C'
        )

    def test_v3_tags_quote_multi_word_values_and_convert_operators(self):
        q = quiet_query(
            gen="Larus",
            sp="fuscus",
            cnt="United States",
            rec_type="song",
            q_lt="C",
            len_gt=120,
        )

        self.assertEqual(
            q.query,
            'sp:fuscus gen:Larus cnt:"United States" type:song q:<C len:>120',
        )

    def test_missing_api_key_fails_before_network_request(self):
        q = quiet_query(sp='"larus fuscus"')

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("query.request.urlopen") as urlopen:
                with self.assertRaisesRegex(ValueError, API_KEY_ENV_VAR):
                    quiet_call(q.retrieve_meta)

        urlopen.assert_not_called()


class MetadataRetrievalTests(unittest.TestCase):
    def test_retrieve_meta_uses_v3_endpoint_key_per_page_and_paginates(self):
        responses = [
            FakeResponse(
                {
                    "numRecordings": "2",
                    "numSpecies": "1",
                    "page": 1,
                    "numPages": 2,
                    "recordings": [{"id": "1"}],
                }
            ),
            FakeResponse(
                {
                    "numRecordings": "2",
                    "numSpecies": "1",
                    "page": 2,
                    "numPages": 2,
                    "recordings": [{"id": "2"}],
                }
            ),
        ]
        q = quiet_query(sp='"larus fuscus"', api_key="secret", per_page=1)

        with mock.patch("query.request.urlopen", side_effect=responses) as urlopen:
            data = quiet_call(q.retrieve_meta, verbose=True)

        self.assertEqual(data["numRecordings"], 2)
        self.assertEqual(data["recordings"], [{"id": "1"}, {"id": "2"}])
        self.assertNotIn("page", data)
        self.assertNotIn("numPages", data)

        requested_urls = [call.args[0] for call in urlopen.call_args_list]
        first_url, second_url = requested_urls
        parsed, params = parsed_query(first_url)
        self.assertEqual(parse.urlunsplit(parsed._replace(query="")), API_ENDPOINT)
        self.assertEqual(params["query"], 'sp:"larus fuscus"')
        self.assertEqual(params["key"], "secret")
        self.assertEqual(params["per_page"], "1")
        self.assertEqual(params["page"], "1")
        self.assertEqual(parsed_query(second_url)[1]["page"], "2")

    def test_http_api_errors_include_response_body(self):
        q = quiet_query(sp='"larus fuscus"', api_key="bad-key")
        body = io.BytesIO(
            b'{"error":"client_error","message":"Missing or invalid key"}'
        )
        http_error = error.HTTPError(
            API_ENDPOINT, 401, "Unauthorized", hdrs={}, fp=body
        )

        with mock.patch("query.request.urlopen", side_effect=http_error):
            with self.assertRaisesRegex(RuntimeError, "Missing or invalid key"):
                quiet_call(q.retrieve_meta, attempts=1)


class RecordingDownloadTests(unittest.TestCase):
    def test_retrieve_recordings_normalizes_file_url_and_appends_key(self):
        q = quiet_query(sp='"larus fuscus"', api_key="secret")
        recordings = [
            {
                "id": "1065457",
                "en": "Lesser Black-backed Gull",
                "file": "//xeno-canto.org/1065457/download",
            },
            {
                "id": "restricted",
                "en": "Hidden Bird",
                "file": "",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.object(q, "retrieve_meta", return_value=recordings):
                with mock.patch("query.request.urlretrieve") as urlretrieve:
                    quiet_call(q.retrieve_recordings, outdir=tmpdir)

        urlretrieve.assert_called_once()
        url, output_path = urlretrieve.call_args.args
        parsed, params = parsed_query(url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "xeno-canto.org")
        self.assertEqual(parsed.path, "/1065457/download")
        self.assertEqual(params["key"], "secret")
        self.assertTrue(output_path.endswith("LesserBlack-backedGull/1065457.mp3"))


if __name__ == "__main__":
    unittest.main()
