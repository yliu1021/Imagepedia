from flask import Flask, render_template, request, flash, redirect, make_response
from werkzeug import secure_filename
import os
import ImageRecognition
import WikiParser
import json

import struct
import imghdr
import urllib

def get_image_size(fname):
    '''Determine the image type of fhandle and return its size.
    from draco'''
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            return
        if imghdr.what(fname) == 'png':
            check = struct.unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                return
            width, height = struct.unpack('>ii', head[16:24])
        elif imghdr.what(fname) == 'gif':
            width, height = struct.unpack('<HH', head[6:10])
        elif imghdr.what(fname) == 'jpeg':
            try:
                fhandle.seek(0) # Read 0xff next
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf:
                    fhandle.seek(size, 1)
                    byte = fhandle.read(1)
                    while ord(byte) == 0xff:
                        byte = fhandle.read(1)
                    ftype = ord(byte)
                    size = struct.unpack('>H', fhandle.read(2))[0] - 2
                # We are at a SOFn block
                fhandle.seek(1, 1)  # Skip `precision' byte.
                height, width = struct.unpack('>HH', fhandle.read(4))
            except Exception: #IGNORE:W0703
                return
        else:
            return
        return [width, height]
        
        
UPLOAD_FOLDER = 'static/'
ALLOWED_EXTENSIONS = ['jpg', 'png', 'jpeg', 'gif']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    
@app.route('/' , methods = ['GET','POST'])
def home():
    if request.method == 'POST':
        for file in os.listdir('static/'):
            if file.endswith('.png') or file.endswith('.jpg') or file.endswith('.gif') or file.endswith('.jpeg'):
                os.remove('static/'+file)
        f = request.files['file']
        filename = secure_filename(f.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            f.save(filepath)
        except IOError:
            return """\
            <!DOCTYPE html>
            <html lang="en">

            <head><title>Error</title></head>
            <body>
            <h1>Please upload a valid file</h1>
            </body>
            """
        
        r = None
        try:
            r = ImageRecognition.getResponse(filepath,
                ImageRecognition.labelFeature,
                ImageRecognition.logoFeature,
                ImageRecognition.faceFeature,
                ImageRecognition.landmarkFeature,
                ImageRecognition.textFeature,
            )
        except IOError:
            return """\
            <!DOCTYPE html>
            <html lang="en">

            <head><title>Error</title></head>
            <body>
            <h1>Unable to open file</h1>
            </body>
            """
        newfilepath = filepath.split('/')[1]
        
        dimensions = get_image_size(filepath)
        if dimensions == None:
            print "UNABLE TO GET IMAGE SIZE"
            dimensions = [600, 600]
        print("DIMENSIONS: ", dimensions)
        if dimensions[0] > dimensions[1]:
            dimensions[1] = int(float(dimensions[1]) / float(dimensions[0]) * 600)
            dimensions[0] = 600
        else:
            dimensions[0] = int(float(dimensions[0]) / float(dimensions[1]) * 600)
            dimensions[1] = 600
            
        print("NEW DIMENSIONS: ", dimensions)
        print("RESPONSE: ", r)
        
        labels = []
        faces = []
        logos = []
        landmarks = []
        texts = []
        if 'label' in r:
            for label in r['label']:
                name = label['description']
                content = WikiParser.createSection(name)
                name = "<h3 style='color:white; background-color:black'>" + name.capitalize() + "</h3>"
                if content == None:
                    labels.append(name.capitalize())
                    continue
                summary = ""
                if content.content == None:
                    summary = "<p style='color:black'>" + content.url + "</p>"
                else:
                    summary = "<p style='color:black'>" + content.content.encode('ascii', 'xmlcharrefreplace') + "</p>"
                url = '<a href="{}" style="text-decoration: none">'.format(content.url) + name + summary+"</a>"
                labels.append(url)
            labels = ["<h1>Wikipedia suggestions</h1>"] + labels
                
        if 'face' in r:
            for (i, face) in enumerate(r['face']):
                faces.append("<h3 style='color:white; background-color:black'>Face {}:</h3>".format(i+1))
                if 'joy' in face:
                    if face['joy'] > 2:
                        faces.append("<p style='color:black'>Appears joyful</p>")
                if 'surprise' in face:
                    if face['surprise'] > 2:
                        faces.append("<p style='color:black'>Appears surprised</p>")
                if 'sorrow' in face:
                    if face['sorrow'] > 2:
                        faces.append("<p style='color:black'>Appears sorrowful</p>")
                if 'anger' in face:
                    if face['anger'] > 2:
                        faces.append("<p style='color:black'>Appears angry</p>")
                if 'blurred' in face:
                    if face['blurred'] > 2:
                        faces.append("<p style='color:black'>Appears blurry</p>")
                if 'underExposed' in face:
                    if face['underExposed'] > 2:
                        faces.append("<p style='color:black'>Appears under exposed</p>")
                if 'headwear' in face:
                    if face['headwear'] > 2:
                        faces.append("<p style='color:black'>Headwear detected</p>")
                if 'panAngle' in face:
                    angle = face['panAngle']
                    faces.append("<p style='color:black'>Pan Angle: {:.3}&deg;</p>".format(angle))
                if 'tiltAngle' in face:
                    angle = face['tiltAngle']
                    faces.append("<p style='color:black'>Tilt Angle: {:.3}&deg;</p>".format(angle))
                if 'rollAngle' in face:
                    angle = face['rollAngle']
                    faces.append("<p style='color:black'>Roll Angle: {:.3}&deg;</p>".format(angle))
            faces = ["<h1>Facial Analysis</h1>"] + faces
        
        if 'logo' in r:
            names = []
            for logo in r['logo']:
                name = logo['description']
                content = WikiParser.createSection(name)
                if content == None:
                    if name not in names:
                        logos.append("<h3 style='color:white; background-color:black'>" + name + "</h3>")
                        names.append(name)
                    continue
                name = "<h3 style='color:white; background-color:black'>" + name + "</h3>"
                summary = ""
                if content.content == None:
                    summary = "<p style='color:black'>" + content.url + "</p>"
                else:
                    summary = "<p style='color:black'>" + content.content.encode('ascii', 'xmlcharrefreplace') + "</p>"
                url = '<a href="{}" style="text-decoration: none">'.format(content.url) + name + summary+"</a>"
                logos.append(url)
            logos = ["<h1>Logo Recognition</h1>"] + logos    
        
        if 'landmark' in r:
            names = []
            print("LANDMARKS: ", r['landmark'])
            for landmark in r['landmark']:
                name = landmark['description']
                if name in names:
                    continue
                names.append(name)
                content = WikiParser.createSection(name)
                location = ""
                if len(landmark['locations']) > 0:
                    location = landmark['locations'][0]
                header = "<h3 style='color:white; background-color:black'>{} ({}, {})</h3>".format(name, location[0], location[1])
                if content == None:
                    landmarks.append(header)
                    continue
                
                summary = "<p style='color:black'>" + content.content.encode('ascii', 'xmlcharrefreplace') + "</p>"
                mapUrl = '<a href="https://www.google.com/maps/place/{}/@{:.7},{:.7}" style="text-decoration: none">'.format(urllib.quote(name), location[0], location[1]) + header + "</a>"
                wikiUrl = '<a href="{}" style="text-decoration: none">'.format(content.url) + summary + "</a>"
                landmarks.append(mapUrl)
                landmarks.append(wikiUrl)
                
            landmarks = ["<h1>Landmarks</h1>"] + landmarks
        
        if 'text' in r:
            text = r['text'][0]
            description = text['description']
            texts.append(description.encode('ascii', 'xmlcharrefreplace'))
            texts = ["<h1>OCR</h1>"] + texts
        
        html = """\
            <!DOCTYPE html>
            <html lang="en">

            <head>

            <meta charset="utf-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta name="description" content="">
            <meta name="author" content="">

            <title>Imagine</title>

            <!-- Bootstrap Core CSS -->
            <link href="/static/css/bootstrap.min.css" rel="stylesheet">

            <!-- Custom CSS -->
            <link href="/static/css/agency.css" rel="stylesheet">	
        	<link href="/static/css/new.css" rel="stylesheet">	

            <!-- Custom Fonts -->
            <link href="/static/font-awesome/css/font-awesome.min.css" rel="stylesheet" type="text/css">
            <link href="https://fonts.googleapis.com/css?family=Montserrat:400,700" rel="stylesheet" type="text/css">
            <link href='https://fonts.googleapis.com/css?family=Kaushan+Script' rel='stylesheet' type='text/css'>
            <link href='https://fonts.googleapis.com/css?family=Droid+Serif:400,700,400italic,700italic' rel='stylesheet' type='text/css'>
            <link href='https://fonts.googleapis.com/css?family=Roboto+Slab:400,100,300,700' rel='stylesheet' type='text/css'>

            <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
            <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
            <!--[if lt IE 9]>
                <script src="https://oss.maxcdn.com/libs/html5shiv/3.7.0/html5shiv.js"></script>
                <script src="https://oss.maxcdn.com/libs/respond.js/1.4.2/respond.min.js"></script>
            <![endif]-->

        </head>""" + """\
        <body id="page-top" class="index" link='black' vlink='black' style='background-color:white'>

            <!-- Navigation -->
            <nav class="navbar navbar-default navbar-fixed-top">
                <div class="container">
                    <!-- Brand and toggle get grouped for better mobile display -->
                    <div class="navbar-header page-scroll">
                        <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
                            <span class="sr-only">Toggle navigation</span>
                            <span class="icon-bar"></span>
                            <span class="icon-bar"></span>
                            <span class="icon-bar"></span>
                        </button>
                        <a class="navbar-brand page-scroll" href="#page-top" style="background-color:black">Imagepedia</a>
                    </div>

                    <!-- Collect the nav links, forms, and other content for toggling -->
                    <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
                        <ul class="nav navbar-nav navbar-right">
                            <li class="hidden">
                                <a href="#page-top"></a>
                            </li>
                            <li>
                                <a class="page-scroll" href="#services"></a>
                            </li>
                            <li>
                                <a class="page-scroll" href="#portfolio"></a>
                            </li>
                            <li>
                                <a class="page-scroll" href="#about"></a>
                            </li>
                            <li>
                                <a class="page-scroll" href="#team"></a>
                            </li>
                            <li>
                                <a class="page-scroll" href="#contact"></a>
                            </li>
                        </ul>
                    </div>
                    <!-- /.navbar-collapse -->
                </div>
                <!-- /.container-fluid -->
            </nav>
            <div align="center"><a><img src="/static/{p}" width="{width}" height="{height}"></a></div>
            {landmarks}
            {logos}
            {faces}
            {labels}
            {texts}
        </body>
        </html>
        """.format(p = newfilepath, texts = "".join(texts), landmarks = "".join(landmarks), logos = "".join(logos), labels = "".join(labels), faces = "".join(faces), width = dimensions[0], height = dimensions[1])
        response = make_response(html, 200)
        response.headers['Content-Type'] = 'text/html'
        
        return response
    else:
        return render_template('index.html')

if __name__ == '__main__':
   app.run(debug = True)