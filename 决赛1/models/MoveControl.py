import serial
from .config import Mode, HeightMode
import time


# 输入一个十进制的[-128, 127]范围内的整数，获取它补码的十进制
def get_int8(num):
    assert -128 <= num <= 127, print("int8类型范围为[-128, 127]")
    if num >= 0:
        return int(num)
    else:
        return int(255 + num + 1)


# 运动控制类，包含小车的距离控制，以及旋转控制
class MoveControl(object):
    def __init__(self, port, baudrate) -> None:
        self.port = port
        self.baudrate = baudrate
        self.serial = serial.Serial(port, baudrate)
        print("与stm32串口初始化成功")
        self.serial.flush()

        # 初始化数据列表 [头帧，模式，X方向，Y方向，角度，二维码1，二维码2，尾帧]
        self.send_buffer = [0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0xFE]

    # 生成串口数据、发送数据并等待回传结果
    # noinspection PyTypeChecker
    def __send_serial_msg(self, mode, x_dis=None, y_dis=None, angel=None):
        if mode == Mode.x_distance:
            assert x_dis is not None, print("未指定x方向移动距离")
            self.send_buffer[1] = mode.value
            self.send_buffer[2] = (x_dis >> 8) & 0xFF
            self.send_buffer[3] = x_dis & 0xff
        


        elif mode == Mode.y_distance:
            assert y_dis is not None, print("未指定y方向移动距离")
            self.send_buffer[1] = mode.value
            self.send_buffer[2] = (y_dis >> 8) & 0xFF
            self.send_buffer[3] = y_dis & 0xff


        elif mode == Mode.rotate:
            assert angel is not None, print("未设置角度")
            self.send_buffer[1] = mode.value
            self.send_buffer[4] = get_int8(angel)
            
        elif mode == Mode.mix_mode:
            self.send_buffer[1] = mode.value
            self.send_buffer[2] = y_dis.value
            self.send_buffer[3] = get_int8(x_dis)

      
        elif mode == Mode.rotate_together:
            assert angel is not None, print("未设置角度")
            self.send_buffer[1] = mode.value
            self.send_buffer[4] = get_int8(angel)

        elif mode == Mode.rotate_together2:
            assert angel is not None, print("未设置角度")
            self.send_buffer[1] = mode.value
            self.send_buffer[4] = get_int8(angel)

        elif mode == Mode.qrcode:
            self.send_buffer[1] = mode.value

        elif mode == Mode.x_dis_mm:
            assert x_dis is not None, print("未指定x方向移动距离，单位:毫米")
            self.send_buffer[1] = mode.value
            self.send_buffer[2] = get_int8(x_dis)
 
            
        elif mode == Mode.y_dim_mm:
            assert y_dis is not None, print("未指定x方向移动距离，单位:毫米")
            self.send_buffer[1] = mode.value
            self.send_buffer[3] = get_int8(y_dis)
            
            
        elif mode == Mode.adjust_height_a:
            assert x_dis is not None, print("未指定转盘高度")
            self.send_buffer[1] = mode.value
            self.send_buffer[2] = get_int8(x_dis)
            
            
        elif mode == Mode.move_mm_newx:
            self.send_buffer[1] = mode.value
            self.send_buffer[2] = (x_dis >> 8) & 0xFF
            self.send_buffer[3] = x_dis & 0xff
        
        elif mode == Mode.move_mm_newy:
            self.send_buffer[1] = mode.value
            self.send_buffer[2] = (y_dis >> 8) & 0xFF
            self.send_buffer[3] = y_dis & 0xff
        

        # 从原料区抓取物料块 放到1
        elif mode == Mode.grub_1:
            self.send_buffer[1] = mode.value

        # 从原料区抓取物料块 放到2
        elif mode == Mode.grub_2:
            self.send_buffer[1] = mode.value

        elif mode == Mode.max_height:
            self.send_buffer[1] = mode.value
            
        elif mode == Mode.get_qrPos:
            self.send_buffer[1] = mode.value


        # 从1抓取物料块 放到地上
        elif mode == Mode.down_1:
            self.send_buffer[1] = mode.value

        # 从2抓取物料块 放到地上
        elif mode == Mode.down_2:
            self.send_buffer[1] = mode.value

        elif mode == Mode.put_to_turn:
            self.send_buffer[1] = mode.value
        
        
        elif mode == Mode.turn_front:
            self.send_buffer[1] = mode.value
            
        elif mode == Mode.rotate_adjust:
            self.send_buffer[1] = mode.value
            
        elif mode == Mode.rotate_reset:
            self.send_buffer[1] = mode.value


        
        # 调整升降台的位置
        elif mode == Mode.adjust_height:
            self.send_buffer[1] = mode.value
            self.send_buffer[2] = x_dis.value

        elif mode == Mode.adjust_height_a:
            self.send_buffer[1] = mode.value
            self.send_buffer[2] = get_int8(x_dis)
        

        else:
            raise ValueError("下位机模式选择错误，现有的模式有", [mode.name for mode in Mode])

        self.serial.write(self.send_buffer)

        self.__wait_for_movement_done()
        time.sleep(0.05)
    
    # 程序启动后，需要等待下位机启动指令  [0xFF, 0x10, 0xFE]
    def wait_for_start_cmd(self):
        while True:
            data = self.serial.read(8)
            print(data)
            if 0x02 in data:
                break

      
    # 在下发动作后，比如前进，旋转等，下位机执行结束后会回传任务结束指令[0xFF, 0x01, 0xFE]
    def __wait_for_movement_done(self):
        while True:
            header = ord(self.serial.read())
            if header == self.send_buffer[0]:
                if ord(self.serial.read()) == 0x01:
                    return True
                else:
                    pass
            else:
                pass

    
    def notice_qr_info(self):
        self.__send_serial_msg(mode=Mode.qrcode)


    # 从下位机获取二维码信息
    def get_qrPos(self) -> str:
        n = self.serial.read()
        print(f"n:{n}")
        buffer_a = [0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0xFE]
        buffer_a[1] = 54
        result = []
        self.serial.write(bytes(buffer_a))
        while True:
            m = self.serial.read()
            print(f"m:{m}")
            if m != b'\xff' and m != b'\xfe':
                break
        result.append(m.decode())
        for i in range(6):
            a = self.serial.read()
            #print(a)
            result.append(a.decode())
        self.serial.read(3)
        return "".join(result)


    # 距离控制，支持x和y同时输入，先运行x再运行y
    def set_distance(self, x=0, y=0):
        x = 1e-9 if x == 0 else x
        y = 1e-9 if y == 0 else y
        x_dis = int(x * 100)
        y_dis = int(y * 100)
        if x_dis != 0:
            self.__send_serial_msg(mode=Mode.x_distance, x_dis=x_dis)
        if y_dis != 0:
            self.__send_serial_msg(mode=Mode.y_distance, y_dis=y_dis)

    # 较为精细的距离控制
    def move_in_mm(self, x=0, y=0):
        x = 128 if x > 128 else int(x)
        x = -127 if x < -127 else int(x)
        y = 128 if y > 128 else int(y)
        y = -127 if y < -127 else int(y)
        if x != 0:
            self.__send_serial_msg(mode=Mode.x_dis_mm, x_dis=x)
        if y != 0:
            self.__send_serial_msg(mode=Mode.y_dim_mm, y_dis=y)
            
    def move_in_mm_new(self, x=0, y=0):
        x = 1e-9 if x == 0 else x
        y = 1e-9 if y == 0 else y
        x_dis = int(x * 10)
        y_dis = int(y * 10)
        if x_dis != 0:
            self.__send_serial_msg(mode=Mode.move_mm_newx, x_dis=x_dis)
        if y_dis != 0:
            self.__send_serial_msg(mode=Mode.move_mm_newy, y_dis=y_dis)

    # 旋转，角度定义为[-127, 128]之间
    def rotate(self, angle):
        assert -127 <= angle <= 128, print("角度应当在[-127, 128]之间")
        self.__send_serial_msg(mode=Mode.rotate, angel=angle)


    def turn_left(self):
        #self.rotate_adjust()
        self.rotate(77)
        self.rotate_adjust()

    def turn_right(self):
        #self.rotate_adjust()
        self.rotate(-77)
        self.rotate_adjust()

    def turn_together(self, angle):
        assert -127 <= angle <= 128, print("角度应当在[-127, 128]之间")
        self.__send_serial_msg(mode=Mode.rotate_together, angel=angle)

    def turn_together2(self, angle):
        assert -127 <= angle <= 128, print("角度应当在[-127, 128]之间")
        self.__send_serial_msg(mode=Mode.rotate_together2, angel=angle)

    def rotate_adjust(self):
        self.__send_serial_msg(mode=Mode.rotate_adjust)
        
    def rotate_reset(self):
        self.__send_serial_msg(mode=Mode.rotate_reset)

    # 从原料区抓取物料块
    def grubBlockFromRawArea(self):
        self.__send_serial_msg(mode=Mode.grub_1)

    # 把物块放到地上
    def putBlockToCircle(self):
        self.__send_serial_msg(mode=Mode.down_1)

    # 从地上抓取物块
    def grubBlockFromGround(self):
        self.__send_serial_msg(mode=Mode.grub_2)

    # 物块码垛
    def putBlockToAnotherBlock(self):
        self.__send_serial_msg(mode=Mode.down_2)

    def putBlockToTurn(self):
        self.__send_serial_msg(mode=Mode.put_to_turn)

    def putBlockToStack(self):
        self.__send_serial_msg(mode=Mode.put_to_stack)

    def adjustHeightOrderHeight(self, height):
        self.__send_serial_msg(mode=Mode.adjust_height_a, x_dis=height)

    def highUp(self):
        self.__send_serial_msg(mode=Mode.max_height)

    # 调整升降台到合适的位置    1.读取二维码  2.识别原料区  3.识别圆环   4.识别物料块圆心 
    def adjustHeight(self, target_height):
        heightConfigs = [mode for mode in HeightMode]
        if target_height not in heightConfigs:
            raise ValueError("小车高度模式中没有这个模式{0}".format(target_height))
        self.__send_serial_msg(mode=Mode.adjust_height, x_dis=target_height)
    

    """
        混合模式: 支持在小车的移动过程中移动升降台，减少时间
        输入参数：
            height_mode: 期望的模式，支持单纯的升降台移动，以及夹取后的直接离开
            move_dis: 小车移动距离（仅限X方向移动）
        返回参数：
            无；当接收到下位机信号后，函数结束
    """

    def move_while_adjusting_height(self, mix_mode, move_dis: float):
        if abs(move_dis) > 1.25:
            raise ValueError('太远了，这个模式最远支持1.25m')
        dis = 100 * move_dis
        self.__send_serial_msg(mode=Mode.mix_mode, x_dis=dis, y_dis=mix_mode)

    def __del__(self):
        self.serial.close()
        print("程序结束，释放串口")
