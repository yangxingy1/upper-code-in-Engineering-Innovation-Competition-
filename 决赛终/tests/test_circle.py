import cv2 as cv

cap = cv.VideoCapture(0)

while True:
    for i in range(5):
        ret, frame = cap.read()
    
    cv.imwrite('circle.png', frame)