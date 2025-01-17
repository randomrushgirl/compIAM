# Copyright 2013, 2014 Music Technology Group - Universitat Pompeu Fabra
#
# Several functions in this file are part of Dunya and have been ported
# from pycompmusic (https://github.com/MTG/pycompmusic), the official API
#
# Dunya is free software: you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free Software
# Foundation (FSF), either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see http://www.gnu.org/licenses/

import os
import tqdm
import errno

from .conn import (
    _dunya_query_json,
    get_mp3,
    _file_for_document,
    set_token,
)
from compiam.io import (
    write_csv,
    write_json,
    write_scalar_txt,
)

from compiam.utils import get_logger

logger = get_logger(__name__)


class Corpora:
    """Dunya corpora class with access functions"""

    def __init__(self, tradition, cc, token):
        """Dunya corpora class init method.

        :param tradition: the name of the tradition.
        :param cc: bool flag to indicate if the Creative Commons version of the corpora is chosen.
        :param token: Dunya personal token to access te database.
        """
        # Load and set token
        self.token = token
        set_token(self.token)

        self.tradition = tradition
        self.collection = (
            "dunya-" + self.tradition + "-cc" if cc else "dunya-" + self.tradition
        )
        logger.warning(
            "To load the full metadata of the initialized corpora, run .get_metadata(). " + 
            "Please note that it might take a while..."
        )

    def get_collection(self):
        """Get the documents (recordings) in a collection."""
        query = _dunya_query_json("document/" + self.collection)["documents"]
        collection = []
        for doc in query:
            doc["mbid"] = doc.pop("external_identifier")
            collection.append(doc)
        return collection

    def get_recording(self, rmbid):
        """Get specific information about a recording.

        :param rmbid: A recording MBID.
        :returns: mbid, title, artists, raga, tala, work.
            ``artists`` includes performance relationships attached to the recording, the release, and the release artists.
        """
        return _dunya_query_json("api/" + self.tradition + "/recording/%s" % rmbid)
    
    def get_metadata(self):
        """Get the full metadata of the initialized corpora. It might take a while..."""

        # Initializing database
        try:
            metadata = self._get_metadata()

            self.recording_list = metadata["recording_list"]
            self.artist_list = metadata["artist_list"]
            self.concert_list = metadata["concert_list"]
            self.work_list = metadata["work_list"]
            self.raga_list = metadata["raga_list"]
            self.tala_list = metadata["tala_list"]
            self.instrument_list = metadata["instrument_list"]

        except:
            raise ValueError(
                """Error accessing metadata. Have you entered the right token? If you are confident about that, 
                consider loading the Corpora instance again."""
            )

    def _get_metadata(self):
        """Query a list of unique identifiers per each relevant tag in the Dunya database. This
        method is automatically run when the corpora is initialized.

        :returns: A dictionary of lists of unique identifiers per each tag: artists, concerts, works,
        raagas, taalas, and instruments. It also includes a complete list of recording ids for the collection
        """
        recording_list = []
        artist_list = []
        concert_list = []
        work_list = []
        raga_list = []
        tala_list = []
        instrument_list = []

        for rec in tqdm.tqdm(
            self.get_collection(), desc="Parsing metadata from database"
        ):
            try:
                # Getting artist list
                for artist in self.get_recording(rec["mbid"])["artists"]:
                    if artist["lead"]:
                        artist_list.append(artist["artist"])
                    instrument_list.append(artist["instrument"])
                # Getting concert list
                for concert in self.get_recording(rec["mbid"])["concert"]:
                    concert_list.append(concert)
                # Getting work list
                for work in self.get_recording(rec["mbid"])["work"]:
                    work_list.append(work)
                # Getting raaga list
                for raga in self.get_recording(rec["mbid"])["raaga"]:
                    raga_list.append(raga)
                # Getting taala list
                for tala in self.get_recording(rec["mbid"])["taala"]:
                    tala_list.append(tala)
                recording_list.append(rec["mbid"])
            except:
                continue

        return {
            "recording_list": recording_list,
            "artist_list": list({a["mbid"]: a for a in artist_list}.values()),
            "concert_list": list({c["mbid"]: c for c in concert_list}.values()),
            "work_list": list({w["mbid"]: w for w in work_list}.values()),
            "raga_list": list({r["uuid"]: r for r in raga_list}.values()),
            "tala_list": list({t["uuid"]: t for t in tala_list}.values()),
            "instrument_list": list({i["mbid"]: i for i in instrument_list}.values()),
        }

    def get_artist(self, ambid):
        """Get specific information about an artist.

        :param ambid: An artist MBID.
        :returns: mbid, name, concerts, instruments, recordings.
            ``concerts``, ``instruments`` and ``recordings`` include
            information from recording- and release-level
            relationships, as well as release artists.
        """
        return _dunya_query_json("api/" + self.tradition + "/artist/%s" % (ambid))

    def list_concerts(self):
        """List the concerts in the database. This function will automatically page through API results.

        :returns: A list of dictionaries containing concert information:
            ``{"mbid": MusicBrainz Release ID, "title": title of the concert}``
            For additional information about each concert use :func:`get_concert`.
        """
        return self.concert_list

    def get_concert(self, cmbid):
        """Get specific information about a concert.

        :param cmbid: A concert mbid.
        :returns: mbid, title, artists, tracks.
            ``artists`` includes performance relationships attached
            to the recordings, the release, and the release artists.
        """
        return _dunya_query_json("api/" + self.tradition + "/concert/%s" % cmbid)

    def list_works(self):
        """List the works in the database. This function will automatically page through API results.

        :returns: A list of dictionaries containing work information:
            ``{"mbid": MusicBrainz work ID, "name": work name}``
            For additional information about each work use :func:`get_work`.
        """
        return self.work_list

    def get_work(self, wmbid):
        """Get specific information about a work.

        :param wmbid: A work mbid.
        :returns: mbid, title, composers, ragas, talas, recordings.
        """
        return _dunya_query_json("api/" + self.tradition + "/work/%s" % (wmbid))

    def list_ragas(self):
        """List the ragas in the database. This function will automatically page through API results.

        :returns: A list of dictionaries containing raga information:
            ``{"uuid": raga UUID, "name": name of the raga}``
            For additional information about each raga use :func:`get_raga`.
        """
        return self.raga_list

    def get_raga(self, raga_id):
        """Get specific information about a raga.

        :param raga_id: A raga id or uuid.
        :returns: uuid, name, artists, works, composers.
            ``artists`` includes artists with recording- and release-
            level relationships to a recording with this raga.
        """
        return _dunya_query_json("api/" + self.tradition + "/raaga/%s" % str(raga_id))

    def list_talas(self):
        """List the talas in the database. This function will automatically page through API results.

        :returns: A list of dictionaries containing tala information:
            ``{"uuid": tala UUID, "name": name of the tala}``
            For additional information about each tala use :func:`get_tala`.
        """
        return self.tala_list

    def get_tala(self, tala_id):
        """Get specific information about a tala.

        :param tala_id: A tala id or uuid.
        :returns: uuid, name, artists, works, composers.
            ``artists`` includes artists with recording- and release-
            level relationships to a recording with this raga.
        """
        return _dunya_query_json("api/" + self.tradition + "/taala/%s" % str(tala_id))

    def list_instruments(self):
        """List the instruments in the database. This function will automatically page through API results.

        :returns: A list of dictionaries containing instrument information:
            ``{"id": instrument id, "name": Name of the instrument}``
            For additional information about each instrument use :func:`get_instrument`.
        """
        return self.instrument_list

    def get_instrument(self, instrument_id):
        """Get specific information about an instrument.

        :param instrument_id: An instrument id
        :returns: id, name, artists.
            ``artists`` includes artists with recording- and release-
            level performance relationships of this instrument.
        """
        return _dunya_query_json(
            "api/" + self.tradition + "/instrument/%s" % str(instrument_id)
        )

    @staticmethod
    def list_available_types(recording_id):
        """Get the available source filetypes for a Musicbrainz recording.

        :param recording_id: Musicbrainz recording ID.
        :returns: a list of filetypes in the database for this recording.
        """
        document = _dunya_query_json("document/by-id/%s" % recording_id)
        return {
            x: list(document["derivedfiles"][x].keys())
            for x in list(document["derivedfiles"].keys())
        }

    @staticmethod
    def get_annotation(recording_id, thetype, subtype=None, part=None, version=None):
        """Alias function of _file_for_document in the Corpora class.

        :param recording_id: Musicbrainz recording ID.
        :param thetype: the computed filetype.
        :param subtype: a subtype if the module has one.
        :param part: the file part if the module has one.
        :param version: a specific version, otherwise the most recent one will be used.
        :returns: The contents of the most recent version of the derived file.
        """
        return _file_for_document(
            recording_id, thetype, subtype=subtype, part=part, version=version
        )

    @staticmethod
    def save_annotation(
        recording_id, thetype, location, subtype=None, part=None, version=None
    ):
        """A version of get_annotation that writes the parsed data into a file.

        :param recording_id: Musicbrainz recording ID.
        :param thetype: the computed filetype.
        :param subtype: a subtype if the module has one.
        :param part: the file part if the module has one.
        :param version: a specific version, otherwise the most recent one will be used.
        :returns: None (a file containing the parsed data is written).
        """
        data = _file_for_document(
            recording_id, thetype, subtype=subtype, part=part, version=version
        )
        if ("tonic" in subtype) or ("aksharaPeriod" in subtype):
            write_scalar_txt(data, location)
        elif "section" in subtype:
            write_json(data, location)
        elif "APcurve" in subtype:
            write_csv(data, location)
        elif ("pitch" in subtype) or ("aksharaTicks" in subtype):
            write_csv(data, location)
        else:
            raise ValueError(
                "No writing method available for data type: {} and {}", thetype, subtype
            )

    def download_mp3(self, recording_id, output_dir):
        """Download the mp3 of a document and save it to the specificed directory.

        :param recording_id: The MBID of the recording.
        :param output_dir: Where to save the mp3 to.
        :returns: name of the saved file.
        """
        if not os.path.exists(output_dir):
            raise Exception(
                "Output directory %s doesn't exist; can't save" % output_dir
            )

        recording = self.get_recording(recording_id)
        if "concert" in list(recording.keys()):
            concert = self.get_concert(recording["concert"][0]["mbid"])
            title = recording["title"]
            artists = " and ".join([a["name"] for a in concert["concert_artists"]])
            name = "%s - %s.mp3" % (artists, title)
            name = name.replace("/", "-")
        else:
            name = recording_id + ".mp3"
        contents = get_mp3(recording_id)
        path = os.path.join(output_dir, name)
        open(path, "wb").write(contents)
        return name

    def download_concert(self, concert_id, output_dir):
        """Download the mp3s of all recordings in a concert and save them to the specificed directory.

        :param concert_id: The MBID of the concert.
        :param location: Where to save the mp3s to.
        """
        if not os.path.exists(output_dir):
            raise Exception(
                "Output directory %s doesn't exist; can't save" % output_dir
            )

        concert = self.get_concert(concert_id)
        artists = " and ".join([a["name"] for a in concert["concert_artists"]])
        concertname = concert["title"]
        concertdir = "%s - %s" % (artists, concertname)
        concertdir = concertdir.replace("/", "-")
        concertdir = os.path.join(output_dir, concertdir)
        try:
            os.makedirs(concertdir)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(concertdir):
                pass
            else:
                raise

        for r in concert["recordings"]:
            raga_id = r["mbid"]
            title = r["title"]
            disc = r["disc"]
            disctrack = r["disctrack"]
            contents = get_mp3(raga_id)
            name = "%s - %s - %s - %s.mp3" % (disc, disctrack, artists, title)
            path = os.path.join(concertdir, name)
            open(path, "wb").write(contents)
