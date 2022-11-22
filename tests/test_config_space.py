from ConfigSpace.read_and_write import pcs
from rpy2.robjects.packages import importr
import io
from contextlib import redirect_stdout
from irace.compatibility.config_space import convert_from_config_space

irace_pkg = importr('irace')

pcss = '''
barrier_algorithm {0, 1, 2, 3} [0]
barrier_crossover {-1, 0, 1, 2} [0]
barrier_limits_corrections {-1, 0, 1, 4, 16, 64} [-1]
barrier_limits_growth [1000000.0, 100000000000000.0] [1000000000000.0]l
barrier_ordering {0, 1, 2, 3} [0]
barrier_startalg {1, 2, 3, 4} [1]
emphasis_memory {no} [no]
emphasis_mip {0, 1, 2, 3, 4} [0]
emphasis_numerical {yes, no} [no]
feasopt_mode {0, 1, 2, 3, 4, 5} [0]
lpmethod {0, 1, 2, 3, 4, 5, 6} [0]
mip_cuts_cliques {-1, 0, 1, 2, 3} [0]
mip_cuts_covers {-1, 0, 1, 2, 3} [0]
mip_cuts_disjunctive {-1, 0, 1, 2, 3} [0]
mip_cuts_flowcovers {-1, 0, 1, 2} [0]
mip_cuts_gomory {-1, 0, 1, 2} [0]
mip_cuts_gubcovers {-1, 0, 1, 2} [0]
mip_cuts_implied {-1, 0, 1, 2} [0]
mip_cuts_mcfcut {-1, 0, 1, 2} [0]
mip_cuts_mircut {-1, 0, 1, 2} [0]
mip_cuts_pathcut {-1, 0, 1, 2} [0]
mip_cuts_zerohalfcut {-1, 0, 1, 2} [0]
mip_limits_aggforcut [0, 10] [3]i
mip_limits_cutpasses {-1, 0, 1, 4, 16, 64} [0]
mip_limits_cutsfactor [1.0, 16.0] [4.0]l
mip_limits_gomorycand [50, 800] [200]il
mip_limits_gomorypass {0, 1, 4, 16, 64} [0]
mip_limits_submipnodelim [125, 2000] [500]il
mip_ordertype {0, 1, 2, 3} [0]
mip_strategy_backtrack {0.9, 0.99, 0.999, 0.9999, 0.99999, 0.999999} [0.9999]
mip_strategy_bbinterval [1, 1000] [7]il
mip_strategy_branch {-1, 0, 1} [0]
mip_strategy_dive {0, 1, 2, 3} [0]
mip_strategy_file {0, 1} [1]
mip_strategy_fpheur {-1, 0, 1, 2} [0]
mip_strategy_heuristicfreq {-1, 0, 5, 10, 20, 40, 80} [0]
mip_strategy_lbheur {yes, no} [no]
mip_strategy_nodeselect {0, 1, 2, 3} [1]
mip_strategy_presolvenode {-1, 0, 1, 2} [0]
mip_strategy_probe {-1, 0, 1, 2, 3} [0]
mip_strategy_rinsheur {-1, 0, 5, 10, 20, 40, 80} [0]
mip_strategy_search {0, 1, 2} [0]
mip_strategy_startalgorithm {0, 1, 2, 3, 4, 5, 6} [0]
mip_strategy_subalgorithm {0, 1, 2, 3, 4, 5} [0]
mip_strategy_variableselect {-1, 0, 1, 2, 3, 4} [0]
network_netfind {1, 2, 3} [2]
network_pricing {0, 1, 2} [0]
preprocessing_aggregator {-1, 0, 1, 4, 16, 64} [-1]
preprocessing_boundstrength {-1, 0, 1} [-1]
preprocessing_coeffreduce {0, 1, 2} [2]
preprocessing_dependency {-1, 0, 1, 2, 3} [-1]
preprocessing_dual {-1, 0, 1} [0]
preprocessing_fill [2, 40] [10]il
preprocessing_linear {0, 1} [1]
preprocessing_numpass {-1, 0, 1, 4, 16, 64} [-1]
preprocessing_reduce {0, 1, 2, 3} [3]
preprocessing_relax {-1, 0, 1} [-1]
preprocessing_repeatpresolve {-1, 0, 1, 2, 3} [-1]
preprocessing_symmetry {-1, 0, 1, 2, 3, 4, 5} [-1]
read_scale {-1, 0, 1} [0]
sifting_algorithm {0, 1, 2, 3, 4} [0]
simplex_crash {-1, 0, 1} [1]
simplex_dgradient {0, 1, 2, 3, 4, 5} [0]
simplex_limits_perturbation {0, 1, 4, 16, 64} [0]
simplex_limits_singularity [2, 40] [10]il
simplex_perturbation_switch {no, yes} [no]
simplex_pgradient {-1, 0, 1, 2, 3, 4} [0]
simplex_pricing {0, 1, 4, 16, 64} [0]
simplex_refactor {0, 4, 16, 64, 256} [0]
simplex_tolerances_markowitz [0.0001, 0.5] [0.01]l
mip_limits_strongcand [2, 40] [10]il
mip_limits_strongit {0, 1, 4, 16, 64} [0]
mip_strategy_order {yes, no} [yes]
perturbation_constant [1e-08, 0.0001] [1e-06]l

mip_strategy_order | mip_ordertype in {1, 2, 3}
mip_limits_strongcand | mip_strategy_variableselect in {3}
mip_limits_strongit | mip_strategy_variableselect in {3}
perturbation_constant | simplex_perturbation_switch in {yes}
'''

