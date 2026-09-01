# LUFC Data V2 — Substitutions Gold Sign-off
Date: 2026-09-01

## Decision
**SUBSTITUTE RELATIONSHIP LAYER: GOLD LOCKED**

Corrected substitution population: **5,112** entry/replacement events.

The previous raw structured total of 5,111 is superseded by the proven Joël Piroe appearance at Brighton & Hove Albion on 17 May 2026. The corrected appearance population is therefore **58,528 = 53,416 starts + 5,112 substitute appearances**.

## Final QA
- Substitution events: 5,112
- Unique match + incoming player pairs: 5,112
- Unresolved incoming player IDs: 0
- Unresolved outgoing player IDs: 0
- Duplicate incoming player in same match: 0
- Duplicate outgoing player in same match: 0
- Self replacements: 0
- Known-timing chronology failures: 0
- Known substitution timings: 4,167
- Unknown substitution timings retained as NULL: 945
- 46' half-time substitutions: 319
- Stoppage-time substitutions: 167
- Substitute-substituted events: 36

## Locked interpretation rules
1. Player 1–11 remains authority for starters.
2. Corrected Sub population is authority for substitute appearances.
3. A player in a substitution parenthesis replaces the player immediately governing that parenthesis.
4. Multiple substitute names in one parenthesis encode a sequential chain: A → B → C.
5. Nested parentheses encode the same sequential relationship explicitly.
6. 46' is a half-time substitution.
7. 45+X and 90+X are preserved as base minute + stoppage minute.
8. Historical substitutions without a minute retain minute NULL.
9. A dismissal does not create a substitution.
10. A player leaving without replacement does not create a player_on event.
11. Relationship certainty and timing certainty are separate.
12. Raw source text is retained for provenance.

## Locked corrections / regressions
- Brighton 17 May 2026: Anton Stach OFF 74' → Joël Piroe ON 74'. Piroe is missing from structured Sub slots but present in both narrative substitution fields.
- Cardiff City 8 Jan 2023: Darko Gyabi OFF 59' → Max Wöber ON 59'. Raw source conflicts (60'/69'); 59' is the confirmed correction.
- Sheffield United 25 Sep 2010: Lloyd Sam OFF 60' → Robert Snodgrass ON 60'. Snodgrass dismissal remains a separate 88' event.
- Tottenham Hotspur 18 Mar 1972: Terry Cooper → Paul Reaney is the substitution; Peter Lorimer leaving injured at 89' has no replacement and is not counted as a replacement substitution.
- Newport County 7 Jan 2018: Jay-Roy Grot OFF 75' → Samuel Saiz ON 75'; Saiz's later dismissal is separate.
- Mateo Joseph / Fernandez resolves to one player. Existing Gold regression remains 73 appearances = 16 starts + 57 sub appearances.
- Max Wöber / Wober, Clarke Oduor / Odour, and straight/curly apostrophe forms are identity aliases, not separate players.

## Substitute + dismissal regression set
All ten known substitute-then-sent-off cases retain the substitute entry and keep dismissal separate:
- Match 1841: Mick Bates ON minute unknown for Eddie Gray
- Match 3848: Richard Cresswell ON 78' for Rob Hulse
- Match 4030: Tresor Kandol ON 81' for Jermaine Beckford
- Match 4063: Tresor Kandol ON 90' for Andrew Hughes
- Match 4081: Robert Snodgrass ON 60' for Lloyd Sam
- Match 4113: Billy Paynter ON 67' for Luciano Becchio
- Match 4255: Matt Smith ON 46' for Tom Lees
- Match 4370: Alex Mowatt ON 69' for Mirco Antenucci
- Match 4459: Samuel Saiz ON 75' for Jay-Roy Grot
- Match 4624: Pascal Struijk ON 33' for Diego Llorente

## First Gold leaderboards
### Subbed On
1. Wilfried Gnonto — 69
2. Patrick Bamford — 63
3. John Pearson — 60
4. Mateo Joseph — 57
5. Sam Byram — 55
6. Jamie Shackleton — 55
7. Stuart Dallas — 52
8. Tyler Roberts — 48
9. Luciano Becchio — 44
10. Daniel James — 44
11. Joe Gelhardt — 43
12. Darren Huckerby — 42
13. Joël Piroe — 42
14. Ian Moore — 41
15. Mick Bates — 40

### Subbed Off
1. Luciano Becchio — 86
2. Jack Harrison — 86
3. Brenden Aaronson — 79
4. Mateusz Klich — 77
5. Patrick Bamford — 71
6. Rod Wallace — 63
7. Daniel James — 62
8. Wilfried Gnonto — 62
9. Stuart Dallas — 59
10. Neil Kilkenny — 53
11. Pablo Hernandez — 53
12. Gjanni Alioski — 52
13. Robert Snodgrass — 51
14. Harry Kewell — 50
15. Robbie Blake — 50

### Substitute Substituted
1. Carl Shutt — 2
2. Gaetano Berardi — 2
3. Tom Pearce — 2
4. Pablo Hernandez — 2
5. Rodrigo — 2
6. Daniel James — 2
7. John Stiles — 1
8. John Pearson — 1
9. Gary McAllister — 1
10. Steve Hodge — 1
11. Scott Sellars — 1
12. Matthew Jones — 1
13. Darren Huckerby — 1
14. Tony Hackworth — 1
15. Mark Viduka — 1

## Timing note
The replacement relationship layer is Gold. Timing is Gold only where supported by the source/correction evidence. There are 945 replacement events with unknown historical timing; these remain NULL and are not estimated. A small number of externally reconstructed historical chains retain timing-conflict provenance even though the OFF→ON relationship itself is locked.
