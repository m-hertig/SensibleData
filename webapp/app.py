# -*- coding: utf-8 -*-
import os, time
import uuid

from elasticsearch import Elasticsearch
from flask import Flask, send_from_directory, render_template, redirect, flash, session, url_for
from flask_cors import CORS, cross_origin
from flask import request
from werkzeug.utils import secure_filename
import werkzeug.serving
import requests, json, sys
from configobj import ConfigObj
import certifi
import boto3, pprint
import boto3.session
from PIL import Image
# from geoip import geolite2

UPLOAD_FOLDER = '/home/pi/SensibleData/images/'

application = Flask(__name__, static_url_path='')
application.secret_key = '\xc2\x10\xe9\xde\xfd\xe0Y\xad\x0e\xc8\x97\xd9y\x88\xb4\xe4q9,\xff!\x8b\xbd\x91'
CORS(application)
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@application.route("/")
def uploadPage():
    flash("Photo Booth")
    return render_template('index.html')

@application.route("/upload", methods=['POST'])
def upload():
    configobj = ConfigObj('server.config')
    print 'hallo uploader!!!!'
    flash("Trying to analyze your face!")
    moods = {}
    req = request
    if request.method == 'POST':
        try:
            webcam_file = request.files['webcam']
            if webcam_file:
                webcam_file_image = Image.open(webcam_file)
                filename = secure_filename(str(uuid.uuid4())+".jpg")
                filePath = os.path.join(application.config['UPLOAD_FOLDER'], filename)
                webcam_file_image.save(filePath,optimize=True,quality=100)

                try:
                    print "Trying to get Face Analysis from AWS Rekognition"
                    rekognition = boto3.client('rekognition')

                    with open(filePath, 'rb') as source_image:
                        source_bytes = source_image.read()
                        botoSession = boto3.session.Session(region_name='eu-central-1')
                        s3client = botoSession.client('s3', config= boto3.session.Config(signature_version='s3v4'))
                        bucket_name = "sensiblebucket";
                        s3client.upload_fileobj(source_image, bucket_name, "uploads/"+filename)

                    response = rekognition.detect_faces(
                                   Image={ 'Bytes': source_bytes },
                		   Attributes=['ALL'],
                    )

                    pprint.pprint(response)


                    # sample jsondata = {u'url': u'https://www.dropbox.com/s/m8gkdlh6zdeea9e/2015-05-16%2016.13.08.jpg?dl=1', u'face_detection': [{u'emotion': {u'calm': 0.03, u'confused': 0.28, u'sad': 0.09}, u'confidence': 0.99, u'beauty': 0.12593, u'pose': {u'yaw': 0.08, u'roll': 0.1, u'pitch': 14.79}, u'sex': 1, u'race': {u'white': 0.58}, u'boundingbox': {u'tl': {u'y': 48.46, u'x': 139.23}, u'size': {u'width': 376.15, u'height': 376.15}}, u'smile': 0, u'quality': {u'brn': 0.51, u'shn': 1.6}, u'mustache': 0, u'beard': 0}], u'ori_img_size': {u'width': 576, u'height': 576}, u'usage': {u'status': u'Succeed.', u'quota': 19968, u'api_id': u'yHvz5xQExIxdKT1M'}}
                    print "Got it"
                    print response
                    firstPerson = response["FaceDetails"][0]

                    #beauty = str(int(jsondata["face_detection"][0]["beauty"]*100))
                    # 0 = female, 1 = male
                    sex = firstPerson["Gender"]["Value"]
                    if sex.lower() == "male":
                        sex = "M"
                    elif sex.lower() == "female":
                        sex = "F"
                    age = str(int((firstPerson["AgeRange"]["High"] + firstPerson["AgeRange"]["Low"])/2))
                    #smile = jsondata["face_detection"][0]["smile"]
                    emotions = firstPerson["Emotions"]
                    for emotion in emotions:
                        att = emotion['Type'].lower()
                        val = int(round(emotion['Confidence']))
                        moods[att] = val


                except Exception as e:
                    print(e)
                    print "error parsing data"
                    # Error analyzing your face! Please try again!
                    return "2"

                #calculate happiness
                #happiness = 50+(moods['happy']/2)-(moods['sad']/2)

                # clientIPAddress = request.headers.get('X-Forwarded-For', request.remote_addr)
                # print clientIPAddress
                # country = "Unknown"
                # match = geolite2.lookup(clientIPAddress)
                # if (match is not None):
                #     country = match.country

                # here comes the elasticsearch index command
                # data = {'age':age, 'gender':sex, 'file':configobj["pictures_url"]+filename, 'timestamp':time.time(), 'country':country, 'event':'Sheffield'}
                # # append moods to data
                # data.update(moods)
                # print data
                # print "Trying to put data into elasticsearch"

                # es = Elasticsearch(
                #     [configobj["elasticsearch_url"]],
                #     #port=80,
                #     use_ssl=True,
                #     verify_certs=True,
                #     ca_certs=certifi.where(),
                #     request_timeout=1000
                # )
                # try:
                #     es.index(index='faces', doc_type='face', body=data)
                # except Exception as e:
                #     # "Error indexing your face! Please try again!"
                #     return "3"

                #target_url = config[config[elasticsearch_index_url]] % filename
                #r = requests.put(target_url, data=json.dumps(data))
                #jsondata =  r.json()
                # sample jsondata = {u'url': u'https://www.dropbox.com/s/m8gkdlh6zdeea9e/2015-05-16%2016.13.08.jpg?dl=1', u'face_detection': [{u'emotion': {u'calm': 0.03, u'confused': 0.28, u'sad': 0.09}, u'confidence': 0.99, u'beauty': 0.12593, u'pose': {u'yaw': 0.08, u'roll': 0.1, u'pitch': 14.79}, u'sex': 1, u'race': {u'white': 0.58}, u'boundingbox': {u'tl': {u'y': 48.46, u'x': 139.23}, u'size': {u'width': 376.15, u'height': 376.15}}, u'smile': 0, u'quality': {u'brn': 0.51, u'shn': 1.6}, u'mustache': 0, u'beard': 0}], u'ori_img_size': {u'width': 576, u'height': 576}, u'usage': {u'status': u'Succeed.', u'quota': 19968, u'api_id': u'yHvz5xQExIxdKT1M'}}
                # print "Done"
                #print jsondata

                    # moodString = ""
                    # for key,value in moods.iteritems():
                    #     moodString += str(key).capitalize()+": "+str(value)+"% <br>"
                return "Analyzed your face!"
                # return "Analyzed your face!<br>"+str(sex)+" "+str(age)+" yrs<br>"+moodString

        except Exception as ex:
            print ex

@application.route('/pictures/<path:path>')
def get_picture(path):
    return send_from_directory(application.config['UPLOAD_FOLDER'], path)


if __name__ == "__main__":
#    key = '/home/pi/SensibleData/webapp/ssl/server.key'
#    cert = '/home/pi/SensibleData/webapp/ssl/server.crt'
    application.run('0.0.0.0', 80, debug=True)
