'''
Ver. 1.0.0
released on 2023/08/22
Developed by David.SY.Chen

License all reserved by LDC in BenQ.

Version:
IndieCat - 1.0.0
motobojocasa - 1.0.0
bound_setting - 1.0.0
'''

from bound_setting import BoundStore
from IndieCat import IndieCat
from motobojocasa import Moto
from time import ticks_ms, ticks_add, ticks_diff
from machine import ADC,Pin


SLEEP_TIME_MS = 10
OUTPUT_CYCLE_MS = 50
LONG_PRESS_TIME_MS = 3000

MOTOR_PIN, ADC_PIN = 15, 26
BUTTON_PIN = 16
LED_PIN = 0
CMD, TOTAL_STEP = 0, 270            #CMD是初始command, TOTAL_STEP用於馬達最大角度
MAX_CYCLE = 5                       #cycle數最大值



#啟動硬體
motor = Moto(MOTOR_PIN, TOTAL_STEP, CMD)
adc = ADC(Pin(ADC_PIN, Pin.IN))
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
led_array = IndieCat(LED_PIN, OUTPUT_CYCLE_MS)

#啟動軟體
BS = BoundStore()

BS.sleep_time = OUTPUT_CYCLE_MS
BS.store()


angle_duty_table = [
    [250,   0],
    [3480,  15],
    [7375,  30],
    [12625, 45],
    [17170, 60],
    [20260, 75],
    [23730, 90],
    [26422, 105],
    [30120, 120],
    [34060, 135],
    [37212, 150],
    [41125, 165],
    [46465, 180],
    [49424, 195],
    [52300, 210],
    [56820, 225],
    [60323, 240],
    [63945, 255],
    [65535, 270]
]





def duty_to_angle(duty:int) -> int:
    '''
    使用angle_duty_table來內插出所有角度值
    '''

    if duty < angle_duty_table[0][0]: return angle_duty_table[0][1]

    #Binary Search
    r = len(angle_duty_table)-1
    l = 0
    while l+1 != r:
        mid = (l+r)>>1
        if angle_duty_table[mid][0] < duty:
            l = mid
        else:
            r = mid
    
    a, b = angle_duty_table[l][1], angle_duty_table[r][1]
    x, y = angle_duty_table[l][0], angle_duty_table[r][0]

    #interpolation
    len_l, len_r = duty - x, y - duty

    ans = (len_l * b + len_r * a) // (y - x)
    return ans



'''
總共有3種模式: STOP, PLAY, SETTING
以下的tree的left node代表短按button, right node代表長按
    STOP
    /  \\
PLAY    SETTING
----------------
        PLAY
        /  \\
    PAUSE   STOP
    /  \\
PLAY   STOP
----------------
                        SETTING
                        /     \\
                LWR BOUND      STOP
                /       \\
        UPR BOUND        STOP
        /       \\
SAVE & STOP      STOP
----------------
'''

class FUNCTION_NODE:
    '''
    每個FUNCTION_NODE儲存了三個介面(可變電阻, LED陣列, 馬達)的狀態
    '''

    #CONSTANT
    ACTIVE = 'ACTIVE'
    DEACTIVE = 'DEACTIVE'


    def __init__(self,
                 tag:str,
                 left:str = 'NONE',
                 right:str = 'NONE',
                 potentialmeter:str = DEACTIVE,
                 led:list[str] = ['BLACK', '0', 'DEBLINK'],
                 motor:str = DEACTIVE):
        '''
        tag:    自身的名稱標籤
        left:   單擊按鍵後前往的下個標籤
        right:  長按按鍵後前往的下個標籤
        potentialmeter:     可變電阻是否開啟
        led:                LED陣列的輸出狀態
        motor:              馬達輸出值的來源, 如果為-1則不輸出
        '''
        self.tag = tag
        self.left = left
        self.right = right

        self.potentialmeter = potentialmeter
        self.led = led
        self.motor = motor



class MotorStatus:

    timer = None
    def __init__(self,
                 step_total:int,
                 bound_data:list[int|float],
                 direction:int = 1) -> None:
        '''
        儲存馬達每個運動位置, 狀態的物件
        \n變數:
        bound_data - [初始點, 結束點, 步長]
        step_total - 總cycle數
        direction - 馬達運行的方向, 1是正行程, -1是負行程
        '''
        self.step_now = bound_data[0]
        self.direction = direction
        self.step_total = step_total

        self.upr_bound = bound_data[1]
        self.lwr_bound = bound_data[0]
        self.length_step = bound_data[2]

        self.counter = 0
        self.done = False

    

    def next(self) -> int|None:
        
        
        def turn_around() -> None:
            self.direction *= -1
            return

        if self.done: return

        self.step_now += self.direction * self.length_step
        int_step_now = int(round(self.step_now))
        
        '''if int_step_now == self.lwr_bound:
            new_time = ticks_ms()
            if self.timer:
                print(ticks_diff(new_time, self.timer))
            self.timer = new_time'''

        if int_step_now == self.upr_bound or int_step_now == self.lwr_bound: turn_around()
        if int_step_now == self.lwr_bound: self.counter += 1

        if self.is_done(int_step_now): self.done = True

        return int_step_now
    


    def reset(self,
              new_bound_data:list[int|float] = []) -> int:
        if not new_bound_data:
            new_bound_data = [
                self.lwr_bound,
                self.upr_bound,
                self.length_step
            ]
        self.__init__(self.step_total, new_bound_data)
        return int(self.step_now)

        

    def is_done(self, step_now:int) -> bool:
        if step_now != self.lwr_bound: return False
        return self.counter == self.step_total
    




