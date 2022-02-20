#from boolector_scheduler import BoolectorScheduler
from ilp_scheduler import ILPScheduler
from z3_scheduler import Z3_GroundTruth as Z3Scheduler
#from gurobi_scheduler import GurobiScheduler
import pickle
from pathlib import Path
import time
from absl import app, flags

FLAGS = flags.FLAGS

flags.DEFINE_integer('num_tasks', 25, 'number of tasks.')
flags.DEFINE_integer('NUM_GPUS', 2, 'Number of GPUs available.')
flags.DEFINE_integer('NUM_CPUS', 10, 'Number of CPUs available.')
flags.DEFINE_integer('task_runtime', 15, 'Estimated task runtime.')
flags.DEFINE_enum('scheduler', 'z3', ['boolector', 'z3', 'gurobi'],
                  'Sets which ILP scheduler to use')
flags.DEFINE_bool('opt', False,
                  'False --> feasibility only; True --> maximize slack')
flags.DEFINE_bool('dump', False, 'writes smtlib2 to outpath')
flags.DEFINE_string('outpath', "out", "path for output")
flags.DEFINE_bool('dump_nx', False, 'dumps networkx object')

flags.DEFINE_integer('dep1', 0, "first dep source")
flags.DEFINE_integer('dep2', 1, "first dep target")

flags.DEFINE_integer('cpu_process', 3, "process to be sent to cpu")

mini_run = False

def verify_schedule(start_times, placements, needs_gpu, release_times,
                    absolute_deadlines, expected_runtimes, dependency_matrix,
                    num_gpus, num_cpus):
    # check release times
    # import IPython; IPython.embed()
    assert all([s >= r for s, r in zip(start_times, release_times)
                ]), "not_valid_release_times"
    assert all([(not need_gpu or (p > num_cpus))
                for need_gpu, p in zip(needs_gpu, placements)
                ]), "not_valid_placement"
    assert all([
        (d >= s + e)
        for d, e, s in zip(absolute_deadlines, expected_runtimes, start_times)
    ]), "doesn't finish before deadline"
    for i, row_i in enumerate(dependency_matrix):
        for j, column_j in enumerate(row_i):
            if i != j and column_j:
                assert start_times[i] + expected_runtimes[i] <= start_times[
                    j], f"not_valid_dependency{i}->{j}"
    placed_tasks = [
        (p, s, s + e)
        for p, s, e in zip(placements, start_times, expected_runtimes)
    ]
    placed_tasks.sort()
    for t1, t2 in zip(placed_tasks, placed_tasks[1:]):
        if t1[0] == t2[0]:
            #print(t1, t2)
            assert t1[2] <= t2[1], "overlapping_tasks_on_{t1[0]}}"


