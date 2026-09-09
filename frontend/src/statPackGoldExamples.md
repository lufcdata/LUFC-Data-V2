# Gold Stat Pack editorial benchmarks

These are benchmark sentence forms, not hard-coded facts. Figures/names may only be published when LUFC Data proves them.

- Leeds have lost 30 of their last 38 matches in London.
- Leeds have won just one of their last 19 league matches in London.
- All four of Leeds' away league defeats this season have come in London.
- Leeds have kept just two clean sheets in their last 41 competitive matches in London.
- [Player] has made more Leeds appearances in London without winning than any other player in the club's history.
- [Opponent] completed a league double over Leeds for the first time since the 1959/60 season.
- Leeds' last meeting with [opponent] produced their biggest winning margin against them since [historical result/date].
- Leeds are looking to record consecutive home league wins against [opponent] for the first time since [year].

## Chelsea fixture learning — 9 September 2026

The following examples are added as editorial learning for the Chelsea League Cup fixture. They are **story patterns**, not permanent hard-coded output. Before publishing, the Stat Pack must rebuild the population from canonical LUFC Data and prove the figures, date, venue and competition.

- **Opponent + stadium unbeaten run across all competitions:** “Chelsea are unbeaten at Stamford Bridge against Leeds in nine games across all competitions, winning seven and drawing two.” The machine should be able to identify an opponent's active unbeaten sequence at the exact physical stadium, even when the sequence spans more than one competition, and return the W/D/L split.
- **Last Leeds win at the exact stadium:** “Leeds' last win at Stamford Bridge was in December 1999 in the Premier League, a 2-0 victory.” Pair a long opponent/stadium run with the precise last Leeds win: month/year, competition and score.
- **Recent all-competition form with a low-defeat ceiling:** “Leeds have lost two of their last 16 games across all competitions (W7, D7, L2).” Search rolling all-competition windows, not only league form, and prefer the strongest concise low-defeat story when it is notable. The supplied W8/D5/L2 split was not used because it totals 15 and does not match the canonical last-16 population.
- **Early-season defensive record across league and cup:** “Leeds have conceded two goals in their four league and cup games so far.” At the start of a season, test combined competitive matches for goals conceded, clean sheets, goals scored and unbeaten/defeat context rather than waiting for large samples.
- **Competition progression frequency over prior campaigns:** “Leeds reached the League Cup fourth round once in the previous eight campaigns, in 2021/22.” For cup fixtures, inspect the same competition across a defined number of prior seasons and report how often Leeds reached the upcoming/next round, with the most recent qualifying campaign where useful.
- **Cup tie outcomes against opponents from a specified league level:** “Leeds have been eliminated from 17 of their last 22 League Cup ties against Premier League opponents, although they beat Nottingham Forest 2-0 in the previous round.” The machine should classify the opponent by the division they occupied **at the date of the tie**, build a chronological tie-level population rather than a raw match population, and calculate eliminations/progressions over a rolling number of qualifying ties. Where the latest qualifying tie breaks a strong historical trend, surface that contrast with opponent and score.
- **Multiple top-flight eliminations in one cup campaign:** “Leeds last knocked out two top-flight clubs in a single League Cup season in 2012/13 (Everton, Southampton).” For each cup campaign, count distinct opponents Leeds eliminated while those clubs were top-flight members at the time, then identify the most recent season meeting a threshold such as two or more and name the qualifying opponents.

### General rules learned from these examples

- Stadium history should use canonical physical-stadium identity, so naming/sponsorship changes never split the population.
- Opponent-at-stadium research must be able to span **all competitions** as well as exact competition populations.
- Where a current run is negative for Leeds, phrase it neutrally and precisely; pair it with the last Leeds success when that adds historical value.
- Recent-form windows may span league and cups when the story explicitly says “across all competitions”; never silently mix scopes.
- Early-season small samples are publishable when the wording clearly states the sample size (“four games so far”).
- Cup progression research is season-based: count campaigns reaching a specified round, not merely matches won in the competition.
- Cup opponent-strength research must use the opponent's league level in the season/date of the tie, never the club's current division.
- A cup **tie** is the analytical unit for elimination/progression stats. Two-legged ties must count once, with progression decided by the tie outcome rather than either individual leg.
- For “knocked out N top-flight clubs in a season” stories, count distinct eliminated opponents, not wins or matches, and preserve the opponent names as supporting evidence.
- Contrast clauses such as “although…” are valuable when the most recent result runs against a long-term trend, but both halves must be independently proven from canonical data.
- Every benchmark must be regenerated from the database before publication. A supplied stat that fails arithmetic, population or chronology checks is a research lead, not publishable evidence.

The benchmark is story-first: current fact → archive search → historical implication → concise football sentence.
