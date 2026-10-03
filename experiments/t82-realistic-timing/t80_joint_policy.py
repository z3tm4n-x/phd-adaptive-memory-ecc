"""Integer direct-fast LOW oracle. Choose this type once, before observations."""
from t80_policy import MonitorState, join


class DirectState(MonitorState):
    LOW_kind = 'direct-fast'

    def message(self,index,value,now,good=True):
        start=index*self.stride
        deadline=start+self.w+self.d
        if now<deadline:raise ValueError('early message waits for fixed deadline')
        valid=(good and now==deadline and index>self.last_index and type(value) is int
               and 0<=value<=self.k and value<2**64)
        self.last_index=max(index,self.last_index)
        if not valid:
            self.Q=self.LOW=None
            self.holdM=max(self.holdM,now+self.hM)
            return False
        # lease here is hF from WINDOW START, not from delivery/end of Q.
        self.LOW=join(self.LOW,(deadline,start+self.lease))
        return True
