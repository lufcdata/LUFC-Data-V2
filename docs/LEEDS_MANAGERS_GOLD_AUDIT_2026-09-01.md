# Leeds Managers Gold Audit — 2026-09-01

## Scope

This audit will establish one authoritative Leeds managerial assignment for every one of the 4,856 LUFC fixtures while preserving the existing manager/spell source data as provenance.

## Golden rules

- One Leeds match -> one authoritative Leeds managerial authority assignment.
- Fixture responsibility outranks generic appointment/departure dates when a transition date is ambiguous.
- Committees are authority entities, not fake people.
- Caretaker/interim/permanent status is role metadata and must not be allowed to corrupt fixture ownership.
- Do not treat a whole multi-year spell as caretaker merely because the manager initially arrived as caretaker.
- Do not invent exact dates to close historical gaps.
- Existing Gold match, substitution and Opposition Manager layers must not be disturbed.
- User verification is required before Leeds Managers is Gold locked.

## Baseline inherited from live Supabase

- 4,856 matches
- 4,856 matches currently linked to a `manager_spell_id`
- 0 currently unassigned matches
- 49 canonical rows in `managers`
- 57 rows in `manager_spells`
- all 57 spell rows currently own at least one fixture

The current model is structurally complete, but it has not yet passed a forensic Gold audit.

## Immediate structural findings

### 1. The Board Committee — March to May 1935

The live model currently stores `The Board Committee` as a row in `managers`, with a caretaker spell from 6 Mar 1935 to 1 Jul 1935. It owns 12 fixtures, beginning Everton away on 6 Mar 1935 and ending Tottenham Hotspur at home on 4 May 1935.

This is semantically suspect as a person identity. If historical evidence supports committee control, Gold modelling should represent it as a managerial authority/committee rather than a fictional person.

### 2. Caretaker-to-permanent spells are conflated

The current `caretaker` boolean applies to an entire spell. This is already wrong or at least semantically lossy for several long spells labelled `Caretaker / Manager`, notably:

- David O'Leary — 203 matches, 1998-2002
- Peter Reid — 22 matches, 2003
- Kevin Blackwell — 115 matches, 2004-2006

Gold modelling must separate fixture authority from role period.

### 3. Short transition spells need exact fixture verification

High-risk examples include:

- Maurice Lindley — four caretaker spells
- Peter Gunby — two caretaker spells
- Dave Geddis — one match on 24 Oct 2006
- Gwyn Williams — one match on 29 Jan 2008
- Nigel Gibbs — one match on 1 Feb 2014 during the Brian McDermott dismissal/reinstatement episode
- Neil Redfearn — three caretaker spells plus a later permanent head-coach spell

## First chronological audit batch — 1920 to July 1935

### Arthur Fairclough

Live assignment:
- spell: 26 Feb 1920 to 10 Jun 1927
- fixture population: 309
- first database match: 28 Aug 1920
- last database match: 7 May 1927

The official Leeds United manager history lists Arthur Fairclough from February 1920 to May 1927. Independent Leeds statistical material also gives him 309 matches, matching the live fixture population exactly.

Initial verdict: **fixture population strongly consistent; exact administrative end date still to be normalised separately from match authority.**

### Dick Ray

Live assignment:
- spell: 11 Jun 1927 to 6 Mar 1935
- fixture population: 342
- first match: 27 Aug 1927
- last match: 2 Mar 1935

Official Leeds history places his second spell from July 1927 to March 1935. Independent Leeds statistics give 342 matches, again matching the live fixture population exactly. Other Leeds historical material says Ray resigned on 5 Mar 1935.

Initial verdict: **342-match fixture population strongly supported; exact date field requires date-level cleanup because live `date_left=1935-03-06` differs from sources placing resignation on 5 Mar / generic March.**

### 1935 transition

The live assignments are:
- 2 Mar 1935 Portsmouth: Dick Ray
- 6 Mar 1935 Everton: The Board Committee
- 9 Mar through 4 May: The Board Committee
- 31 Aug 1935 Stoke City: Billy Hampson

Official Leeds manager history lists Dick Ray through March 1935 and Billy Hampson from July 1935, omitting the interregnum as a named manager. That supports the existence of a non-individual authority gap, but not yet the exact constitutional label `The Board Committee`.

This 12-match block is therefore the first major forensic target.

### Billy Hampson

Live assignment:
- spell: 1 Jul 1935 to 30 Apr 1947
- fixture population: 217
- first match: 31 Aug 1935
- last match: 26 Apr 1947

Official Leeds manager history lists Hampson from July 1935 to May 1947. Independent Leeds statistics give 217 matches, exactly matching the database population.

Initial verdict: **fixture population strongly consistent.**

## Audit status

Leeds Managers is **NOT Gold**. The audit has begun with the earliest managerial era and has already isolated the first architectural problem: the 1935 committee must be treated as an authority question, not simply accepted as a person record.
