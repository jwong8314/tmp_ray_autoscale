from typing import List
from base_scheduler import BaseScheduler

def GroundTruthCost(num_gpu, num_task,horizon,cpu_is_dependent, release_time = 2, expected_runtime=15):
    

    all_starts = 2*[release_time+expected_runtime*i for i in range(num_task//2)]
    if num_task % 2 == 1:
        all_starts = [release_time+expected_runtime*i for i in range(num_task//2)]
        all_starts = all_starts +  [release_time+expected_runtime*i for i in range(num_task//2 + 1 )] 

    if cpu_is_dependent:
        all_starts.append(release_time + expected_runtime)
    else:
        all_starts.append(release_time)

    all_starts.sort()
    all_starts = all_starts[:-1]
    assert len(all_starts) == num_task
    all_end_times = [s + expected_runtime for s in all_starts]
    all_slack = [ horizon - s for s in all_end_times ]

    total = sum(all_slack)
    if num_task < 4:
        total -= expected_runtime

    print (total)
    return  total 

class ILPScheduler(object):
    def schedule(needs_gpu: List[bool],
                 release_times: List[int],
                 absolute_deadlines: List[int],
                 expected_runtimes: List[int],
                 dependency_matrix,
                 pinned_tasks: List[int],
                 num_tasks: int,
                 num_gpus: int,
                 num_cpus: int,
                 bits: int = 8):
        raise NotImplementedError


class ILPBaseScheduler(BaseScheduler):
    def __init__(self, sched_solver: ILPScheduler):
        self.sched_solver = sched_solver()

    def schedule(self, tasks, task_graph, worker_pools):
        dependency_matrix = task_graph.get_dep(tasks)
        needs_gpu = [t.needs_gpu for t in tasks]
        absolute_deadlines = [t.deadline for t in tasks]
        expected_runtimes = [t.expected_runtime for t in tasks]
        num_tasks = len(tasks)

        num_gpus = worker_pools.num_gpu()
        num_cpus = worker_pools.num_cpu()

        release_times = [0] * num_tasks
        pinned_tasks = [None] * num_tasks

        (start_times,
         placements), opt_value, sched_runtime = self.sched_solver.schedule(
             needs_gpu,  #: List[bool],
             release_times,  #: List[int],
             absolute_deadlines,  #: List[int],
             expected_runtimes,  #: List[int],
             dependency_matrix,
             pinned_tasks,  #: List[int],
             num_tasks,  #: int,
             num_gpus,  #: int,
             num_cpus,  #: int,
             optimize=True,
         )

        result = list(zip(start_times, placements))
        return sched_runtime, result
