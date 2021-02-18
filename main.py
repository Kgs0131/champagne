from flask import Flask, render_template, request, redirect, url_for
from flaskext.markdown import Markdown
import pickle
from os import path as os_path, mkdir as os_mkdir, remove as os_remove
from datetime import datetime
import sys, getopt
import boto3
from botocore.config import Config
import pprint

dynamodb = boto3.client('dynamodb', config=Config(region_name='us-east-1'))
pp = pprint.PrettyPrinter(indent=4)
app = Flask("Champagne")
Markdown(app)


@app.route("/")
def home():
    scan = dynamodb.scan(TableName='notes')
    allNotes = scan['Items']
    return render_template("home.html", notes=allNotes)

@app.route("/addNote")
def addNote():
    return render_template("noteForm.html", headerLabel="New Note", submitAction="createNote", cancelUrl=url_for('home'))

@app.route("/createNote", methods=["post"])
def createNote():
    noteId = 1
    scan = dynamodb.scan(TableName='notes')['Items']
    for i in scan: 
        noteId = noteId + 1

    noteId = str(noteId) 

    lastModifiedDate = datetime.now()
    lastModifiedDate = lastModifiedDate.strftime("%d-%b-%Y %H:%M:%S")
    noteTitle = request.form['noteTitle']
    noteMessage = request.form['noteMessage']

    dynamodb.put_item(TableName='notes', Item = {'id' : {'N' : noteId}, 'title' : {'S' : noteTitle}, 'notedate' : {'S': lastModifiedDate}, 'content': {'S': noteMessage}})

    return redirect(url_for('viewNote', noteId=noteId))

@app.route("/viewNote/<int:noteId>")
def viewNote(noteId):
    noteId = str(noteId)
    note = dynamodb.get_item(TableName='notes', Key = {'id': {'N' : noteId}})['Item']
    return render_template("viewNote.html", note=note, submitAction="/saveNote")

@app.route("/editNote/<int:noteId>")
def editNote(noteId):
    noteId = str(noteId)
    note = dynamodb.get_item(TableName='notes', Key = {'id': {'N' : noteId}})['Item']
    cancelUrl = url_for('viewNote', noteId=noteId)
    return render_template("noteForm.html", headerLabel="Edit Note", note=note, submitAction="/saveNote", cancelUrl=cancelUrl)

@app.route("/saveNote", methods=["post"])
def saveNote():
    lastModifiedDate = datetime.now()
    lastModifiedDate = lastModifiedDate.strftime("%d-%b-%Y %H:%M:%S")

    noteId = str(int(request.form['noteId']))
    noteTitle = request.form['noteTitle']
    noteMessage = request.form['noteMessage']
    
    dynamodb.update_item(TableName='notes', 
    Key={
        'id': {'N': noteId},
    },
    UpdateExpression="set title = :t, notedate = :d, content = :c",
    ExpressionAttributeValues={
        ':t': {'S' : noteTitle},
        ':d': {'S' :lastModifiedDate},
        ':c': {'S' :noteMessage}
        },
    ReturnValues="UPDATED_NEW")
    
    return redirect(url_for('viewNote', noteId=noteId))

@app.route("/deleteNote/<int:noteId>")
def deleteNote(noteId):
    noteId = str(noteId)
    dynamodb.delete_item(TableName='notes', Key={'id': {'N': noteId}})
    return redirect("/")

if __name__ == "__main__":
    debug = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:p:", ["debug"])
    except getopt.GetoptError:
        print('usage: main.py [-h 0.0.0.0] [-p 5000] [--debug]')
        sys.exit(2)

    port = "5000"
    host = "0.0.0.0"
    print(opts)
    for opt, arg in opts:
        if opt == '-p':
            port = arg
        elif opt == '-h':
            host = arg
        elif opt == "--debug":
            debug = True

    app.run(host=host, port=port, debug=debug)

