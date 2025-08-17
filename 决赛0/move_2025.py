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
    def __init__(self, _stm32_port: str, _stm32_baudrate: int, cam_index: int) -> None:
        self.stm32_port = _stm32_port
        self.stm32_baudrate = _stm32_baudrate
        self.cam = cam_index

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
    def adjustCircle(self, thresh=0.01, dis_max_y=90, dis_max_x=110, timeout=30):
        #t1 = time.time()
        while True:
            d_x, d_y = self.downward_detection.get_circle_center()
            print(d_x, d_y)
            if abs(d_y) > thresh:
                self.moveControl.move_in_mm(y=d_y * dis_max_y)
                #print(f"移动了{d_x * dis_max}mm")
                #continue
            if abs(d_x) > thresh:
                self.moveControl.move_in_mm(x=-d_x * dis_max_x)
            if abs(d_x) < thresh and abs(d_y) < thresh:
                break
            #if time.time() - t1 > timeout:
                #break
        self.moveControl.move_in_mm(y=-1)
        self.moveControl.move_in_mm(x=-2)

    # 精加工区域码垛，根据物料块圆心位置，调整小车的X、Y位置
    def adjustColorCircle(self, thresh=0.04, dis_max=60, timeout=5):
        t1 = time.time()
        while True:
            d_x, d_y = self.downward_detection.get_colored_circle_center()
            if abs(d_y) > thresh:
                self.moveControl.move_in_mm(y=d_y * dis_max)
                #print(-dx * dis_max)
                continue
            if abs(d_x) > thresh:
                self.moveControl.move_in_mm(x=-d_x * dis_max * 0.75)
            if abs(d_x) < thresh and abs(d_y) < thresh:
                break
            if time.time() - t1 > timeout:
                break
        #self.moveControl.move_in_mm(y=8)
        #self.moveControl.move_in_mm(x=10)

    def catch(self, task_color_list):
        self.moveControl.set_distance(x=-0.03, y=-0.02)
        self.moveControl.adjustHeight(target_height=HeightMode.qrPos)
        #self.adjustCircle()
        self.moveControl.move_in_mm(y=10)
        # 真实颜色列表
        color_list_real = ['']

        # 第一次颜色识别
        print("detect 1")
        color_middle = self.downward_detection.detect_color_new()
        print(color_middle)
        color_list_real.append(color_middle)
        self.moveControl.set_distance(x=-0.13)

        # 第二次颜色识别
        print("detect 2")
        color_right = self.downward_detection.detect_color_new()
        print(color_right)
        color_list_real.append(color_right)

        # 排除出第三次颜色
        color_left = list(set(task_color_list) - set(color_list_real))[0]
        print(color_left)

        # 重构为从左到右的颜色列表
        color_list_real[0] = color_left
        color_list_real[1] = color_middle
        color_list_real[2] = color_right

        # 当前颜色为最右侧的颜色
        current_color = color_right

        # 三次抓取
        for i, color in enumerate(task_color_list):
            current_index = color_list_real.index(current_color)
            next_index = color_list_real.index(color)

            dis2move = -(next_index - current_index) * dis_between_every_circle
            self.moveControl.set_distance(x=dis2move)
            self.moveControl.grubBlockFromGround()

            current_color = color
            if i == 2:
                dis2red = dis_between_every_circle * (2 - color_list_real.index(current_color))
                red2corner = 0.7
                # 前往粗加工和暂存区之间的拐角
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.rawAreaLeave,
                                                             move_dis=-(dis2red + red2corner))

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
        #self.moveControl.turn_left()
        #self.moveControl.turn_left()
        #self.moveControl.adjust_rotate()
        #exit(0)
        #self.moveControl.notice_qr_info()
        #qr_info = self.moveControl.get_qrPos()
        #task1_color, task2_color = self.get_taskinfo(qr_info)
        #self.log(f'二维码识别结果为，任务1: {task1_color}, 任务2: {task2_color}')
        #exit(0)
        #task = ['red', 'green', 'blue']
        #for i, color in enumerate(task):
        #    if self.downward_detection.detect_colored_circle(task[i]):
        #        self.moveControl.putBlockToRaw()
        #exit(0)
        #self.moveControl.back_home()
        #task = ['red', 'gree', 'blue']
        #self.catch(task)
        #exit(0)
        #for i in range(10):
            #self.moveControl.turn_left()
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
        # self.moveControl.wait_for_start_cmd()
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
        self.moveControl.rotate_reset()
        self.moveControl.set_distance(y=0.11)
        # self.moveControl.adjustHeight(target_height=HeightMode.qrPos)
        # self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=1)
        self.moveControl.set_distance(x=1.55)
        # 在二维码区识别二维码
        self.log(f'通知下位机识别二维码')
        #self.moveControl.notice_qr_info()
        #qr_info = self.moveControl.get_qrPos()
        qr_info = "123+213"
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
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=-0.5)
        
        # self.moveControl.set_distance(x=-0.4)
        self.moveControl.turn_left()
        self.moveControl.set_distance(x=1.77)
        
        # 根据任务一的顺序移动小车，并摆放物料块
        current_color = color_list_in_rough_area[1]  # 小车现在应该处于中间色块
        self.moveControl.turn_left()

        self.catch(task1_color)


        # ---------------------------------- 2.前往暂存区，将物料块放到暂存区的地面 ---------------------------------- #
        self.log(f'第一圈任务：4.前往暂存区，将物料块放到暂存区的地面')

        # -------- 前往暂存区 ----------- #

        dis2blue = 0.75  # 拐角到暂存区蓝色物料块圆环的距离
        dis2first_block = dis_between_every_circle * color_list_in_rough_area.index(task1_color[0])

        self.moveControl.turn_right()
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=-(dis2blue + dis2first_block))

        current_color = task1_color[0]
        for i, color in enumerate(task1_color):
            current_index = color_list_in_restore_area.index(current_color)
            next_index = color_list_in_restore_area.index(color)
            if current_index == next_index:
                self.moveControl.adjustHeight(HeightMode.qrPos)
            else:
                dis2move = -(next_index - current_index) * dis_between_every_circle
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=dis2move)
            self.adjustCircle()
            self.moveControl.putBlockToCircle()
            current_color = color

        # ---------------------------------- 3.把放到暂存区的物料块拿回小车 ---------------------------------- #
        self.log(f'第一圈任务：3.将放到精加工的物块再放到小车上')

        # 按任务一的顺序，将精加工的物料搬到小车上
        for i, color in enumerate(task1_color):
            current_index = color_list_in_rough_area.index(current_color)
            next_index = color_list_in_rough_area.index(color)

            if current_index == next_index:
                self.moveControl.adjustHeight(HeightMode.circleArea)
            else:
                dis2move = -(next_index - current_index) * dis_between_every_circle
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.stackArea, move_dis=dis2move)
            # self.adjustCircle()
            self.moveControl.grubBlockFromGround()
            current_color = color

        # ---------------------------------- 4.离开暂存区，前往成品区 ------------------#
        self.log(f'第一圈任务：5.回到原料区，准备任务二')
        # 计算从当前位置到暂存区最中间物料块（绿色）的距离
        dis2restore_green = dis_between_every_circle * (1 - color_list_in_restore_area.index(current_color))
        self.moveControl.set_distance(x=-dis2restore_green)

        self.moveControl.turn_right()
        self.moveControl.set_distance(x=-1.75)
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=-0.01)  # 从拐角到原料区的距离
        self.moveControl.turn_right()
        
        # 识别转盘色环和放物料
        for i, color in enumerate(task1_color):
            if self.downward_detection.detect_colored_circle(task1_color[i]):
                self.moveControl.putBlockToRaw()
        exit(0)
        self.moveControl.set_distance(x=-0.98)
        self.moveControl.turn_right()
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.rawArea, move_dis=-0.90)
        # self.moveControl.adjustHeight(HeightMode.rawArea)
        # ----------------------------------  1.到原料区抓取物块 ---------------------------------- #
        self.log(f'第二圈任务：1.前往原料区，抓取物料块')

        self.catch(task2_color)

        # ---------------------------------- 2.前往暂存区，将物料块放到暂存区的地面 ---------------------------------- #
        self.log(f'第二圈任务：4.前往暂存区，将物料块放到暂存区的地面')

        # -------- 前往暂存区 ----------- #

        dis2blue = 0.75  # 拐角到暂存区蓝色物料块圆环的距离
        dis2first_block = dis_between_every_circle * color_list_in_rough_area.index(task2_color[0])

        self.moveControl.turn_right()
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=-(dis2blue + dis2first_block))

        current_color = task2_color[0]
        for i, color in enumerate(task2_color):
            current_index = color_list_in_restore_area.index(current_color)
            next_index = color_list_in_restore_area.index(color)
            if current_index == next_index:
                self.moveControl.adjustHeight(HeightMode.qrPos)
            else:
                dis2move = -(next_index - current_index) * dis_between_every_circle
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=dis2move)
            self.adjustCircle()
            self.moveControl.putBlockToCircle()
            current_color = color

        # ---------------------------------- 3.把放到暂存区的物料块拿回小车 ---------------------------------- #
        self.log(f'第一圈任务：3.将放到精加工的物块再放到小车上')

        # 按任务一的顺序，将精加工的物料搬到小车上
        for i, color in enumerate(task2_color):
            current_index = color_list_in_rough_area.index(current_color)
            next_index = color_list_in_rough_area.index(color)

            if current_index == next_index:
                self.moveControl.adjustHeight(HeightMode.circleArea)
            else:
                dis2move = -(next_index - current_index) * dis_between_every_circle
                self.moveControl.move_while_adjusting_height(mix_mode=MixMode.qrPos, move_dis=dis2move)
            # self.adjustCircle()
            self.moveControl.grubBlockFromGround()
            current_color = color

        # ---------------------------------- 3.离开暂存区，前往成品区 ------------------#
        self.log(f'第一圈任务：5.回到原料区，准备任务二')
        # 计算从当前位置到暂存区最中间物料块（绿色）的距离
        dis2restore_green = dis_between_every_circle * (1 - color_list_in_restore_area.index(current_color))
        self.moveControl.set_distance(x=-dis2restore_green)

        self.moveControl.turn_right()
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.rawArea, move_dis=-1.85)  # 从拐角到原料区的距离
        self.moveControl.turn_right()
        # 识别转盘色环和放物料
        for i, color in enumerate(task2_color):
            if self.downward_detection.detect_colored_circle(task2_color[i]):
                self.moveControl.putBlockToAnotherBlock()
            else:
                pass
        self.log(f'-------------- 任务执行完成！ --------------')


if __name__ == "__main__":
    # stm32_port = "COM4"
    stm32_port = "/dev/ttyUSB0"
    stm32_baudrate = 115200
    cam_name = 0

    com = ComRun(stm32_port, stm32_baudrate, cam_name)
    com.run()
