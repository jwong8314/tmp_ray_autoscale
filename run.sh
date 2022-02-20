for c in {0..${t}}
    do 
        for i in {0..${t}}
        do
            for j in {0..${t}}
            do 
                if [ $i -ne $j ]; then
                    echo "$i $j"
                    python benchmark_ilp_schedulers.py --dump=True --outpath="../data_curriculum_5" --dump_nx=True  --dep1=$i --dep2=$j --cpu_process=$c
                fi
            done
        done
    done
