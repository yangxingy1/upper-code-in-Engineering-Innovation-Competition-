import time
from loguru import logger

from models.Detection import Detection
from models.MoveControl import MoveControl
from models.config import (
    color_list,
    color_list_in_rough_area,
    color_list_in_restore_area,
    dis_between_every_circle,
    HeightMode,
    MixMode,
)



class ComRun:
    def __init__(self, _stm32_port: str, _stm32_baudrate: int, cam_index: str) -> None:
        self.stm32_port = _stm32_port
        self.stm32_baudrate = _stm32_baudrate
        self.cam = cam_index
        print(self.cam)
        self.moveControl = MoveControl(self.stm32_port, self.stm32_baudrate)
        self.downward_detection = Detection(self.cam)
        self.log('串口和摄像头初始化完成')

    # 获取二维码信息
    @staticmethod
    def get_taskinfo(qr_result: str) -> tuple[list[str], list[str]]:
        if len(qr_result) != 7:
            raise ValueError

        task1_num = [int(task_str) for task_str in qr_result[:3]]
        task2_num = [int(task_str) for task_str in qr_result[4:]]

        task1_colors = [color_list[i] for i in task1_num]
        task2_colors = [color_list[i] for i in task2_num]

        return task1_colors, task2_colors

    # 根据圆心调整小车X，Y位置
    def adjustCircle(self, thresh=0.007, dis_max_y=90, dis_max_x=110, timeout=30):
        #t1 = time.time()
        while True:
            d_x1, d_y1 = self.downward_detection.get_circle_center()
            print(d_x1, d_y1)
            if abs(d_y1) > thresh:
                self.moveControl.move_in_mm(y=d_y1 * dis_max_y)
                #print(f"移动了{d_x * dis_max}mm")
                #continue
            if abs(d_x1) > thresh:
                self.moveControl.move_in_mm(x=-d_x1 * dis_max_x)
            if abs(d_x1) < thresh and abs(d_y1) < thresh:
                break
            #if time.time() - t1 > timeout:
                #break
        self.moveControl.move_in_mm_new(y=-0.5)
        self.moveControl.move_in_mm_new(x=-3.1)
        
    def adjustCircle_new(self, thresh=0.007, dis_max_y=90, dis_max_x=110, timeout=30):
        #t1 = time.time()
        while True:
            d_x1, d_y1 = self.downward_detection.get_circle_center()
            print(d_x1, d_y1)
            if abs(d_y1) > thresh:
                self.moveControl.move_in_mm(y=d_y1 * dis_max_y)
                #print(f"移动了{d_x * dis_max}mm")
                #continue
            if abs(d_x1) > thresh:
                self.moveControl.move_in_mm(x=-d_x1 * dis_max_x)
            if abs(d_x1) < thresh and abs(d_y1) < thresh:
                break
            #if time.time() - t1 > timeout:
                #break
        self.moveControl.move_in_mm_new(y=-0.9)
        self.moveControl.move_in_mm_new(x=-3.1)

    # 精加工区域码垛，根据物料块圆心位置，调整小车的X、Y位置
    def adjustColorCircle(self, thresh=0.02, dis_max=60, timeout=100):
        t1 = time.time()
        while True:
            d_x, d_y = self.downward_detection.get_colored_circle_center()
            print(d_x, d_y)
            if abs(d_y) > thresh:
                self.moveControl.move_in_mm(y=d_y * 70)
                #print(-dx * dis_max)
            if abs(d_x) > thresh:
                self.moveControl.move_in_mm(x=-d_x * 60)
            if abs(d_x) < thresh and abs(d_y) < thresh:
                break
            if time.time() - t1 > timeout:
                break
        #self.moveControl.move_in_mm(y=8)
        #self.moveControl.move_in_mm(x=10)
    def test1(self):
        self.moveControl.wait_for_start_cmd()
        self.moveControl.notice_qr_info()     
        self.moveControl.rotate_reset()
        self.moveControl.set_distance(y=0.13)
        self.moveControl.set_distance(x=0.82)
        time.sleep(2)
        self.log(f'通知下位机识别二维码') 

        qr_info = self.moveControl.get_qrPos()
        task1_color, task2_color = self.get_taskinfo(qr_info)
        self.log(f'二维码识别结果为，任务1: {task1_color}, 任务2: {task2_color}')
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=0.63)
        self.moveControl.set_distance(y=-0.04)
        print(task1_color)
        for i, color in enumerate(task1_color):
            self.moveControl.adjustHeight(target_height=HeightMode.rawArea)
            self.downward_detection.detect_color(color)
            if i == 2:
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.rawAreaLeave, move_dis=-0.4)
                break
            self.moveControl.grubBlockFromRawArea()
        exit(0)
        
    def test2(self):
        task1_color = ["red", "green", "blue"]
        current_color = "green"
        self.moveControl.adjustHeight(target_height=HeightMode.circleArea)
        for i, color in enumerate(task1_color):
            current_index = color_list_in_rough_area.index(current_color)
            next_index = color_list_in_rough_area.index(color)
            if current_index == next_index:
                self.moveControl.adjustHeight(HeightMode.qrPos)
            else:
                dis2move = -(next_index - current_index) * dis_between_every_circle
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=dis2move)
            print("begin to adjust circles")
            self.adjustCircle()
            print("finish")
            self.moveControl.putBlockToCircle()

            current_color = color
        self.log(f'第一圈任务：3.将放到粗加工的物块再放到小车上')

        # 移动到1
        current_index = color_list_in_rough_area.index(current_color)
        first_index = color_list_in_rough_area.index(task1_color[0])
        dis = -(first_index - current_index) * 0.15
        self.moveControl.set_distance(x=dis)
        # 抓1移动到2
        current_color = task1_color[0]
        next_color = task1_color[1]
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)
        # 抓2移动到3
        current_color = task1_color[1]
        next_color = task1_color[2]
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)
        # 抓3走 计算到红色的距离
        current_color = task1_color[2]
        next_color = "red"
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15
        red2corner = -0.7
        dis = red2corner + dis
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)
        exit(0)

    def test3(self):
        self.moveControl.adjustHeight(target_height=HeightMode.circleArea)
        task2_color = ["red","green","blue"]
        current_color = "green"
        for i, color in enumerate(task2_color):
            current_index = color_list_in_rough_area.index(current_color)
            next_index = color_list_in_rough_area.index(color)
            if current_index == next_index:
                self.moveControl.adjustHeight(HeightMode.qrPos)
            else:
                dis2move = -(next_index - current_index) * dis_between_every_circle
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=dis2move)
            print("begin to adjust circles")
            self.adjustCircle()
            print("finish")
            self.moveControl.putBlockToCircle()

            current_color = color 
        exit(0)
        
    def test4(self):
        self.moveControl.adjustHeight(target_height=HeightMode.stackArea)
        task2_color = ["red", "green", "blue"]
        self.adjustColorCircle()
        self.moveControl.highUp()
        current_color = task2_color[0]
        # 放1走到2
        current_index = color_list_in_restore_area.index(current_color)
        next_index = color_list_in_restore_area.index(task2_color[1])
        dis = -(next_index - current_index) * dis_between_every_circle
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave,move_dis=dis)
        # 放2走到3
        current_index = color_list_in_restore_area.index(task2_color[1])
        next_index = color_list_in_restore_area.index(task2_color[2])
        dis = -(next_index - current_index) * dis_between_every_circle
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave,move_dis=dis)      
        # 放3走到拐角
        dis2restore_red = dis_between_every_circle * (2 - color_list_in_restore_area.index(task2_color[2]))
        dis2corner2 = 0.75
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave, move_dis=-(dis2restore_red + dis2corner2))
        exit(0)
        
    @staticmethod
    def continueOrNot():
        x = input('是否继续程序:')
        if x == 'y' or x == 'Y':
            pass
        else:
            exit(0)

    @staticmethod
    def log(msg: str) -> None:
        logger.info(msg)

    def run(self):
        #self.adjustCircle()
        #exit(0)
        #————————————————————————————————————————————test1----start-car-----------------------
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=0.00)
        self.moveControl.adjustHeight(target_height=HeightMode.circleArea)
        #self.adjustCircle()
        #self.moveControl.putBlockToCircle()
        #exit(0)
        #self.test1()
        #-------------------------------------------------------------------------------------
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=0.00)
        #self.moveControl.adjustHeight(target_height=HeightMode.circleArea)
        #self.adjustCircle()
        #exit(0)
        #--------------------------------------------test2----circle-area-1-------------------
        #self.test2()
        #-------------------------------------------------------------------------------------       
        #--------------------------------------------test3----circle-area-2-------------------
        self.test3()
        #--------------------------------------------test3----circle-area-2-------------------
        #--------------------------------------------test4----stack-area----------------------
        #self.test4()
        #-------------------------------------------------------------------------------------
        #self.moveControl.adjustHeight(target_height=HeightMode.stackArea)
        #task2_color = ["red", "green", "blue"]
        #self.adjustColorCircle()
        #self.moveControl.highUp()
        #current_color = task2_color[0]
        # 放1走到2
        #current_index = color_list_in_restore_area.index(current_color)
        #next_index = color_list_in_restore_area.index(task2_color[1])
        #dis = -(next_index - current_index) * dis_between_every_circle
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave,move_dis=dis)
        # 放2走到3
        #current_index = color_list_in_restore_area.index(task2_color[1])
        #next_index = color_list_in_restore_area.index(task2_color[2])
        #dis = -(next_index - current_index) * dis_between_every_circle
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave,move_dis=dis)      
        # 放3走到拐角
        #dis2restore_red = dis_between_every_circle * (2 - color_list_in_restore_area.index(task2_color[2]))
        #dis2corner2 = 0.75
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave, move_dis=-(dis2restore_red + dis2corner2))
        #exit(0)
        #self.moveControl.adjustHeightOrderHeight(height=85)
        #exit(0)
        #self.moveControl.rotate_reset()
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave, move_dis=0.3)
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave, move_dis=0.3)
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave, move_dis=0.3)
        
        #exit(0)
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=0.00)
        #self.moveControl.adjustHeight(target_height=HeightMode.circleArea)
        #task1_color = ['red', 'green', 'blue']
        #current_color = 'green'
        #for i, color in enumerate(task1_color):
        #    current_index = color_list_in_rough_area.index(current_color)
        #    next_index = color_list_in_rough_area.index(color)
        #    if current_index == next_index:
        #        self.moveControl.adjustHeight(HeightMode.qrPos)
        #    else:
        #        dis2move = -(next_index - current_index) * dis_between_every_circle
        #        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=dis2move)
        #    print("begin to adjust circles")
        #    self.adjustCircle()
        #    print("finish")
        #    self.moveControl.putBlockToCircle()
        #    current_color = color
        #exit(0)
        #self.moveControl.notice_qr_info()
        #self.moveControl.set_distance(x=0.20)
        #qr_info = self.moveControl.get_qrPos()
        #print(qr_info)
        #task1_color, task2_color = self.get_taskinfo(qr_info)
        #exit(0)
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=0.15)
        #exit(0)
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=0.0)
        #self.moveControl.adjustHeight(target_height=HeightMode.circleArea)
        #self.adjustColorCircle()
        #self.moveControl.putBlockToAnotherBlock()
        #exit(0)
        #self.moveControl.rotate_reset()    
        #self.moveControl.set_distance(x=1.8)
        #self.moveControl.set_distance(x=0.9)
        #self.moveControl.rotate_adjust()
        #time.sleep(5)
        #self.moveControl.set_distance(x=0.9)
        #self.moveControl.turn_right()
        #self.moveControl.set_distance(x=1.8)
        #self.moveControl.turn_right()
        #self.moveControl.set_distance(x=1.8)
        #self.moveControl.turn_right()
        #self.moveControl.rotate_adjust()
        
        #exit(0)
        #self.moveControl.notice_qr_info()
        #qr_info = self.moveControl.get_qrPos()
        #task1_color, task2_color = self.get_taskinfo(qr_info)
        #print(task1_color, task2_color)
        #exit(0)
        #for i in range(10):
        #    self.moveControl.turn_left()
        #exit(0)
        #self.moveControl.adjustHeight(target_height=HeightMode.circleArea)
        #self.adjustCircle_new()
        #self.moveControl.putBlockToCircle()
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=0.0)
        #exit(0)
        #self.moveControl.adjustHeight(target_height=HeightMode.circleArea)
        #self.moveControl.rotate_reset()
        #self.moveControl.set_distance(x=-0.45)
        #self.moveControl.rotate_adjust()
        #for i in range(3):
        #    self.moveControl.adjustHeight(target_height=HeightMode.circleArea)
        #    self.adjustCircle()
        #    self.moveControl.putBlockToCircle()
        #    self.moveControl.set_distance(x=0.15)
        #self.moveControl.putBlockToCircle()
        #self.moveControl.rotate_reset()
        #self.moveControl.set_distance(x=1.00)
        #self.moveControl.rotate_adjust()
        #exit(0)
        #exit(0)
        #self.moveControl.adjustHeight(target_height=HeightMode.stackArea)
        #self.adjustColorCircle()
        #self.moveControl.putBlockToAnotherBlock()
        #exit(0)
        #self.adjustCircle()
        #exit(0)
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=0.01)
        #self.moveControl.adjustHeight(target_height=HeightMode.stackArea)
        #exit(0)
        #self.adjustCircle()
        #self.moveControl.putBlockToCircle()
        #exit(0)
        # self.moveControl.notice_qr_info()
        # qr_info = self.moveControl.get_qrPos()
        # task1_color, task2_color = self.get_taskinfo(qr_info)
        # print(task1_color,task2_color)
        # .
        # exit(0)
        # 
        # self.moveControl.move_in_mm()
        # self.moveControl.adjustHeight(target_height=HeightMode.qrPos)
        # self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=0.20)
        # exit(0)

        # ---------------------------------------------------------------------------------------- #
        # 前置任务：                                                                               #
        #         1. 机器人移动到二维码区，识别二维码信息，从而获取两次拿取物料块的顺序             # 
        # -----------------------------------------------------------------------------------------#

        self.log(f'------------- 小车运行前置任务，移动到二维码并扫描二维码信息 -------------------')
        # ----------------------------------- 1.读取二维码信息 ----------------------------------- #
        # 前往二维码
        self.log(f'前往二维码')
        self.moveControl.wait_for_start_cmd()
        self.moveControl.notice_qr_info()     
        #self.moveControl.wait_for_start_cmd()
        self.moveControl.rotate_reset()
        self.moveControl.set_distance(y=0.13)
        #self.notice_qr_info()
        # self.moveControl.adjustHeight(target_height=HeightMode.qrPos)
        self.moveControl.set_distance(x=0.85)
        time.sleep(2)
        # 在二维码区识别二维码
        self.log(f'通知下位机识别二维码')
        #self.moveControl.notice_qr_info()  

        qr_info = self.moveControl.get_qrPos()
        #qr_info = '213+132'
        task1_color, task2_color = self.get_taskinfo(qr_info)
        self.log(f'二维码识别结果为，任务1: {task1_color}, 任务2: {task2_color}')


        # ---------------------------------------------------------------------------------------  #
        # 第一圈任务：                                                                             #
        #           1.前往原料区，抓取物料块
        #           2.前往粗加工区，放料块
        #           3.将放到粗加工的物块再放到小车上
        #           4.前往暂存区，将物料块放到暂存区的地面
        #           5.回到原料区，准备任务二
        # ---------------------------------------------------------------------------------------- #

        self.log(f'-------------- 小车运行第一圈的任务 --------------')
        # ----------------------------------  1.到原料区抓取物块 ---------------------------------- #
        self.log(f'第一圈任务：1.前往原料区，抓取物料块')
        # 前往原料区
        # self.moveControl.adjustHeight(target_height=HeightMode.rawArea)
        # self.moveControl.set_distance(x=0.95)
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=0.60)
        self.moveControl.set_distance(y=-0.04)
        print(task1_color)
        # 调整高度，识别颜色，抓取物块
        for i, color in enumerate(task1_color):
            self.moveControl.adjustHeight(target_height=HeightMode.rawArea)
            self.downward_detection.detect_color(color)
            if i == 2:
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.rawAreaLeave, move_dis=-0.4)
                break
            self.moveControl.grubBlockFromRawArea()

        # ----------------------------------  2.到粗加工区放料块 ---------------------------------- #
        self.log(f'第一圈任务：2.前往粗加工区，放料块')
        # 前往粗加工区
        # self.moveControl.set_distance(x=-0.4)
        self.moveControl.set_distance(y=0.03)
        self.moveControl.turn_left()
        self.moveControl.set_distance(x=1.78)
        # 根据任务一的顺序移动小车，并摆放物料块
        current_color = color_list_in_rough_area[1]  # 小车现在应该处于中间色块
        self.moveControl.turn_together(77)

        # 此时车头朝向粗加工区蓝色物料块方向，车尾朝向红色物料块方向
        self.moveControl.rotate_adjust()
        for i, color in enumerate(task1_color):
            current_index = color_list_in_rough_area.index(current_color)
            next_index = color_list_in_rough_area.index(color)
            if current_index == next_index:
                self.moveControl.adjustHeight(HeightMode.qrPos)
            else:
                dis2move = -(next_index - current_index) * dis_between_every_circle
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=dis2move)
            print("begin to adjust circles")
            self.adjustCircle()
            print("finish")
            self.moveControl.putBlockToCircle()

            current_color = color

        # ---------------------------------- 3.把放到粗加工区的物料块拿回小车 ---------------------------------- #
        self.log(f'第一圈任务：3.将放到粗加工的物块再放到小车上')

        # 移动到1
        current_index = color_list_in_rough_area.index(current_color)
        first_index = color_list_in_rough_area.index(task1_color[0])
        dis = -(first_index - current_index) * 0.15
        self.moveControl.set_distance(x=dis)
        # 抓1移动到2
        current_color = task1_color[0]
        next_color = task1_color[1]
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)
        # 抓2移动到3
        current_color = task1_color[1]
        next_color = task1_color[2]
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)
        # 抓3走 计算到红色的距离
        current_color = task1_color[2]
        next_color = "red"
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15
        red2corner = -0.7
        dis = red2corner + dis
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)


        # ---------------------------------- 4.前往暂存区，将物料块放到暂存区的地面 ---------------------------------- #
        self.log(f'第一圈任务：4.前往暂存区，将物料块放到暂存区的地面')

        # -------- 前往暂存区 ----------- #

        dis2blue = 0.75  # 拐角到暂存区蓝色物料块圆环的距离
        dis2first_block = dis_between_every_circle * color_list_in_rough_area.index(task1_color[0])

        self.moveControl.turn_right()
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=-(dis2blue + dis2first_block))

        current_color = task1_color[0]
        self.moveControl.rotate_adjust()
        for i, color in enumerate(task1_color):
            current_index = color_list_in_restore_area.index(current_color)
            next_index = color_list_in_restore_area.index(color)
            if current_index == next_index:
                self.moveControl.adjustHeight(HeightMode.qrPos)
            else:
                dis2move = -(next_index - current_index) * dis_between_every_circle
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=dis2move)
            self.adjustCircle_new()
            self.moveControl.putBlockToCircle()
            current_color = color


        # ---------------------------------- 5.离开暂存区，前往原料区 ------------------#
        self.log(f'第一圈任务：5.回到原料区，准备任务二')
        # 计算从当前位置到暂存区最右边物料块（红色）的距离
        dis2restore_red = dis_between_every_circle * (2 - color_list_in_restore_area.index(current_color))
        dis2corner2 = 0.78
        self.moveControl.set_distance(x=-(dis2corner2 + dis2restore_red))

        self.moveControl.turn_right()
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.rawArea, move_dis=-0.45)  # 从拐角到原料区的距离
        # self.moveControl.set_distance(x=-0.4)
        # self.moveControl.adjustHeight(HeightMode.rawArea)

        # -------------------------------------------------------------------------------------- #
        # 任务二：
        #       1.在原料区按任务二顺序取物料块
        #       2.将物料块搬运到粗加工
        #       3.将物料块搬运到暂存区
        #       4.将物料块搬运到粗加工并进行码垛
        # -------------------------------------------------------------------------------------- #

        self.log(f'-------------- 小车运行第二圈的任务 --------------')
        # ----------------------------------  1.在原料区抓取物块 ---------------------------------- #
        self.log(f'第二圈任务：1.在原料区抓取物块')
        # 调整高度，识别颜色，抓取物块
        for i, color in enumerate(task2_color):
            self.moveControl.adjustHeight(target_height=HeightMode.rawArea)
            self.downward_detection.detect_color(color)
            if i == 2:
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.rawAreaLeave, move_dis=-0.42)
                break
            self.moveControl.grubBlockFromRawArea()


        # ----------------------------------  2.将物料块放到粗加工区 ---------------------------------- #
        self.log(f'第二圈任务：2.将物料块放到粗加工区')
        # 前往粗加工区
        # self.moveControl.set_distance(x=-0.4)
        self.moveControl.turn_left()
        self.moveControl.set_distance(x=1.78)
        # 根据任务二的顺序移动小车，并摆放物料块
        current_color = color_list_in_rough_area[1]  # 小车现在应该处于中间色块
        self.moveControl.turn_together(77)
        self.moveControl.rotate_adjust()
        # 此时车头朝向粗加工区蓝色物料块方向，车尾朝向红色物料块方向
        for i, color in enumerate(task2_color):
            current_index = color_list_in_rough_area.index(current_color)
            next_index = color_list_in_rough_area.index(color)
            if current_index == next_index:
                self.moveControl.adjustHeight(HeightMode.qrPos)
            else:
                dis2move = -(next_index - current_index) * dis_between_every_circle
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=dis2move)
            print("begin to adjust circles")
            self.adjustCircle()
            print("finish")
            self.moveControl.putBlockToCircle()

            current_color = color

        # ---------------------------------- 3.把放到粗加工区的物料块拿回小车 ---------------------------------- #
        self.log(f'第二圈任务：3.把放到粗加工区的物料块拿回小车')
        # 按任务二的顺序，将粗加工的物料搬到小车上
        # 移动到1
        current_index = color_list_in_rough_area.index(current_color)
        first_index = color_list_in_rough_area.index(task2_color[0])
        dis = -(first_index - current_index) * 0.15
        self.moveControl.set_distance(x=dis)
        # 抓1移动到2
        current_color = task2_color[0]
        next_color = task2_color[1]
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)
        # 抓2移动到3
        current_color = task2_color[1]
        next_color = task2_color[2]
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)
        # 抓3走 计算到红色的距离
        current_color = task2_color[2]
        next_color = "red"
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15
        red2corner = -0.7
        dis = red2corner + dis
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)
                

        # ---------------------------------- 4.前往暂存区，将新的物料块码垛到任务一的物料块上 ---------------------------------- #
        self.log(f'第二圈任务：4.将物料块码垛到任务一的物料块上')
        # -------- 前往暂存区 ----------- #
        # 计算从当前位置到粗加工红色物料块的距离
        # dis2red = dis_between_every_circle * (2 - color_list_in_rough_area.index(current_color))
        # red2corner = 0.8
        # 前往粗加工和暂存区之间的拐角
        # self.moveControl.set_distance(x=-(dis2red + red2corner))

        dis2blue = 0.73  # 拐角到暂存区蓝色物料块圆环的距离
        dis2first_block = dis_between_every_circle * color_list_in_rough_area.index(task2_color[0])
        
        self.moveControl.turn_right()
        #self.moveControl.set_distance(x=-(dis2blue + dis2first_block))
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=-(dis2blue + dis2first_block))
        self.moveControl.rotate_adjust()
        self.adjustColorCircle()
        self.moveControl.highUp()
        current_color = task2_color[0]
        # 放1走到2
        current_index = color_list_in_restore_area.index(current_color)
        next_index = color_list_in_restore_area.index(task2_color[1])
        dis = -(next_index - current_index) * dis_between_every_circle
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave,move_dis=dis)
        # 放2走到3
        current_index = color_list_in_restore_area.index(task2_color[1])
        next_index = color_list_in_restore_area.index(task2_color[2])
        dis = -(next_index - current_index) * dis_between_every_circle
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave,move_dis=dis)      
        # 放3走到拐角
        dis2restore_red = dis_between_every_circle * (2 - color_list_in_restore_area.index(task2_color[2]))
        dis2corner2 = 0.75
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave, move_dis=-(dis2restore_red + dis2corner2))
                 
        #for i, color in enumerate(task2_color):
        #    current_index = color_list_in_restore_area.index(current_color)
        #    next_index = color_list_in_restore_area.index(color)
        #    dis2move = -(next_index - current_index) * dis_between_every_circle
            
            # self.moveControl.adjustHeight(HeightMode.stackArea)
       #     if i == 0:
       #         self.adjustColorCircle()
       #     current_color = color
       #     if i == 2:
       #         dis2restore_red = dis_between_every_circle * (2 - color_list_in_restore_area.index(current_color))
       #         dis2corner2 = 0.75
       #         self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave, move_dis=-(dis2restore_red + dis2corner2))
       #         break
       #     self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackAreaLeave,move_dis=dis2move)
            #self.moveControl.putBlockToAnotherBlock()
            

        # ------------------------------------------------------------------------------------------ #
        # 结束任务：
        #         1.小车从暂存区回到启停区
        # ------------------------------------------------------------------------------------------ #
        self.log(f'-------------- 小车执行最后的任务：回到启停区 --------------')

        self.moveControl.turn_right()
        self.moveControl.set_distance(x=-1.89)
        self.moveControl.set_distance(y=-0.26)

        self.log(f'-------------- 任务执行完成！ --------------')


if __name__ == "__main__":
    # stm32_port = "COM4"
    stm32_port = "/dev/ttyUSB0"
    stm32_baudrate = 115200
    cam_name = 0

    com = ComRun(stm32_port, stm32_baudrate, cam_name)
    com.run()
