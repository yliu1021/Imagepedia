import argparse
import base64
import httplib2

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

import WikiParser

with open("priv/apiKey.txt") as f:
    api = f.read()
apiVersion = "v1"
DISCOVERY_URL='https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'

labelFeature = 'label'
textFeature = 'text'
faceFeature = 'face'
landmarkFeature = 'landmark'
logoFeature = 'logo'
safeSearchFeature = 'safeSearchFeature'
imageProperties = 'imageProperties'

AvailFeatures = {
    labelFeature:      "LABEL_DETECTION",
    textFeature:       "TEXT_DETECTION",
    faceFeature:       "FACE_DETECTION",
    landmarkFeature:   "LANDMARK_DETECTION",
    logoFeature:       "LOGO_DETECTION",
    safeSearchFeature: "SAFE_SEARCH_DETECTION",
    imageProperties:   "IMAGE_PROPERTIES"
}

class ImageRecognition():
    
    def __init__(self, imagePath):
        with open(imagePath) as image:
            self.imageData = base64.b64encode(image.read()).decode("UTF-8")
            
        credentials = GoogleCredentials.get_application_default()
        self.service = discovery.build('vision', 'v1', credentials=credentials,
                                  discoveryServiceUrl=DISCOVERY_URL)
    
    
    def getResponse(self, *f):
        features = []
        for feature in f:
            if feature in AvailFeatures:
                features.append(AvailFeatures[feature])
        b = self._createRequest(features)
        request = self.service.images().annotate(body=b)
        response = request.execute()
        return self._parseResponse(response)
        # return response
        
    
    def _parseResponse(self, responses):
        result = {}
        for response in responses['responses']:
            if 'labelAnnotations' in response:
                result[labelFeature] = map(self._entityAnnotation, response['labelAnnotations'])
            if 'textAnnotations' in response:
                result[textFeature] = map(self._entityAnnotation, response['textAnnotations'])
            if 'faceAnnotations' in response:
                result[faceFeature] = map(self._faceAnnotation, response['faceAnnotations'])
            if 'landmarkAnnotations' in response:
                result[landmarkFeature] = map(self._entityAnnotation, response['landmarkAnnotations'])
            if 'logoAnnotations' in response:
                result[logoFeature] = map(self._entityAnnotation, response['logoAnnotations'])
            if 'safeSearchAnnotations' in response:
                result[safeSearchFeature] = self._safeSearchAnnotation(response['safeSearchAnnotation'])
            if 'imageProperties' in response:
                result[imageProperties] = self._imagePropertiesAnnotation(response['imagePropertiesAnnotation'])
            if 'error' in response:
                result = response['error']
                return result
        return result
        
        
    def _safeSearchAnnotation(self, safe):
        result = {}
        result['adult'] = self._likelihood(safe['adult'])
        result['spoof'] = self._likelihood(safe['spoof'])
        result['medical'] = self._likelihood(safe['medical'])
        result['violence'] = self._likelihood(safe['violence'])
        return result
        
        
    def _entityAnnotation(self, annotation):
        result = {}
        if 'description' in annotation:
            result['description'] = annotation['description']
        if 'locations' in annotation:
            result['locations'] = self._locationInfo(annotation['locations'])
        return result
        
        
    def _locationInfo(self, locations):
        l = []
        for loc in locations:
            if 'latLng' in loc:
                latLng = loc['latLng']
                lat = 0
                lon = 0
                if 'latitude' in latLng:
                    lat = latLng['latitude']
                if 'longitude' in latLng:
                    lon = latLng['longitude']
                l.append((lat, lon))
        return l
    
    
    def _faceAnnotation(self, annotation):
        result = {}
        result['boundingPoly'] = self._boundingPoly(annotation['boundingPoly'])
        result['landmarks'] = map(self._landmark, annotation['landmarks'])
        result['rollAngle'] = annotation['rollAngle']
        result['panAngle'] = annotation['panAngle']
        result['tiltAngle'] = annotation['tiltAngle']
        result['confidence'] = annotation['detectionConfidence']
        result['joy'] = self._likelihood(annotation['joyLikelihood'])
        print(annotation)
        result['sorrow'] = self._likelihood(annotation['sorrowLikelihood'])
        result['anger'] = self._likelihood(annotation['angerLikelihood'])
        result['surprise'] = self._likelihood(annotation['surpriseLikelihood'])
        result['underExposed'] = self._likelihood(annotation['underExposedLikelihood'])
        result['blurred'] = self._likelihood(annotation['blurredLikelihood'])
        result['headwear'] = self._likelihood(annotation['headwearLikelihood'])
        return result
        
        
    def _likelihood(self, l):
        if l == 'UNKNOWN':
            return -1
        if l == 'VERY_UNLIKELY':
            return 0
        if l == 'UNLIKELY':
            return 1
        if l == 'POSSIBLE':
            return 2
        if l == 'LIKELY':
            return 3
        if l == 'VERY_LIKELY':
            return 4
        return l
        
        
    def _boundingPoly(self, poly):
        result = []
        print("VERTICES: ", poly['vertices'])
        for vertex in poly['vertices']:
            result.append(self._vertex(vertex))
        return result
        
        
    def _vertex(self, vertex):
        x = 0
        y = 0
        if 'x' in vertex:
            x = vertex['x']
        if 'y' in vertex:
            y = vertex['y']
        return (x, y)
        
        
    def _landmark(self, landmark):
        result = {}
        result['type'] = self._type(landmark['type'])
        result['position'] = self._position(landmark['position'])
        return result
        
        
    def _position(self, pos):
        return (pos['x'], pos['y'], pos['z'])
        
    
    def _type(self, t):
        return t
        
        
    def _createRequest(self, features):
        image = {'content': self.imageData}

        f = []
        for feat in features:
            f.append({
                'type': feat,
                'maxResults': 5
            })
        
        r = [{'image': image, 'features': f}]
        b = {'requests': r}
        return b
        
        
def getResponse(location, *features):
    i = ImageRecognition(location)
    response = i.getResponse(*features)
    return response

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('image_file', help='The image you\'d like to label.')
    args = parser.parse_args()
    # print(getResults(args.image_file))
    i = ImageRecognition(args.image_file)
    response = i.getResponse(
        labelFeature,
        textFeature,
        # faceFeature
        landmarkFeature,
        logoFeature,
        # safeSearchFeature)
        )
    # print response
    if labelFeature in response:
        labels = response[labelFeature]
        print("LABELS:")
        for label in labels:
            print(label['description'])
    if textFeature in response:
        texts = response[textFeature]
        # print("TEXTS:")
        for text in texts: pass
            # print(text['description'])
    if landmarkFeature in response:
        landmarks = response[landmarkFeature]
        print("LANDMARKS:")
        for landmark in landmarks:
            print(landmark['description'])
    if logoFeature in response:
        logos = response[logoFeature]
        print("LOGOS:")
        for logo in logos:
            print(logo['description'])
            
        
