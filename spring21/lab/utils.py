def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]
        
import time
    
class Stopwatch():
    
    def __init__(self):
        self.reset()
        
    def start(self):
        if self.start_time is None:
            self.start_time = time.perf_counter()
    
    def stop(self):
        if self.start_time is not None:
            self.elapsed += time.perf_counter() - self.start_time
            self.start_time = None
    
    def active(self):
        return self.start_time is not None
    
    def reset(self):
        self.elapsed = 0
        self.start_time = None
        