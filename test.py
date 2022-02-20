import ray
ray.init()
import os
import time
import signal

import pickle
import multiprocessing as mp

def child(i):
    if i % 2 == 0: 
        print (f"sleeping {i}")
        time.sleep(20)
        print (f"waking {i}")
    else:
        print (f"sleeping {i}")
        time.sleep(3)
        print (f"waking {i}")
    with open (f"f{i}.txt", "wb") as f :
        pickle.dump( i,f)
    exit(0)
    

def g(i):
    new_pid = os.fork()
    if new_pid == 0: 
        child(i)
    else: 
        start = time.time()
        while True:
            elapsed = time.time() - start
            print (i, elapsed)
            if elapsed > 5:
                os.kill(new_pid, signal.SIGKILL)
                print ("killed")
                return -1
            else: 
                # check if the process is alive
                try: 
                    alive = (os.waitpid(new_pid, os.WNOHANG) == (0,0))
                except OSError as e :
                    if e.errno != errno.ECHILD:
                        print ("idk")
                if not alive:
                    print ("i", i)
                    i = pickle.load(open(f"f{i}","rb"))
                    return i
            time.sleep(1)

@ray.remote
class Function:
    def __init__(self,i):
        self._start = None
        self.i = i
        
    def execute(self, i, f):
        self._start = time.time()
        return f(i)
        
    def duration(self):
        return self.i, time.time() - self._start
       
funcs = [Function.remote(i) for i in range(4)]
everyone = [f.execute.remote(i,g) for i,f in enumerate(funcs)]
all_durations = [f.duration.remote() for f in funcs]

#result, rest = ray.wait(all_durations)
#result,rest = [ray.get(r)for r in result], [ray.get(r)for r in rest]
#print(result,rest)
everyone = ray.get(everyone)    
print (everyone)
print ("done")

#if duration == []:
#    print ("killed task 0")
#    ray.kill(funcs[0])
#    all_durations = [f.duration.remote() for f in funcs[1:]]
#else:
#    i, duration = ray.get(duration[0])
#    print (ray.get(everyone[i]) , "output")
#
#ray.wait(all_durations, timeout = 5)
#print ("finally")

        

