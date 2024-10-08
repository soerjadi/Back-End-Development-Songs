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

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health")
def health():
    return {"status":"OK"}

@app.route("/count")
def count():
    return {"count":20}

@app.route("/song")
def get_song():
    db = client.songs
    songs = db.songs.find({})

    return {"songs": json_util.dumps(songs)}

@app.route("/song/<int:id>")
def get_detail_song(id):
    db = client.songs
    song = db.songs.find_one({"id": id})

    return json_util.dumps(song)

@app.route("/song", methods=["POST"])
def create_song():
    req_song = request.json

    db = client.songs
    is_exists = db.songs.find_one({"id": req_song["id"]})
    if is_exists:
        return {"Message": f"song with id {req_song['id']} already present"}, 302

    print(req_song)
    result = db.songs.insert_one(req_song)
    return {"inserted id": {"$oid":json_util.dumps(result.inserted_id)}}

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    req_song = request.json

    db = client.songs
    exists = db.songs.find_one({"id": id})
    if not exists:
        return {"message":"song not found"}, 404

    new_values = {
        "$set": req_song
    }

    db.songs.update_one({"id": id}, new_values)

    song = db.songs.find_one({"id":id})
    return json_util.dumps(song)

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    db = client.songs
    exists = db.songs.find_one({"id":id})
    if not exists:
        return {"message":"song not found"}, 404

    result = db.songs.delete_one({"id":id})

    if result.deleted_count != 1:
        return {"message":"internal server error"}, 500

    response = make_response('', 204)
    return response