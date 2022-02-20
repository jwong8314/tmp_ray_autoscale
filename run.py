import subprocess
for n in range(4, 24):
    for c in range(0,n):
        for i in range (0,n):
            for j in range (0,n): 
                for cpu in range (2,11):
                    if i != j:
                        command = f"python benchmark_ilp_schedulers.py --dump=True --outpath=../data_curriculum_{n} --dump_nx=True  --dep1={i} --dep2={j} --cpu_process={c} --num_tasks={n} --NUM_CPUS={cpu}"
                        subprocess.run(command.split(" "))

