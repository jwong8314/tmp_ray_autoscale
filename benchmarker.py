
from pathlib import Path
import sys
import pickle

data_dir = Path(sys.argv[1])

filename = "./feas_res.pkl"
subdir = [x  for x in data_dir.iterdir() if x.is_dir()]
paths = [s / filename for s in subdir]

results = [  pickle.load(open (path, "rb")) for path in  paths]


import ray
ray.init()

@ray.remote
def f(results):
    needs_gpu = results["needs_gpu"]
    release_times = results["release_times"]
    absolute_deadlines = results["absolute_deadlines"]
    expected_runtimes = results["expected_runtimes"]
    dependency_matrix = results["dependency_matrix"]
    pinned_tasks = results["pinned_tasks"]
    num_gpus = results["n_gpu"]
    num_cpus = results["n_cpus"]
    num_tasks = len(needs_gpu)
    from gurobi_scheduler import GurobiScheduler
    sched = GurobiScheduler()
    out, output_cost, sched_runtime = sched.schedule(needs_gpu,
                release_times,
                absolute_deadlines,
                expected_runtimes,
                dependency_matrix,
                pinned_tasks,
                num_tasks,
                num_gpus,
                num_cpus,
                optimize=True,
                dump=False,
                outpath=".",
                dump_nx=False)
    return (out,output_cost,sched_runtime)

output = [f.remote(res) for res in results]
output_res = ray.get(output)

output_final = list(zip (subdir, output_res))


for path, (out,output_cost,sched_runtime) in output_final:
    with open (path / "gurobi.csv", "w") as f:
        f.write(f"{int(output_cost)}, {sched_runtime}")
    
    with open (path / "gurobi.out", "wb") as f:
        pickle.dump(out, f)
    


    
