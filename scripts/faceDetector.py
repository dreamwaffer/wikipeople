import cv2
import os

# Load the cascade
face_cascade = cv2.CascadeClassifier('models/haarcascade_frontalface_default.xml')

with os.scandir('pics') as dir:
    for picture in dir:
        if picture.name.endswith(".jpg"):
            img = cv2.imread(f'pics/{picture.name}') # Read the input image
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # Convert into grayscale
            faces = face_cascade.detectMultiScale(gray, 1.1, 5) # Detect faces
            print(picture.name)
            # print(len(faces))
            # Draw rectangle around the faces
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            # Display the output
            cv2.imshow('img', img)
            cv2.waitKey()