def do_run(scheduler: ILPScheduler,
           num_tasks: int = 5,
           expected_runtime: int = 20,
           horizon: int = 45,
           num_gpus: int = 2,
           num_cpus: int = 10,
           optimize: bool = True,
           dump: bool = False,
           outpath: str = None,
           dump_nx: bool = False):

    print(f"Running for {num_tasks} task over horizon of {horizon}")
    # True if a task requires a GPU.
    needs_gpu = [True] * num_tasks
    # Release time when task is ready to start.
    release_times = [2 for _ in range(0, num_tasks)]
    # Absolute deadline when task must finish.
    absolute_deadlines = [horizon for _ in range(0, num_tasks)]
    # Expected task runtime.
    expected_runtimes = [expected_runtime for _ in range(0, num_tasks)]
    # True if task i must finish before task j starts
    dependency_matrix = [[False for i in range(0, num_tasks)]
                         for j in range(0, num_tasks)]
    # Hardware index if a task is pinned to that resource (or already running
    # there).
    pinned_tasks = [None] * num_tasks
    if not mini_run:
        dependency_matrix[FLAGS.dep1][FLAGS.dep2] = True
        needs_gpu[FLAGS.cpu_process] = False

    if outpath is not None:
        smtpath = outpath + f"{'opt' if optimize else 'feas'}.smt"
    else:
        smtpath = None
    print(f"smtpath: {smtpath}")
    out, output_cost, sched_runtime = scheduler.schedule(needs_gpu,
                                                         release_times,
                                                         absolute_deadlines,
                                                         expected_runtimes,
                                                         dependency_matrix,
                                                         pinned_tasks,
                                                         num_tasks,
                                                         num_gpus, #TODO: Leo change api here also
                                                         num_cpus,
                                                         bits=13,
                                                         optimize=optimize,
                                                         dump=dump,
                                                         outpath=smtpath,
                                                         dump_nx=dump_nx, 
                                                         cpu_proc_is_dep = (FLAGS.dep2 == FLAGS.cpu_process))

    #print(sched_runtime)
    # import IPython; IPython.embed()

    verify_schedule(out[0], out[1], needs_gpu, release_times,
                    absolute_deadlines, expected_runtimes, dependency_matrix,
                    num_gpus, num_cpus)
    print ("schedule verified")
    #  print ('GPU/CPU Placement:' ,out[0])
    #  print ('Start Time:' ,out[1])
    #print(out)
    if outpath is not None:
        with open(outpath + f"{'opt' if optimize else 'feas'}_res.pkl",
                  'wb') as fp:
            data = {
                'needs_gpu': needs_gpu,
                'release_times': release_times,
                'absolute_deadlines': absolute_deadlines,
                'expected_runtimes': expected_runtimes,
                'dependency_matrix': dependency_matrix,
                'pinned_tasks': pinned_tasks,
                'model': f"{out}",
                'n_gpu': num_gpus,
                'n_cpus': num_cpus,
                'runtime': sched_runtime,
                'output_cost': (int(f"{output_cost}") if output_cost is not None else None)
            }
            pickle.dump(data, fp)
            print("filepath =", fp)
    return (sched_runtime), output_cost


def main(args):
    if FLAGS.scheduler == 'boolector':
        scheduler = BoolectorScheduler()
    elif FLAGS.scheduler == 'z3':
        scheduler = Z3Scheduler()
    elif FLAGS.scheduler == 'gurobi':
        scheduler = GurobiScheduler()
    else:
        raise ValueError('Unexpected --scheduler value {FLAGS.scheduler}')
    runtimes = []
    # for num_tasks in range(1, 2, 1):
    num_tasks = FLAGS.num_tasks
    horizon = 15 * (num_tasks - 1 )//2 + 20
    outpath = (
        FLAGS.outpath +
        (f"/tasks={num_tasks}_horizon={horizon}_ngpu=" +
         f"{FLAGS.NUM_GPUS}_ncpu={FLAGS.NUM_CPUS}_cpu-proc={FLAGS.cpu_process}dep={FLAGS.dep1}" +
         f"-before-{FLAGS.dep2}/") if FLAGS.dump else None)
    print(f"outpath flag: {FLAGS.outpath}")
    print(f"dump flag: {FLAGS.dump}")
    if outpath is not None and not Path(outpath).is_dir():
        Path(outpath).mkdir()

    if mini_run:
        runtime, output_cost = do_run(scheduler,
                                      5,
                                      5,
                                      8000,
                                      2,
                                      1,
                                      optimize=FLAGS.opt,
                                      dump=FLAGS.dump,
                                      outpath=outpath,
                                      dump_nx=FLAGS.dump_nx)

    else:
        print(f"outpath: {outpath}")
        runtime, output_cost = do_run(scheduler,
                                      num_tasks,
                                      FLAGS.task_runtime,
                                      horizon,
                                      FLAGS.NUM_GPUS,
                                      FLAGS.NUM_CPUS,
                                      optimize=FLAGS.opt,
                                      dump=FLAGS.dump,
                                      outpath=outpath,
                                      dump_nx=FLAGS.dump_nx)

    print(f"runtime: {runtime} ----- output_cost: {output_cost}")
#     runtimes.append((num_tasks, runtime, output_cost))
#     if runtime > 600 or mini_run:
#         break


if __name__ == '__main__':
    app.run(main)
