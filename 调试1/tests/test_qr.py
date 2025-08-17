import cv2 as cv
import pyzbar.pyzbar as pyzbar

# 扫码函数
def detect_camera_scan_QRcode(capture):
    barcodeData = ''
    while True:
        ret, frame = capture.read()
        if ret is True:
            image_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            barcodes = pyzbar.decode(image_gray)
            for barcode in barcodes:
                barcodeData = barcode.data.decode("utf-8")
            if len(barcodeData) == 7:
                return barcodeData
            if cv.waitKey(1) & 0xFF == 27:
                break
        else:
            continue


def order_1(capture):
    task = ''
    task = str(detect_camera_scan_QRcode(capture))
    return task

if __name__ == '__main__':
    cap = cv.VideoCapture(0)
    task = order_1(cap)
    print(task)