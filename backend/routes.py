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


def song_not_found_response():
    return make_response({"message": "song with id not found"}, 404)

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id: str):
    song = db.songs.find_one({"id": id})
    if not song:
        return song_not_found_response()
    return make_response(parse_document(song), 200)


def invalid_input_parameter_response():
    return make_response({"message": "Invalid input parameter"}, 442)

@app.route("/song", methods=["POST"])
def create_song() -> dict:
    # Get payload
    if not request.is_json:
        return invalid_input_parameter_response()

    # TODO: Add payload validation (!!)
    song = request.get_json()
    # Check if song already exists:
    if db.songs.find_one({"id": (song_id := song.get("id"))}):
        # return make_response({"message": "Song already exists"}, 409)  # 409 would make more sense to me...
        return make_response({"Message": f"song with id {song_id} already present"}, 302)

    # Add it:
    db.songs.insert_one(song)

    return make_response({"inserted id": parse_field(song.get("_id"))}, 201)


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id: int):
    # Find song to update:
    song = db.songs.find_one({"id": id})
    if not song:
        # return song_not_found_response()  # This is consistent, but the lab is not...
        return make_response({"message": "song not found"}, 404)

    # Get payload
    if not request.is_json:
        return invalid_input_parameter_response()
    updated_fields = request.get_json()

    # Update the song
    update_result = db.songs.update_one({"id": id}, {"$set": updated_fields})
    if update_result.modified_count == 0:  # Nothing updated
        return make_response({"message":"song found, but nothing updated"}, 200)

    # Song was updated:
    song = db.songs.find_one({"id": id})
    # return make_response({}, 204)  I feel this would make more sense than 201 CREATED
    return make_response(parse_document(song), 201)

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id: int):
    delete_result = db.songs.delete_one({"id": id})
    if delete_result.deleted_count == 0:
        return make_response({"message":"song not found"}, 404)
    # Song was deleted (let's assume there aren't more songs with the same id)
    return make_response({"message": "song deleted"}, 204)
