# Music theory for chord-progression validation

Read this when you want to **sanity-check a chord progression** — is the key right,
are the chords plausible, is one likely mis-transcribed? It backs
`scripts/analyze-progression.py`, which turns the workflow below into a repeatable
gate. The mental model matches how many players chart by ear: **find the key, then
think in scale degrees** (幾級和弦 / Nashville numbers), and notice when a chord
doesn't belong.

This is a *sanity gate, not an oracle*. Its job is to surface "look here," not to
overrule your ears. Unusual ≠ wrong.

## Contents

1. [The workflow: key → degrees → check](#the-workflow)
2. [Finding the key (circle of fifths + key-fit)](#finding-the-key)
3. [The relative major/minor trap](#relative-majorminor)
4. [Roman numerals & Nashville numbers](#degrees)
5. [Diatonic-fit labels](#fit-labels)
6. [The transition matrix (rock corpus)](#transition-matrix)
7. [Reading the analyzer's verdict](#reading-the-verdict)
8. [Honest caveats](#caveats)
9. [Sources](#sources)

## The workflow

1. **Find the key** — the tonic (home chord) and mode (major/minor). Everything
   downstream is relative to it.
2. **Re-express each chord as a scale degree** — `G` in the key of C is the `V`
   (Nashville `5`); `Am` is the `vi` (`6m`). This is the transposition-invariant
   view a relative-pitch player already hears.
3. **Check plausibility on two independent axes:**
   - *Diatonic fit* — is each chord in the key, a common borrowing, or foreign?
   - *Transition likelihood* — is each chord-to-chord move common in real pop?
4. **Flag the conjunction** — a chord that is **both out-of-key and reached by a
   rare move** is the strongest "probably mis-transcribed" signal.

`analyze-progression.py song.cho` runs all four and prints the verdict.

## Finding the key

**Key-fit scoring.** For each of the 24 candidate keys (12 major + 12 minor), score
how well the chords fit: reward chords that are diatonic (in the key's scale),
penalize foreign chords by their **circle-of-fifths distance** from the tonic (a
chord one step around the circle — like `V`-of-`V` or `bVII` — is closely related
and cheap; a tritone away is far and expensive). The best-scoring key wins.

The **circle of fifths** orders roots by perfect fifths (C→G→D→A→E→B→F♯→…). Distance
on the circle is a good proxy for harmonic relatedness: a key's own diatonic chords
cluster near its tonic, so counting diatonic membership and discounting the strays
by circle distance is a lightweight stand-in for the classic Krumhansl–Schmuckler
key-profile method (which `music21` implements, if you want the heavier cross-check).

**Diatonic triads** (the 7 chords built on each scale degree):

| | I | ii | iii | IV | V | vi | vii° |
|---|---|---|---|---|---|---|---|
| **Major** | maj | min | min | maj | maj | min | dim |

| | i | ii° | III | iv | v / V | VI | VII / vii° |
|---|---|---|---|---|---|---|---|
| **Natural minor** | min | dim | maj | min | min | maj | maj |

Minor is looser: the raised 6th/7th of harmonic & melodic minor make `V` (major),
`vii°`, and a major-`IV` diatonic-in-context too, so the analyzer treats both the
natural and raised forms as "in key."

## Relative major/minor

C major and A minor share the **exact same seven notes** — so the pitch-class set
*alone cannot tell them apart*. This is the single most common key-detection error
(MIREX even awards partial credit for a relative/parallel mix-up). Disambiguate with
**tonic-emphasis cues, not the note set**:

- **The last chord** — progressions overwhelmingly end on the tonic. Strongest cue.
- **The first chord** — usually the tonic too.
- **Cadences** — `V→I` nails major; `V→i`, `bVII→i`, or `iv→i` nails minor.

When these cues are weak the key is *genuinely ambiguous*. The analyzer then reports
**low confidence and names the runner-up** ("A minor … or C major?") rather than
committing — that's honest, and it warns you the downstream numerals could flip.
Consequence to remember: analyzing a C-major song as A minor re-labels a plain
`V→I` (`G→C`) as the flat-side `bVII→bIII`, which then looks "rare." A pile of rare
flags on a low-confidence key often just means the key guess is off by a relative.

## Degrees

**Roman numerals** encode degree + quality: uppercase = major (`I IV V`), lowercase
= minor (`ii iii vi`), `°` = diminished, `+` = augmented, a leading `b`/`#` marks a
chromatic root (`bVII`, `#iv`), and a `/note` shows a slash bass (`I/D`). Sevenths
and extensions ride along (`V7`, `IVmaj7`).

**Nashville numbers** are the same idea with digits — `1 4 5` for the majors, `6m`
for vi, `5` for the V — which is exactly the "幾級和弦" shorthand. `analyze-progression.py`
prints both columns.

**Spelling is key-relative, not pitch-class arithmetic.** The degree comes from the
chord's *letter name* against the key's scale letters (so in F major, `Bb` is `IV`,
not `#III`), and the accidental from the pitch difference. Get the key wrong and the
numerals cascade wrong — another reason the tool leads with key confidence.

## Fit labels

Each chord gets one label:

- **diatonic** — built on a scale degree with the expected quality. The default.
- **secondary** — a `V/x`: a major/dominant chord a fifth above a diatonic degree
  (e.g. `B7` in G major is `V/vi`, the dominant of `Em`). Extremely common; colorful,
  not wrong.
- **borrowed** — from the parallel mode or common modal mixture (`bVII`, `bVI`,
  `bIII`, a major tonic in a minor key / Picardy). Also idiomatic.
- **out-of-key** — none of the above. *This* is what's worth a second look — but
  only becomes a "suspect" when a rare transition also points at it (below).

## Transition matrix

The analyzer scores each chord-to-chord **move** against a first-order transition
matrix built from a real pop/rock corpus — **de Clercq & Temperley's "A Corpus
Analysis of Rock Harmony" (2011), Table 3**, a 12×12 count matrix over Roman-numeral
roots from 99 analyzed songs. Why an empirical *rock* prior and not textbook theory:
rock legitimately does things classical harmony calls errors — `V→IV` happens ~26%
of the time in rock vs ~7% in classical, and `bVII→IV→I` ("double plagal") is a
signature move. A classical prior would over-flag perfectly normal pop.

Key facts baked in: `I`, `IV`, `V`, `bVII`, `VI` account for ~87% of all chords;
the most common pre-tonic chords are `IV`, then `V`, then `bVII`; the top cadential
trigrams are `IV V I`, `V IV I`, `bVII IV I`.

**Important — root categories only.** The corpus collapses chord *quality* and folds
applied chords into their root (so `ii` and `V/V` are one category, `II`). Transition
scoring therefore works on the **scale-degree root relative to the tonic** (a
semitone interval, mode-independent) — which is also why a minor-key song keeps its
own tonic as `I` and its chords land on the flat-side categories (`bIII`, `bVI`,
`bVII`) exactly as the corpus was built. The quality-aware Roman/Nashville labels are
a separate layer the analyzer computes itself.

A move rarer than ~3% is flagged **"review — surprising, maybe intentional."** It is
*not* called wrong: a first-order model can't see voice-leading, a modulation, or a
deliberate surprise.

## Reading the verdict

```
Key: G major   [confidence: high]

Chord   Roman   Nash  Fit
G       I       1     diatonic
B7      III7    3     secondary(V/vi)
Em7     vi7     6m    diatonic
Cmaj7   IVmaj7  4     diatonic
D7      V7      5     diatonic

Transition check: no improbable moves — progression is idiomatic.
Progression plausibility: 0.96
```

- **Key line** — the detected key + confidence, or a given `--key`. Low confidence
  names the runner-up; take the numerals with a grain of salt when it's low.
- **Per-chord table** — degrees + fit label. Scan the `Fit` column for `out-of-key`.
- **Transition check** — only the improbable moves, aggregated with counts. Frame as
  "review," never "error."
- **SUSPECT list** — the payload: chords that are **out-of-key AND reached by a rare
  move**. These are the ones actually worth re-checking against the recording. A rare
  move *into a diatonic chord* is "unusual but fine"; a borrowed chord reached by a
  *common* move is "colorful, fine." Only the conjunction is a red flag.
- **Warnings** — repeated adjacent chords (a held chord, or a redundant/mis-typed
  double) and chords trailing past a line's last syllable (an instrumental beat, or a
  floater to fold into a bar). Advisory — some are faithful to the arrangement.
- **Plausibility** — `0.5·diatonic-fit + 0.5·transition-likelihood`, a rough 0–1
  gauge. Low means "look closer," not "broken."

Use it as a **tie-breaker** too: when two fetched charts disagree, the one with the
higher plausibility / fewer suspects is usually the better transcription.

## Caveats

- **First-order only.** It sees pairs of chords, not phrases — so it can't tell a
  modulation or a set-up-and-resolve from a mistake. Hence "review," not "wrong."
- **Rock-descriptive, not prescriptive.** The prior describes what pop *does*, not
  what's "allowed." Jazz, gospel, and art-pop will trip more flags and still be fine.
- **Relative/parallel ambiguity is real.** Low confidence means the key (and thus the
  numerals) could flip; confirm the tonic by ear.
- **Enharmonic spelling follows the key.** A chart that spells `D#` where the key
  wants `Eb` will get a slightly-off degree label — cosmetic, not a harmony error.
- **`music21` escalation.** For a Krumhansl/Aarden key cross-check or rigorous
  secondary-dominant/augmented-sixth analysis, run `analyze-progression.py` under
  `uv run --with music21`; the core stays zero-dependency by default.

## Sources

- de Clercq, T. & Temperley, D. (2011). "A Corpus Analysis of Rock Harmony."
  *Popular Music* 30(1): 47–70. Cambridge University Press.
  doi:10.1017/S026114301000067X — the transition/marginal tables.
- **Rock Corpus** — https://rockcorpus.midside.com (CC BY 4.0; RS 200 / v2.1). Cite
  the article for the numbers; attribute the corpus for the dataset.
- UMass *Fundamentals of Music Theory*, Unit 18 — pop-vs-classical two-chord table
  (secondary corroboration): https://fundamentalsofmusictheory.umasscreate.net/unit-18/
- Krumhansl–Schmuckler key finding — https://rnhart.net/articles/key-finding/ ;
  Temperley (1999) KS re-evaluation.
- `music21` (optional escalation) — roman numerals
  https://music21.org/music21docs/moduleReference/moduleRoman.html ; key profiles
  https://music21.org/music21docs/moduleReference/moduleAnalysisDiscrete.html
- Open Music Theory — Harmonic Functions:
  https://openmusictheory.github.io/harmonicFunctions.html
