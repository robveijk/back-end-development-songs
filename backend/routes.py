from collections.abc import Mapping
from typing import Any

from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))


@app.route("/health", methods=["GET"])
def health_check():
    return make_response({"status": "OK"}, 200)


@app.route("/count", methods=["GET"])
def count_songs():
    return make_response({"count": len(songs_list)}, 200)


def parse_document(song: dict) -> dict:
    return {k: parse_field(v) for k, v in song.items() }

def parse_field(field: Any) -> Any:
    if isinstance(field, ObjectId):
        # make this similar to the example output
        return {"$oid": str(field)}
    return field

@app.route("/song", methods=["GET"])
def songs():  # Note: Used plural as it's required by the lab, but prefer singular (or get_song, actually)
    cursor = db.songs.find({})  # Cursor object
    songs = [parse_document(song) for song in cursor]
    return make_response({"songs": songs}, 200)
