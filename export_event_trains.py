"""Export the analysed channels as event trains, so a continuous-time estimator can be run on them.

Why this file exists. The report's central caution is that a turn-ordered discretisation plus a
permutation surrogate is a PRACTICAL repair, not the principled one. The principled route for data
that is genuinely a set of events in continuous time is a continuous-time estimator, and Shorten,
Spinney and Lizier provide one (CoTETE.jl). We did not run it, and Appendix A says so.

That comparison is the single largest gap between this report and a full paper, and the thing
blocking it is not the analysis but the plumbing: getting the real channels out of a gated,
scaffolded corpus and into the shape a Julia package expects. This does that plumbing once, so the
comparison becomes a short script rather than a project.

What it writes, per channel:

  <channel>_events.json    every agent's speaking times in seconds from window start, plus the
                           symbol it used, plus the metadata needed to reproduce the selection
  <channel>_trains.csv     the same thing flat: agent, t_seconds, symbol
  run_cotete.jl            a ready Julia script that reads the JSON and runs pairwise
                           continuous-time TE, with the parameters the report used where they carry
                           over, and explicit TODOs where they do not

Nothing here touches message text, and humans are excluded unless asked for, so the export carries
no content and no identities: it is timestamps and small-alphabet symbol ids only.

Usage:  python export_event_trains.py [--out DIR] [--days 14] [--k 8]
"""
from __future__ import annotations

import argparse
import json
import pathlib

import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
CHANNELS = (("main-village", GENERAL), ("open-chat-village", None))

JULIA = r'''# Continuous-time transfer entropy on the exported AI Village event trains.
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
'''


def export(village: str, room_id: str | None, out: pathlib.Path, days: int, k: int) -> dict:
    msgs, names, rooms = S.load_village(village)
    room = room_id or S.busiest_room(msgs)
    span, lo, hi = S.cut_window(msgs, room, days=days)
    S.symbolise(span, k=k, seed=0)
    agents = S.select_agents(span, min_msgs=50, top_k=15)
    keep = set(agents)
    sub = sorted([m for m in span if m["_sp"] in keep], key=lambda m: (m["_t"], m["id"]))
    if not sub:
        raise SystemExit(f"{village}: no messages selected")

    t0 = sub[0]["_t"]
    alphabet = sorted({m["_topic"] for m in sub})
    sym_id = {s: i for i, s in enumerate(alphabet)}

    trains: dict[str, dict] = {a: {"t": [], "symbol": []} for a in agents}
    for m in sub:
        trains[m["_sp"]]["t"].append(round(float(m["_t"] - t0), 3))
        trains[m["_sp"]]["symbol"].append(sym_id[m["_topic"]])

    rec = {
        "village": village,
        "room": room,
        "window_days": days,
        "window_seconds": round(float(sub[-1]["_t"] - t0), 3),
        "n_events": len(sub),
        "n_agents": len(agents),
        "alphabet_size": len(alphabet),
        "symboliser": f"TopicSymboliser(k={k}, seed=0)",
        "agents": list(agents),
        "trains": trains,
        "note": ("Times are seconds from the first selected message. Symbols are small-alphabet "
                 "topic-cluster ids, not text. No message content and no human participants are "
                 "included, so this export carries no identities."),
    }

    stem = f"{village}_{('general' if room_id else 'busiest')}"
    (out / f"{stem}_events.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    lines = ["agent,t_seconds,symbol"]
    for a in agents:
        for t, s in zip(trains[a]["t"], trains[a]["symbol"]):
            lines.append(f"{a},{t},{s}")
    (out / f"{stem}_trains.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="cotete_export")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--k", type=int, default=8)
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = []
    for village, room_id in CHANNELS:
        rec = export(village, room_id, out, args.days, args.k)
        summary.append({kk: rec[kk] for kk in
                        ("village", "room", "n_events", "n_agents", "window_seconds",
                         "alphabet_size")})
        print(f"{rec['village']}: {rec['n_events']} events, {rec['n_agents']} agents, "
              f"{rec['window_seconds']:.0f}s window, alphabet {rec['alphabet_size']}")

    (out / "run_cotete.jl").write_text(JULIA, encoding="utf-8")
    (out / "export_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nwrote {out}/ including run_cotete.jl")
    print("Julia is NOT installed here, so the comparison has not been run. That is the point:")
    print("the plumbing is done, the analysis is one script away.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
