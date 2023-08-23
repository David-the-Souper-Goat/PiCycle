'''
Ver. 1.0.0
Developed by David.SY.Chen
License all reserved by LDC in BenQ.
'''

from machine import Pin
import neopixel as np
from time import ticks_ms, ticks_add


class IndieCat:
    '''
    8顆RGB LED陣列串
    '''

    color_map = {
        'RED':(63,0,0),
        'GREEN':(0,63,0),
        'BLUE':(0,0,63),
        'PURPLE':(31,15,31),
        'BLACK':(0,0,0)
    }

    is_blinking = 0
    is_all_out = 0

    def __init__(self,
                 output_pin:int,
                 refresh_time:int = 10) -> None:
        '''
        初始化一組1X8的全彩LED陣列\n
        output_pin:   在PICO上連接LED陣列的GPIO
        refresh_time: 系統更新LED陣列的週期 [ms]

        --函數--
        blink:        閃爍整排陣列,沒亮的LED則不做事
        deblink:      解除blink

        '''
        self.led = np.NeoPixel(Pin(output_pin), 8)
        self.refresh_time = refresh_time
        self.color = self.color_map['RED']
        self.number = 0




    def blink(self, freq:float = 1.0) -> None:
        '''
        閃爍整排陣列,沒亮的LED則不做事
        freq: 陣列閃爍的頻率,預設1 Hz'''
        period = int(1000 // freq)

        self.is_blinking = 1
        self.blink_period = period
        self.blink_end = ticks_add(ticks_ms(), period)

        return
    

    def deblink(self) -> None:

        self.is_blinking = 0
        self.is_all_out = 0

        return
    



    def show_number(self, num:int) -> None:
        '''
        以二進位顯示LED
        '''

        #因為只有8位元容量, 所以超過2^8則離開
        if num > (1<<8) or num < 0: return

        for i in range(8):

            #如果系統顯示全黑, 則直接不亮
            if self.is_all_out:
                self.led[i] = (0,0,0)

            #判定數字的對應位元狀態
            elif (num>>i)&1:
                self.led[i] = self.color
            else:
                self.led[i] = (0,0,0)            

            

        #儲存做好的數字在記憶體
        self.number = num

        return
    


    def change_color_to(self, color:str|tuple) -> None:
        if isinstance(color,str):
            if color in self.color_map:
                self.color = self.color_map[color]
        
        if isinstance(color, tuple):
            if len(color) != 3: return
            for i in color:
                if i < 0 or i > 255: return
            self.color = color

        return
    

    def __go__(self) -> None:

        if self.is_blinking:
            #檢查時間
            now = ticks_ms()
            if now >= self.blink_end:
                #如果超過預定閃爍時間
                #切換 is_blinking
                self.is_all_out ^= 1

                #更新數字
                self.show_number(self.number)

                #更新下一次閃爍時間
                self.blink_end = ticks_add(now, self.blink_period)

        self.led.write()

        return