import pickle
filename = "./feas_res.pkl"
results = pickle.load(open (filename, "rb"))
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

with open ("./gurobi.csv", "w") as f:
    f.write(f"{int(output_cost)}, {sched_runtime}")

with open ("./gurobi.out", "wb") as f:
    pickle.dump(out, f)
    


    
