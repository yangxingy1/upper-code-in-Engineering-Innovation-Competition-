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
    def adjustColorCircle(self, thresh=0.05, dis_max=60, timeout=100):
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

        dis2red = dis_between_every_circle * (2 - color_list_real.index(current_color))
        red2corner = 0.7
        self.moveControl.set_distance(x=-(dis2red + red2corner))
        self.moveControl.set_distance(y=0.02)

    def putToTurn(self, task_color:list):
        for color in task_color:
            index = color_list_in_rough_area.index(color)
            while True:
                mes = self.downward_detection.detect_pyzbar()
                if mes == 'k':
                    pass
                elif mes == str(index):
                    self.moveControl.putBlockToTurn()
                    break
                else:
                    pass

    def putToTurn_2(self, task_color):
        for color in task_color:
            index = color_list.index(color)
            while True:
                mes = self.downward_detection.detect_pyzbar()
                if mes == 'k':
                    pass
                elif mes == str(index):
                    self.moveControl.putBlockToStack()
                    break
                else:
                    pass

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
        #color_middle = self.downward_detection.detect_color_new()
        #print(color_middle)
        #exit(0)
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.start_car, move_dis=0.00)
        #self.moveControl.adjustHeight(target_height=HeightMode.circleArea)
        #self.adjustColorCircle()
        #self.moveControl.grubBlockFromGround()
        #self.moveControl.putBlockToCircle()
        #self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=0.03)
        #self.moveControl.putBlockToTurn()
        #exit(0)
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
        self.moveControl.rotate_reset()
        self.moveControl.set_distance(y=0.18)
        self.moveControl.set_distance(x=1.63)
        time.sleep(2)
        qr_info = self.moveControl.get_qrPos()
        # qr_info = '213+132'
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
        self.moveControl.set_distance(x=-0.55)
        self.moveControl.turn_left()
        self.moveControl.set_distance(x=1.68)
        current_color = color_list_in_rough_area[1]  # 小车现在应该处于中间色块
        self.moveControl.turn_together(77)
        self.adjustColorCircle()
        # 抓取并移动到拐角
        self.catch(task1_color)


        # ----------------------------------  2.到精加工区放 ---------------------------------- #
        # -------- 前往暂存区 ----------- #

        dis2blue = 0.73  # 拐角到暂存区蓝色物料块圆环的距离
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



        # ----------------------------------  3.在精加工区取走 ---------------------------------- #
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
        # 抓3走 计算到绿色的距离
        current_color = task1_color[2]
        next_color = "green"
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15

        # ----------------------------------  4.前往成品区，在成品区放 ---------------------------------- #
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)
        self.moveControl.turn_right()
        self.moveControl.set_distance(x=-1.78)

        self.moveControl.turn_together2(-77)
        # 放第一轮物块
        self.putToTurn(task1_color)
        # ---------------------------------------------------------------------------------------  #
        # 第二圈任务：                                                                             #
        #           1.前往原料区，抓取物料块
        #           2.前往粗加工区，放料块
        #           3.将放到粗加工的物块再放到小车上
        #           4.前往暂存区，将物料块放到暂存区的地面
        #           5.回到原料区，准备任务二
        # ---------------------------------------------------------------------------------------- #

        # ----------------------------------  1.到暂存区抓 ----------------------------------  #
        # 前往暂存区
        self.moveControl.set_distance(x=-0.95)
        self.moveControl.turn_right()
        self.moveControl.set_distance(x=-0.97)
        self.adjustColorCircle()
        # 抓取物块
        self.catch(task2_color)

        # ----------------------------------  2.到精加工区放 ---------------------------------- #
        # -------- 前往精加工区 ----------- #

        dis2blue = 0.75  # 拐角到暂存区蓝色物料块圆环的距离
        dis2first_block = dis_between_every_circle * color_list_in_rough_area.index(task2_color[0])

        self.moveControl.turn_right()
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.circleArea, move_dis=-(dis2blue + dis2first_block))

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

        # ----------------------------------  3.在精加工区取走 ---------------------------------- #
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
        # 抓3走 计算到绿色的距离
        current_color = task2_color[2]
        next_color = "green"
        current_index = color_list_in_rough_area.index(current_color)
        next_index = color_list_in_rough_area.index(next_color)
        dis = -(next_index - current_index) * 0.15
        red2corner = -0.7
        dis = red2corner + dis

        # ----------------------------------  4.前往成品区，在成品区放 ---------------------------------- #
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.catchToCar, move_dis=dis)
        self.moveControl.turn_right()
        self.moveControl.move_while_adjusting_height(mix_mode=MixMode.rawArea, move_dis=-1.85)  # 从拐角到原料区的距离
        self.moveControl.turn_right()
        # 放第二轮物块
        self.putToTurn_2(task2_color)

        # ----------------------------------  5.回库 ------------------------------------------------- #
        self.moveControl.set_distance(x=1.15)
        self.moveControl.turn_right()
        self.moveControl.set_distance(x=0.05, y=-0.05)
        self.log(f'-------------- 任务执行完成！ --------------')



if __name__ == "__main__":
    # stm32_port = "COM4"
    stm32_port = "/dev/ttyUSB0"
    stm32_baudrate = 115200
    cam_name = 0

    com = ComRun(stm32_port, stm32_baudrate, cam_name)
    com.run()
