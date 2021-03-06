from flask import Flask
from flask import request
from flask import render_template
from pytinysong.request import TinySongRequest
import os
import subprocess
import boto

app = Flask(__name__)

@app.route('/')
def my_form():
    return render_template("my_form.html")

@app.route('/', methods=['POST'])
def my_form_post():
    os.system("rm files.txt")
    os.system("rm *.mp4") 

    youtube_url = request.form['text']

    # os.system("cd #{RAILS_ROOT}/tmp/")

    p = subprocess.Popen("youtube-dl -e --get-title " + youtube_url, stdout=subprocess.PIPE, shell=True)
    (youtube_title, err) = p.communicate()

    os.system("youtube-dl " + youtube_url) 

    os.system("ls > files.txt") 

    f = open('files.txt', 'r')
    
    while True:
        filename = f.readline()
        
        if (".mp4" in filename):
            break

        if (filename == ""):
            break

    f.close()

    # load metadata using pytinysong
    song = TinySongRequest(api_key=os.environ['TINYSONG_APIKEY'])
    results = song.request_metadata(youtube_title)

    artist_name = results.artist_name
    song_name = results.song_name
    album_name = results.album_name

    # do i need this?
    filename = filename.replace(" ", "\ ")
    filename = filename.replace("\n", "")
    filename_parsed = filename.replace("\ ", "_")
    filename_parsed = filename_parsed.replace("\n", "")

    os.system("mv " + filename + " " + filename_parsed)

    mp3_file = filename_parsed[0:len(filename_parsed) - 4] + ".mp3"

    # build string
    ffmpeg_path = "/app/.heroku/vendor/ffmpeg/bin/"

    ffmpeg = ffmpeg_path + "ffmpeg -y -i " + filename_parsed # issue: i want a prettier .mp3 file
    ffmpeg = ffmpeg + " -metadata title=" +  "\"" + song_name   + "\"" + " "
    ffmpeg = ffmpeg + " -metadata artist=" + "\"" + artist_name + "\"" + " "
    ffmpeg = ffmpeg + " -metadata album=" + "\""  + album_name  + "\"" + " " + mp3_file

    os.system(ffmpeg)

    # p = subprocess.Popen("ls -l", stdout=subprocess.PIPE, shell=True)
    # (final_download, err) = p.communicate()

    # upload to aws s3
    AWS_ACCESS_KEY_ID     = os.environ['S3_KEY']
    AWS_SECRET_ACCESS_KEY = os.environ['S3_SECRET']

    conn = boto.connect_s3()
    
    bucket = conn.get_bucket('downloader-proj-assets')

    # testfile = "Battles_-_Tras_3-Blfi00qCQs4.mp3" #mp3_file
    testfile = mp3_file

    # return final_download

    import sys
    def percent_cb(complete, total): # might not need this
        sys.stdout.write('.')
        sys.stdout.flush()

    from boto.s3.key import Key
    k = Key(bucket)
    k.key = testfile
    k.set_contents_from_filename(testfile, # or this
        cb=percent_cb, num_cb=10)

    k.set_acl('public-read')

    final_download = "https://s3.amazonaws.com/downloader-proj-assets/" + k.key
    return render_template("my_form_2.html", final_download = final_download) #final_download = amazon link

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) # app.run()