cs = pcs.read(io.StringIO(pcss))

params = convert_from_config_space(cs)

with io.StringIO() as buf, redirect_stdout(buf):
    irace_pkg.printParameters(params._export())
    output = buf.getvalue()

s = '''barrier_algorithm            "" c (0,1,2,3)      
barrier_crossover            "" c (-1,0,1,2)     
barrier_limits_corrections   "" c (-1,0,1,4,16,64)
barrier_limits_growth        "" r,log (1000000,100000000000000)
barrier_ordering             "" c (0,1,2,3)      
barrier_startalg             "" c (1,2,3,4)      
emphasis_memory              "" c (no)           
emphasis_mip                 "" c (0,1,2,3,4)    
emphasis_numerical           "" c (yes,no)       
feasopt_mode                 "" c (0,1,2,3,4,5)  
lpmethod                     "" c (0,1,2,3,4,5,6)
mip_cuts_cliques             "" c (-1,0,1,2,3)   
mip_cuts_covers              "" c (-1,0,1,2,3)   
mip_cuts_disjunctive         "" c (-1,0,1,2,3)   
mip_cuts_flowcovers          "" c (-1,0,1,2)     
mip_cuts_gomory              "" c (-1,0,1,2)     
mip_cuts_gubcovers           "" c (-1,0,1,2)     
mip_cuts_implied             "" c (-1,0,1,2)     
mip_cuts_mcfcut              "" c (-1,0,1,2)     
mip_cuts_mircut              "" c (-1,0,1,2)     
mip_cuts_pathcut             "" c (-1,0,1,2)     
mip_cuts_zerohalfcut         "" c (-1,0,1,2)     
mip_limits_aggforcut         "" i (0,10)         
mip_limits_cutpasses         "" c (-1,0,1,4,16,64)
mip_limits_cutsfactor        "" r,log (1,16)         
mip_limits_gomorycand        "" i,log (50,800)       
mip_limits_gomorypass        "" c (0,1,4,16,64)  
mip_limits_strongcand        "" i,log (2,40)          | (mip_strategy_variableselect == "3")
mip_limits_strongit          "" c (0,1,4,16,64)   | (mip_strategy_variableselect == "3")
mip_limits_submipnodelim     "" i,log (125,2000)     
mip_ordertype                "" c (0,1,2,3)      
mip_strategy_backtrack       "" c (0.9,0.99,0.999,0.9999,0.99999,0.999999)
mip_strategy_bbinterval      "" i,log (1,1000)       
mip_strategy_branch          "" c (-1,0,1)       
mip_strategy_dive            "" c (0,1,2,3)      
mip_strategy_file            "" c (0,1)          
mip_strategy_fpheur          "" c (-1,0,1,2)     
mip_strategy_heuristicfreq   "" c (-1,0,5,10,20,40,80)
mip_strategy_lbheur          "" c (yes,no)       
mip_strategy_nodeselect      "" c (0,1,2,3)      
mip_strategy_order           "" c (yes,no)        | (mip_ordertype %in% c("1", "2", "3"))
mip_strategy_presolvenode    "" c (-1,0,1,2)     
mip_strategy_probe           "" c (-1,0,1,2,3)   
mip_strategy_rinsheur        "" c (-1,0,5,10,20,40,80)
mip_strategy_search          "" c (0,1,2)        
mip_strategy_startalgorithm  "" c (0,1,2,3,4,5,6)
mip_strategy_subalgorithm    "" c (0,1,2,3,4,5)  
mip_strategy_variableselect  "" c (-1,0,1,2,3,4) 
network_netfind              "" c (1,2,3)        
network_pricing              "" c (0,1,2)        
perturbation_constant        "" r,log (0.00000001,0.0001) | (simplex_perturbation_switch == "yes")
preprocessing_aggregator     "" c (-1,0,1,4,16,64)
preprocessing_boundstrength  "" c (-1,0,1)       
preprocessing_coeffreduce    "" c (0,1,2)        
preprocessing_dependency     "" c (-1,0,1,2,3)   
preprocessing_dual           "" c (-1,0,1)       
preprocessing_fill           "" i,log (2,40)         
preprocessing_linear         "" c (0,1)          
preprocessing_numpass        "" c (-1,0,1,4,16,64)
preprocessing_reduce         "" c (0,1,2,3)      
preprocessing_relax          "" c (-1,0,1)       
preprocessing_repeatpresolve "" c (-1,0,1,2,3)   
preprocessing_symmetry       "" c (-1,0,1,2,3,4,5)
read_scale                   "" c (-1,0,1)       
sifting_algorithm            "" c (0,1,2,3,4)    
simplex_crash                "" c (-1,0,1)       
simplex_dgradient            "" c (0,1,2,3,4,5)  
simplex_limits_perturbation  "" c (0,1,4,16,64)  
simplex_limits_singularity   "" i,log (2,40)         
simplex_perturbation_switch  "" c (no,yes)       
simplex_pgradient            "" c (-1,0,1,2,3,4) 
simplex_pricing              "" c (0,1,4,16,64)  
simplex_refactor             "" c (0,4,16,64,256)
simplex_tolerances_markowitz "" r,log (0.0001,0.5)   
'''

assert output == s