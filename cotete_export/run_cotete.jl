# Continuous-time transfer entropy on the exported AI Village event trains.
#
# This script is the comparison the report says it did not attempt. It is written to be run, not
# read: install the dependency, point it at the exported JSON, and it prints a pairwise table.
#
#   julia> import Pkg
#   julia> Pkg.add(url="https://github.com/dpshorten/CoTETE.jl")
#   julia> Pkg.add(["JSON", "Printf"])
#   julia> include("run_cotete.jl")
#
# What to compare against, from the report (turn-ordered, lag 1, symbol-permutation surrogate):
#   main-village  #general   2 certified edges
#   open-chat     #general   18 certified edges
# If the continuous-time estimator broadly agrees, the practical recipe is validated. If it
# disagrees, that disagreement is a more interesting result than agreement would have been, and it
# is the reason to run this at all.

using JSON, Printf
import CoTETE

const EXPORT = length(ARGS) >= 1 ? ARGS[1] : "main-village_general_events.json"

data = JSON.parsefile(EXPORT)
agents = collect(keys(data["trains"]))
@printf("%s: %d agents, window %.1f s\n", EXPORT, length(agents), data["window_seconds"])

# CoTETE expects sorted event times per process, as Vector{Float64}.
trains = Dict(a => Float64.(data["trains"][a]["t"]) for a in agents)

# Parameters. The report used history length 1 on the turn-ordered grid; in continuous time the
# analogous choice is the number of preceding events considered, which is NOT the same thing and
# should be swept rather than assumed.
# TODO: sweep these rather than trusting the defaults.
params = CoTETE.CoTETEParameters(
    l_x = 1,          # source history events
    l_y = 1,          # target history events
    auto_find_start_and_num_events = true,
)

println("\nsource -> target : TE (nats/second)")
results = Dict{Tuple{String,String},Float64}()
for src in agents, tgt in agents
    src == tgt && continue
    length(trains[src]) < 20 && continue
    length(trains[tgt]) < 20 && continue
    te = CoTETE.estimate_TE_from_event_times(params, trains[tgt], trains[src])
    results[(src, tgt)] = te
    @printf("%-28s -> %-28s : %10.6f\n", src, tgt, te)
end

# TODO: surrogates. CoTETE provides a local-permutation surrogate, which is the point of using it:
# it is the same idea as the report's symbol-permutation repair, applied in continuous time. Run it
# per pair and apply a max-T family-wise correction across all ordered pairs, exactly as the report
# does, so the two sets of certified edges are comparable rather than merely both present.
println("\nTODO: add surrogates and the max-T family-wise correction before comparing edge sets.")
