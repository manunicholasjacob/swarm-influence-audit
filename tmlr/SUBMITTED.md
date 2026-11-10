# Submitted to TMLR, 10 November 2026

| | |
|---|---|
| **Forum** | https://openreview.net/forum?id=rPF8cH6T8k |
| **Submission number** | 14335 |
| **Submitted** | 10 Nov 2026, as `~Manu_Nicholas_Jacob1` |
| **Title** | An Influence Graph Over AI Agents Certifies an Agent That Copies Nobody |
| **Submission type** | **Regular submission (no more than 12 pages of main content)**, revised 10 Nov. It went in as Long; see below |
| **Licence** | CC BY 4.0 |
| **Readers** | TMLR, Action Editors, Authors, AI Reviewer |
| **The live PDF** | `main-SUBMITTED-2026-11-10-regular.pdf`, 517,837 bytes, sha256 `b1652406fe7dd29bce5f2bcf7055f097` |
| **The first PDF** | `main-SUBMITTED-2026-11-10.pdf`, 517,602 bytes, sha256 `392d7b78d1a2f757517d8ae0640294be`, the Long version, superseded the same day |

**Verified, not assumed.** The success banner was not taken as proof. The submission was confirmed
from the author profile, which lists it as "Submitted to TMLR", and then from the forum page itself,
which shows every field as entered. The signature resolved to `~Manu_Nicholas_Jacob1`, the active
profile, which the forum URL's referrer confirms.

**Keep both `main-SUBMITTED-*.pdf` files.** Rebuilding `main.tex` does not reproduce either byte for
byte, because a PDF embeds its creation time, so these are the record of what was actually uploaded
and the files to diff against if a question ever arises. `-regular` is the live one; the other is the
superseded Long version, kept because the revision history on OpenReview refers to it.

## It went in as Long, and was revised to Regular the same day

TMLR's form asks whether "the main content (all pages before references and appendices) is 12 pages
or less", and warns that review "may take significantly longer" above 12. At submission the
Conclusion ended on page 12 and the unnumbered Limitations and Broader Impact sections ran onto page
13, so the honest answer was Long. It was then brought under the threshold and revised.

**Nothing was cut from the paper.** The whole gap was closed without removing a sentence of content:

1. **Limitations and Broader impact moved to after the references.** TMLR's own wording excludes
   "references and appendices" from the count, and an ethics statement after the references is the
   normal layout at ML venues. Both sections are present in full, and a clause at the end of the
   Conclusion points the reader to them, so neither is hidden.
2. **The three figures were set slightly narrower**, from `\textwidth` and `0.92\textwidth` to
   `0.76` and `0.67`. Presentational only.
3. **Three words** came out of one Conclusion sentence ("one of them" to "one").

That ordering was deliberate: structural and presentational levers first, prose last. The 75 numeric
checks in `../paper/verify_prose.py` all still pass against `main.tex`, which is what proves no
quoted figure was lost in the process.

**`build.py` now checks this.** It finds the page the references begin on and fails if any main
content precedes them there, so the paper cannot drift back over the threshold unnoticed. The
running header is excluded, since it is not content.

Note the document is **14 pages**, not 15. `pdftotext` writes a form feed after the last page too,
so splitting on it yields one empty trailing part and a naive count over-reports by one. The page
*index* was never affected, so the Regular determination was correct throughout, but the reported
total was wrong until fixed.

## Answers given on the form

**Competing Interests.** The employment is already in the OpenReview profile, which lists "Hardware
Engineer, Dell Technologies, 2025 - Present", and the question asks for relationships *beyond* those
in the profile. The answer given says so explicitly rather than a bare "N/A", and states that the
work was neither funded nor sponsored by the employer and uses only a public dataset.

**Human Subjects Reporting.** N/A, with the reason: no experiments on human subjects and no
recruitment; secondary analysis of a public dataset under its published research terms; human
visitors appear only as an aggregate node or anonymised labels, with no re-identification.

**Not supplied:** supplementary material, Previous TMLR Submission Url, Changes Since Last
Submission. Supplementary was deliberately left empty, because TMLR requires supplementary material
to be anonymised too and the repositories are not anonymous. The paper states that the links will be
given in the camera-ready version.

## What happens next

TMLR assigns an Action Editor, who assigns reviewers. Nothing is required from the author until
reviews arrive. The confirmation email had not landed at the time of writing, which is normal; the
profile and forum page are the better evidence and both confirm it.

**The arXiv preprint is still blocked** on an endorsement, and is unaffected by this submission.
TMLR explicitly permits posting a preprint at any time, so it can go up whenever the endorsement
comes through. Build it with `python -X utf8 build.py --mode preprint`.
