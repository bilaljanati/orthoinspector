from concurrent.futures import ProcessPoolExecutor, as_completed
import sys
import string
import random
import src.tasks as tasks


class WorkerPool():
    DONE    = 0
    RUNNING = 1
    FAILED  = 2
    UNKNOWN = 3

    def __init__(self, nworkers=8):
        self.nworkers = nworkers
        self.pool = ProcessPoolExecutor(max_workers=nworkers)
        self.futures = {}

    def _generate_id(self, length=8):
        characters = string.ascii_letters + string.digits
        random_id = False
        while not random_id or random_id in self.futures:
            random_id = ''.join(random.choices(characters, k=length))
        return random_id

    def submit(self, val):
        taskid = self._generate_id()
        self.futures[taskid] = self.pool.submit(tasks.do_work, val)
        return taskid

    def get_result(self, taskid):
        if taskid not in self.futures:
            return __class__.UNKNOWN, None
        f = self.futures[taskid]

        if f.done():
            status = __class__.DONE
            res = f.result()
            del self.futures[taskid]
            if res == False:
                status = __class__.FAILED
        else:
            status = __class__.RUNNING
            res = None
        return (status, res)