mode_name = {
    'STOP':[
        'PLAY',     'SETTING_LB',
        'DEACTIVE',
        ['PURPLE',  '255',  'DEBLINK'],
        'DEACTIVE'
    ],
    'PLAY':[
        'PAUSE',    'STOP',
        'DEACTIVE',
        ['RED',     'CNTR', 'DEBLINK'],
        'ACTIVE'
    ],
    'PAUSE':[
        'PLAY',     'STOP',
        'DEACTIVE',
        ['RED',     'CNTR', 'BLINK'],
        'ACTIVE'
    ],
    'DONE':[
        'PLAY',     'SETTING_LB',
        'DEACTIVE',
        ['GREEN',   'CNTR', 'DEBLINK'],
        'DEACTIVE'
    ],
    'SETTING_LB':[
        'SETTING_UB','STOP',
        'ACTIVE',
        ['BLUE',    'READ', 'DEBLINK'],
        'ACTIVE'
    ],
    'SETTING_UB':[
        'SAVE',     'STOP',
        'ACTIVE',
        ['BLUE',    'READ', 'DEBLINK'],
        'ACTIVE'
    ],
    'SAVE':[
        'NONE',     'NONE',
        'DEACTIVE',
        ['BLACK',   '0',    'DEBLINK'],
        'DEACTIVE'
    ]
}



mode_now = 'STOP'
mode:dict[str,FUNCTION_NODE] = {}

for m in mode_name:
    mode[m] = FUNCTION_NODE(m,
                            mode_name[m][0],
                            mode_name[m][1],
                            mode_name[m][2],
                            mode_name[m][3],
                            mode_name[m][4])

del mode_name


def short_press() -> None:
    global mode_now, changed
    mode_now = mode[mode_now].left

    if mode_now == 'SAVE':
        BS.set_bound('lower', new_bound_value[0])
        BS.set_bound('upper', adc_value[0])
        BS.store()
        motor.go_to(MS.reset(BS.print_bound_data()))
        mode_now = 'STOP'

    if mode_now == 'SETTING_UB':
        new_bound_value[0] = adc_value[0]

    if mode_now == 'PLAY' and MS.done:
        motor.go_to(MS.reset(BS.print_bound_data()))

    changed = 1

    return


def long_press() -> None:
    global mode_now, changed
    mode_now = mode[mode_now].right

    if mode_now == 'SETTING_LB':
        MS.reset()
    
    if mode_now == 'STOP':
        motor.go_to(MS.reset())

    changed = 1

    return


#初始化
trigger, changed = 0, 0
pressed = ticks_ms()
end_output_cycle = ticks_add(pressed, OUTPUT_CYCLE_MS)
adc_value = [adc.read_u16()]
new_bound_value = [BS.lwr_bound]

MS = MotorStatus(MAX_CYCLE, BS.print_bound_data())
motor.go_to(MS.reset())



while True:
    def output_function() -> None:

        #ADC是否讀值
        if mode[mode_now].potentialmeter == 'ACTIVE':
            adc_value[0] = duty_to_angle(adc.read_u16())

        #如果ADC有在讀值,且馬達也有運作,則馬達執行ADC的讀值
            if mode[mode_now].motor == 'ACTIVE':
                motor.go_to(adc_value[0])
        
        #如果ADC沒有讀值,但馬達需要運作,則馬達執行循環動作
        elif mode_now == 'PLAY':
            motor.go_to(MS.next())


        #LED的指令
        color, num, blink = mode[mode_now].led
        led_array.change_color_to(color)
        
        if blink == 'BLINK':
            led_array.blink()
        else:
            led_array.deblink()
        
        if num == 'READ':
            led_array.show_number(adc_value[0])
        elif num == 'CNTR':
            led_array.show_number(MS.counter)
        else:
            led_array.show_number(int(num))

        return



    #啟動計時器
    start_cycle = ticks_ms()
    end_cycle = ticks_add(start_cycle, SLEEP_TIME_MS)


    if button.value():
        if not changed:
            if not trigger:
                pressed = ticks_ms()
                trigger = 1
            else:
                if ticks_diff(ticks_ms(), pressed) > LONG_PRESS_TIME_MS:
                    trigger = 0
                    long_press()
    else:
        if changed: changed = 0
        if trigger:
            end_press = ticks_diff(ticks_ms(), pressed)
            if end_press < LONG_PRESS_TIME_MS:
                short_press()
            else:
                long_press()
            trigger = 0


    if end_cycle > end_output_cycle:
        output_function()
        end_output_cycle = ticks_add(start_cycle, OUTPUT_CYCLE_MS)


    
    #當馬達達到循環最大次數時,顯示為完成
    if MS.done: mode_now = 'DONE'


    led_array.__go__()
    motor.__go__()

    while ticks_ms() < end_cycle:
        pass