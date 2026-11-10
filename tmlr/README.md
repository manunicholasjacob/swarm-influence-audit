# The TMLR manuscript

Built 10 November 2026. `main.tex` is the only source. Three PDFs come out of it and they cannot
drift apart, because the mode is chosen at build time rather than by editing the file.

```
python -X utf8 build.py              # all three, with the anonymity check
python -X utf8 build.py --mode submission
```

| mode | output | author block | repository URLs and benchmark name |
|---|---|---|---|
| `submission` | `main.pdf` | **hidden** | **withheld** |
| `preprint` | `main-preprint.pdf` | shown | shown |
| `accepted` | `main-accepted.pdf` | shown | shown |

`main.pdf` is the file to upload to OpenReview. `main-preprint.pdf` is the arXiv version, which
still needs an endorser.

## Why the anonymity gate is tested on the PDF and not the source

TMLR's author guide says a non-anonymous submission is **rejected without review**. The gate here is
a LaTeX conditional, `\ifdeanon`, and a conditional can be wired backwards. So `build.py` extracts
the text of the built PDF and greps it for the author's name, email, both repository URLs and the
benchmark's distinctive name. It fails the build if the submission PDF contains any of them, and
also fails if the preprint build is **missing** them, because a gate stuck shut would quietly
produce an arXiv preprint with no author on it.

That second direction already caught a real mistake. The gate was first written against
`\if@preprint`, which hid the repository URLs from the camera-ready as well, in the one build where
the paper promises to give them. The correct flag is `\if@accepted`, which `tmlr.sty` sets for both
`[preprint]` and `[accepted]` and leaves false only for the anonymous submission.

The check is wired into `../verify_all.py`, so it runs with everything else.

## What the numbers are checked against

`../paper/verify_prose.py` recomputes 78 figures from the committed JSONs in `swarm-bench` and
asserts that each appears in both `../paper/00_PROSE_v1.md` and `main.tex`. Three of the 78 are
scoped to the prose file: they belong to the superseded 30-replicate sweep, which the manuscript
deliberately does not quote.

The verifier normalises LaTeX before searching, so `$[0.046, 0.105]$` matches the computed
`[0.046, 0.105]` and `$p = 2.7 \times 10^{-10}$` matches `2.7e-10`.

## Provenance of the style files

`tmlr.sty`, `tmlr.bst`, `fancyhdr.sty` and `math_commands.tex` were taken on 10 Nov 2026 from
`https://github.com/JmlrOrg/tmlr-style-file/archive/refs/heads/main.zip`, which is the source named
by TMLR's own author guide. Nothing else from that archive is used; the example PDFs and template
were discarded.

**Those four files are not mine and are not under this repository's MIT licence.** They are
redistributed from the JmlrOrg project under the **Apache License 2.0**, whose text is in
`LICENSE-tmlr-style` in this directory. Apache 2.0 requires the licence to travel with the files, so
it is committed here rather than linked. Everything else in this directory is covered by the
repository's own licence.

## Still to do before submission

1. **Decide the voice.** The manuscript is first-person singular throughout, which is the choice
   recorded in the slot workbook. The sprint report says "we". Single-author "I" is accepted at
   TMLR but unusual, and switching is one mechanical pass. This is the only stylistic decision left.
2. **The arXiv preprint needs an endorser.** `main-preprint.pdf` is ready; the endorsement request
   is outstanding, see `../../swarm-alignment-2026/outgoing/00_DISPATCH_LOG.md`.
3. **An OpenReview submission needs the forum id** filled into `\openreview` for the camera-ready.
   It is a placeholder now and is not used in the anonymous build.
4. **Supplementary material must also be anonymised** if any is uploaded. The author guide is
   explicit about that, and the repositories are not anonymous, so either upload an anonymised
   archive or upload nothing and give the links at camera-ready, which is what the paper currently
   promises.
