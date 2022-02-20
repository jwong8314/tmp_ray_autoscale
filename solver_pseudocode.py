class OMT: 
    def set(assignments):
        # set values of assignments to variables 
        # add x == v 
        return
    def get_list_of_atoms():
        # return {id,sexpr}
        return
    def update_curr_smt(dict_of_assignments):
        # tracks smt solution currently seen
        return
    def update_curr_backbone(id, value):
        # tracks smt backbone
        return 

runs = dive(OMT,k = 10)
for r in run: 
    OMT.set(r)
    while (True):
        smt = smt.solver(OMT)
        milp = milp.init()

        smt_assignments = smt.solve()
        OMT.update_curr_smt(smt_assignments)
        for id,sexpr in OMT.get_list_of_atoms:
            v = smt.get_value(sexpr)
            OMT.update_curr_backbone(id,v)
            if v: 
                milp.add(sexpr)
            else: 
                milp.add(not(sexpr))

        milp.add(OMT.abstain())
        lb_curr = milp.solve()
        if lb_curr - lb < tolerance: 
            smt.push()
            is_finished = smt.add(make_blocker(lb_curr + tolerance))
            if is_finished == smt.UNSAT: 
                break
            else: 
                smt.pop()

        blocker = make_blocker(lb_curr)
        smt.add(blocker)
        lb = lb_curr
    