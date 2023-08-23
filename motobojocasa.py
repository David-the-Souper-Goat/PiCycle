'''
Ver. 1.0.0
Developed by David.SY.Chen
License all reserved by LDC in BenQ.
'''
from machine import Pin, PWM


class Moto:

    #馬達的時脈下限
    lwr_limit_ns = 500_000
    #馬達的時脈區間
    interval_ns = 2_000_000
    #最小解析率:最小時脈變化/總時脈區間
    MIN_RATIO_INTERVAL = 0.002
    #最小時脈變化
    min_interval_ns = int(interval_ns * MIN_RATIO_INTERVAL)


    def __init__(self,
                 output_pin: int,
                 total_step: int = 180,
                 initial_position: int = 0,
                 frq: int = 200) -> None:
        '''
        Moto是個Micropython用的伺服馬達控制的基礎物件\n
        控制方式為PWM輸出,預設階數180階,輸出頻率120Hz\n
        預設時脈上下限為[0.5, 2.5] ms\n\n
        初始參數說明:\n
        \t output_pin:        版端輸出PWM訊號的GPIO編號\n
        \t total_step:        伺服馬達實際運動的最大角度範圍\n
        \t initial_position:  希望給馬達的初始位置\n
        \t frq:               PWM訊號的頻率
        '''
        self.motor = PWM(Pin(output_pin, Pin.OUT))
        self.motor.freq(frq)
        self.step = total_step
        self.command = self.__angle2ns__(initial_position)
        self.position = self.__angle2ns__(initial_position)
        self.motor.duty_ns(self.position)


    def go_to(self, cmd:int|None = None) -> None:
        '''
        將下一個command改成cmd\n
        cmd: 下一個位置 in 角度
        '''
        if cmd == None: return
        self.command = self.__angle2ns__(cmd)
        return
    

    def __go__(self) -> None:
        '''
        將position(目前馬達位置)移動到command(目標馬達位置)的function\n
        使用P-control以緩和過快的馬達移動
        '''
        
        cmd, pos = self.command, self.position

        #如果command 和 position相等，則跳出
        if cmd == pos: return

        #P-control係數
        P_coefficient = 0.03

        #算得從position抵達下一個position的變化量
        diff = int(round((cmd - pos) * P_coefficient))

        #若diff小於最小時脈變化,則至少進行1格最小時脈變化
        abs_diff = abs(diff)
        if not diff: return
        diff = self.min_interval_ns * int(diff/abs_diff) if abs_diff < self.min_interval_ns else diff

        #將結果寫入self.position, 並讓馬達送出新的時脈長
        self.position += diff
        self.motor.duty_ns(self.position)

        return
    

    def __angle2ns__(self, angle:int) -> int:
        '''
        將角度值轉換成PWM訊號的時脈長\n
        input:\tangle是角度[與最大角度同單位]\n
        output:\t時脈長[ns]\n
        '''
        lb, itvl = self.lwr_limit_ns, self.interval_ns
        stp = self.step

        if angle < 0:   return lb
        if angle > stp: return lb + itvl
        return lb + int(itvl * angle / stp)