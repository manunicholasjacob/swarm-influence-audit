# The TMLR manuscript

> **SUBMITTED 10 November 2026.** Forum https://openreview.net/forum?id=rPF8cH6T8k, submission
> number 14335. See `SUBMITTED.md` for the exact state, including why it went in as a Long
> submission and how to change that. **`main-SUBMITTED-2026-11-10.pdf` is the file that was
> uploaded; do not delete it**, because rebuilding does not reproduce it byte for byte.

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

## The LLM-use disclosure is required, and its location is specified

TMLR's FAQ requires it. The wording, read from `jmlr.org/tmlr/faq.html` on 10 Nov 2026, is that
authors must "mention explicitly in their submission that they have used this tool", "as a footnote
on the first page". The editorial-policies page separately states that LLMs "are not eligible for
authorship" and that authors are "fully responsible" for the content regardless of tools used.

So the disclosure is not a style choice and cannot be dropped. Two consequences shaped the file:

1. **It is a first-page footnote**, not a line in Broader Impact, which is where it sat until 10 Nov.
   `build.py` checks the rendered page rather than the source, because a footnote can be pushed to
   the following page by the material around it.
2. **No vendor is named.** Nothing in the policy asks for one, so the footnote says "a large
   language model". All three built PDFs contain zero occurrences of any vendor name.

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

1. ~~**Decide the voice.**~~ **Settled: first-person singular.** Checked against the source on
   10 Nov: neither TMLR's author guide nor its editorial policies constrain pronouns, and general
   style guidance accepts or prefers "I" for single-author work. Nothing to change.
2. **The arXiv preprint needs an endorser.** `main-preprint.pdf` is ready; the endorsement request
   is outstanding, see `../../swarm-alignment-2026/outgoing/00_DISPATCH_LOG.md`.
3. ~~**Fill the forum id into `\openreview`.**~~ Done: `rPF8cH6T8k`. It is used only by the accepted
   and preprint builds, so filling it did not change the anonymous PDF.
4. **Supplementary material must also be anonymised** if any is ever uploaded. The author guide is
   explicit about that, and the repositories are not anonymous, so the submission uploaded none and
   the paper promises the links at camera-ready.
5. **Optional: convert to a Regular submission.** It went in as Long because the main content runs
   onto page 13. `SUBMITTED.md` explains how to get it under 12 and why that was not done
   unilaterally.
