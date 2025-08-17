from typing import Tuple
import numpy as np
import cv2 as cv
import math
from pyzbar.pyzbar import decode
from loguru import logger

from .config import color_list

# 输入两个点的坐标，获取两个点之间的距离，并取整
def Distance(x1, y1, x2, y2) -> int:
    x = abs(x1 - x2)
    y = abs(y1 - y2)
    return int(round(math.sqrt(x * x + y * y)))


# 图像识别类，包含摄像头的初始化以及后续的识别
class Detection(object):
    # 颜色矩阵
    lower_green = np.array([32, 69, 49])
    upper_green = np.array([84, 255, 255])
    lower_blue = np.array([0, 101, 0])
    upper_blue = np.array([37, 255, 255])
    lower_red = np.array([86, 90, 150])
    upper_red = np.array([180, 255, 255])

    def __init__(self, camera_index) -> None:
        self.camera_index = camera_index
        self.cap = cv.VideoCapture(camera_index)
        assert self.cap.isOpened(), print("摄像头打开失败")
        # print("摄像头初始化成功")
        # print("摄像头初始化成功")
        _, frame = self.cap.read()
        self.width = frame.shape[1]
        self.height = frame.shape[0]
        self.debug = False
        self.test = False
        self.cv_big_version = int(cv.__version__[0])

    def set_debug(self, whether_debug: bool):
        if whether_debug:
            self.debug = True
        else:
            self.debug = False

    def skip_some(self, count=5):
        for i in range(count):
            _, _ = self.cap.read()

    def detect_pyzbar(self):
        self.skip_some(count=2)
        _, img = self.cap.read()
        barcodes = decode(img)
        if barcodes is not None:
            if len(barcodes) == 1:
                barcode_data = barcodes[0].data.decode("utf-8")
                return barcode_data
            else:
                return 'k'

    # 返回圆心相对于图像中心的比例，x为正，表示圆心在中心右边，需右移
    # y为正，表示圆心在中心下边，需下移
    def get_circle_center(self) -> Tuple[float, float]:
        DeltaX = 0
        DeltaY = 0
        if self.test:
            return 0.0, 0.0
        self.skip_some()
        count = count_ori = 5
        D_X = []
        D_Y = []
        while True:
            _, img = self.cap.read()
            img = cv.medianBlur(img, 5)
            cimg = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            circles = cv.HoughCircles(
                cimg,
                cv.HOUGH_GRADIENT,
                1,
                100,
                param1=100,
                param2=50,
                minRadius=120,
                maxRadius=140,  #120-140 max
            )
            #circles = np.uint16(np.around(circles))
            #circle = circles[0, 1, :]
            #cv.circle(cimg, (circle[0], circle[1]), circle[2], (0, 255, 0), 2)
            #cv.circle(cimg, (circle[0], circle[1]), 2, (0, 0, 255), 3)
            #cv.imshow("i", cimg)
            #cv.waitKey()
            #cv.destroyAllWindows()
            # 判断霍夫检测是否检测到圆
            if not isinstance(circles, np.ndarray):
                print("no")
                if self.debug:
                    cv.imshow("frame", cimg)
                    k = cv.waitKey(1) & 0xFF
                    if k == 27:
                        break

                continue
            print(len(circles[0]))
            # 限制，当只有一个圆时
            if len(circles[0]) == 1:
                circles = np.uint16(np.around(circles))
                #print(circles.shape)
                circle = circles[0, 0, :]
                #print(circle.shape)
                #draw the outer circle
                cv.circle(cimg, (circle[0], circle[1]), circle[2], (0, 255, 0), 2)
                #draw the center of the circle
                cv.circle(cimg, (circle[0], circle[1]), 2, (0, 0, 255), 3)
                #cv.imshow("i", cimg)
                #cv.waitKey()
                #cv.destroyAllWindows()
                x, y = circle[0], circle[1]
                dx = (x - self.width / 2) / self.width * 2
                dy = (y - self.height / 2) / self.height * 2
                D_X.append(dx)
                D_Y.append(dy)
                count -= 1

            if self.debug:
                cv.imshow("frame", cimg)
                k = cv.waitKey(1) & 0xFF
                if k == 27:
                    break

            # 记录连续多次的圆心，取平均
            if count < 1:
                for dx, dy in zip(D_X, D_Y):
                    DeltaX += dx
                    DeltaY += dy
                if not self.debug:
                    break
                else:
                    print(DeltaX / len(D_X), DeltaY / len(D_Y))
                    count = count_ori

        return DeltaX / len(D_X), DeltaY / len(D_Y)

    def detect_color(self, color_detected:str) -> bool:
        self.skip_some()
        lower_color = None
        upper_color = None
        true_cont = 0
        if color_detected == "red":
            lower_color = self.lower_red
            upper_color = self.upper_red
        elif color_detected == "green":
            lower_color = self.lower_green
            upper_color = self.upper_green
        elif color_detected == "blue":
            lower_color = self.lower_blue
            upper_color = self.upper_blue
        else:
            print("!!没这个颜色")
        while True:
            # 读取图像
            _, frame = self.cap.read()
            cutted_frame = frame[240:480, 220:420]
            hsv_frame = cv.cvtColor(cutted_frame, cv.COLOR_RGB2HSV)
            # kernel = np.ones((5, 5), np.uint8)
            # erosion = cv.erode(hsv_frame, kernel, 5)
            img = cv.inRange(hsv_frame, lower_color, upper_color)

            if self.debug:
                cv.imshow("frame", frame)
                cv.imshow("cutted_frame", cutted_frame)
                cv.imshow("hsv_frame", hsv_frame)
                cv.imshow("after_hsv", img)
                k = cv.waitKey(1) & 0xFF
                if k == 27:
                    cv.destroyAllWindows()
                    break
            # 统计非零像素点的数量
            count = np.count_nonzero(img)
            print(f"像素点个数为:{count}")
            # 如果非零像素点数量大于阈值，认为颜色匹配
            threshold = 3500  # 这是一个可以调整的阈值
            if count > threshold:
                true_cont += 1
                if true_cont > 3:
                    return True
                    
    # 返回圆心相对于图像中心的比例，x为正，表示圆心在中心右边，需右移
    # y为正，表示圆心在中心下边，需下移
    def get_colored_circle_center(self, min_r=100) -> Tuple[float, float]:
        DeltaX = 0
        DeltaY = 0
        if self.test:
            return 0.0, 0.0
        self.skip_some()
        count = count_ori = 5
        D_X = []
        D_Y = []
        
        while True:
            _, img = self.cap.read()
            img = cv.medianBlur(img, 5)
            cimg = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            circles = cv.HoughCircles(
                cimg,
                cv.HOUGH_GRADIENT,
                1,
                800,
                param1=100,
                param2=30,
                minRadius=50,
                maxRadius=200,
            )

            # 判断霍夫检测是否检测到圆
            if not isinstance(circles, np.ndarray):
                print("no")
                if self.debug:
                    cv.imshow("frame", cimg)
                    k = cv.waitKey(1) & 0xFF
                    if k == 27:
                        break

                continue
            print(len(circles[0]))
            # 限制，当只有一个圆时
            circles = np.uint16(np.around(circles))
            #print(circles.shape)
            circle = circles[0, 0, :]
            #print(circle.shape)
            #draw the outer circle
            cv.circle(cimg, (circle[0], circle[1]), circle[2], (0, 255, 0), 2)
            #draw the center of the circle
            cv.circle(cimg, (circle[0], circle[1]), 2, (0, 0, 255), 3)
            #cv.imshow("i", cimg)
            #cv.waitKey()
            #cv.destroyAllWindows()
            x, y = circle[0], circle[1]
            dx = (x - self.width / 2) / self.width * 2
            dy = (y - self.height / 2) / self.height * 2
            D_X.append(dx)
            D_Y.append(dy)
            count -= 1
            if self.debug:
                cv.imshow("frame", cimg)
                k = cv.waitKey(1) & 0xFF
                if k == 27:
                    break
            print(count)
            # 记录连续多次的圆心，取平均
            if count < 1:
                for dx, dy in zip(D_X, D_Y):
                    DeltaX += dx
                    DeltaY += dy
                if not self.debug:
                    break
                else:
                    print(DeltaX / len(D_X), DeltaY / len(D_Y))
                    count = count_ori

        return DeltaX / len(D_X), DeltaY / len(D_Y)

    def detect_color_new(self):
        # 定义全色彩阈值列表
        lower_color_list = []
        upper_color_list = []
        # 赋值
        lower_color_list.append(self.lower_red)
        lower_color_list.append(self.lower_green)
        lower_color_list.append(self.lower_blue)
        upper_color_list.append(self.upper_red)
        upper_color_list.append(self.upper_green)
        upper_color_list.append(self.upper_blue)

        # 全色彩阈值列表中的颜色顺序
        color_list_ = ["red", "green", "blue"]

        # 结果列表
        result = []
        min_height = 180  # 色块的最小高度
        min_width = 100  # 色块的最小宽度
        # 开始识别 遍历每一种颜色
        for i in range(3):
            _, frame = self.cap.read()
            # 这里的图像裁剪注意一下，可能需要更改数据    或者在颜色识别前把摄像头紧贴物块   推荐使用后一种方法这样后续的颜色识别阈值也不需要更改
            cutted_frame = frame[240:480, 220:420]
            hsv_frame = cv.cvtColor(cutted_frame, cv.COLOR_RGB2HSV)
            img = cv.inRange(hsv_frame, lower_color_list[i], upper_color_list[i])
            if self.cv_big_version == 4:
                cnts, _ = cv.findContours(img, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
            else:
                raise RuntimeError("cv版本不对")

            if self.debug:
                cv.drawContours(cutted_frame, cnts, -1, (255, 0, 0), 2)
                cv.imshow("frame", frame)
                cv.imshow("cutted_frame", cutted_frame)
                cv.imshow("hsv_frame", hsv_frame)
                cv.imshow("after_hsv", img)
                k = cv.waitKey(1) & 0xFF
                if k == 27:
                    cv.destroyAllWindows()
                    break

            # 统计非零像素点的数量
            count = np.count_nonzero(img)
            print(f"像素点个数为:{count}")
            # 如果非零像素点数量大于阈值，认为颜色匹配
            threshold = 1900  # 这是一个可以调整的阈值
            if count > threshold:
                return color_list_[i]

    def __del__(self):
        logger.info('摄像头检测类销毁')
        self.cap.release()
        del self.cap


if __name__ == "__main__":
    cap_index = 0  # 摄像头索引
    detect = Detection(0)
    detect.set_debug(True)  # 调试模式，会把检测结果显示出来，设置为False的话就不会有图像显示

    # 所有的识别都是通过按下ESC退出，然后进入下一阶段

    # 颜色识别
    for color_now in ["red", "green", "blue"]:
        detect.detect_color(color_now)

    # for color in ["red", "green", "blue"]:
    #     detect.get_colored_circle_center(color)

    # # 二维码识别
    # info = detect.get_qr_info(data_len=7)  # 超时时间，20s内没有读取到就退出
    # print(info)

    # # 圆心检测
    # dx, dy = detect.get_circle_center()
    # print("x方向误差{0}, y方向误差{1}".format(dx, dy))

    # # 直线检测
    # k, d_y = detect.get_line_info()
    # print("检测到直线斜率{0}, y方向与中心差值{1}".format(k, d_y))
