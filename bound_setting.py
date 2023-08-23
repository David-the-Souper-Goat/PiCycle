'''
Ver. 1.0.0
Developed by David.SY.Chen
License all reserved by LDC in BenQ.
'''

import json


class BoundStore:

    def __init__(self) -> None:
        '''
        從儲存空間"store.json"中取得儲存值
        並可以透過函數'store'儲存新的儲存值

        此儲存值係指一串馬達的指令
        '''
        with open('store.json') as opened_file:
            data = json.load(opened_file)
        self.upr_bound = data['cmd_array'][-1]
        self.lwr_bound = data['cmd_array'][0]

        self.cycle_time = data['cycle_time']
        self.sleep_time = data['time_interval']

        self.spread_cmd_list()


    def store(self) -> None:

        def pack() -> dict:
            content = {
                'cycle_time':self.cycle_time,
                'time_interval': self.sleep_time,
                'cmd_array': [self.lwr_bound, self.upr_bound]
            }

            return content
        with open('store.json') as opened_file:
            json.dump(pack(), opened_file)
        
        self.spread_cmd_list()

        return
    

    def print_bound_data(self) -> list[int|float]:
        return [self.lwr_bound, self.upr_bound, self.length_step]

    
    def spread_cmd_list(self) -> None:
        lb, ub = self.lwr_bound, self.upr_bound
        t, p = self.cycle_time, self.sleep_time
        step = t // p
        self.length_step = ((ub - lb)<<1) / step

        return
    

    def set_bound(self, bound_type:str , bound_value:int) -> None:
        
        if bound_type not in ['upper', 'lower']: return

        if bound_type == 'upper':
            self.upr_bound = bound_value
        if bound_type == 'lower':
            self.lwr_bound = bound_value

        return
    

if __name__ == '__main__':

    BS = BoundStore()
    print(BS.cycle_time, BS.sleep_time)
    print(BS.lwr_bound, BS.upr_bound)
    print(BS.length_step)
