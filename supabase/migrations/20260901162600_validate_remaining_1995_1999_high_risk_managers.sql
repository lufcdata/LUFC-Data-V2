-- Provenance-only forensic validation of remaining high-risk 1995-1999 fixtures.
-- No canonical identity or authority changes are made here.

update managerial_assignments
set assignment_certainty = 'confirmed',
    provenance_status = 'forensically_validated',
    provenance_note = case match_id
      when 3284 then 'Mark McGhee confirmed as Leicester City manager for Leeds fixture on 15 Mar 1995. Leicester managerial chronology places McGhee in charge from Dec 1994 to Dec 1995 and direct season schedule lists him for this Leeds fixture.'
      when 3294 then 'Alan Smith confirmed as Crystal Palace manager for Leeds fixture on 9 May 1995. Contemporary Independent reporting on the Leeds defeat explicitly identifies Smith as Crystal Palace manager.'
      when 3326 then 'Jimmy Quinn and Mick Gooding confirmed as joint Reading managers for Leeds League Cup fixture on 10 Jan 1996; relational assignment already represents both people under joint authority.'
      when 3331 then 'Barry Fry confirmed as Birmingham City manager for League Cup semi-final first leg against Leeds on 11 Feb 1996; direct match sheet lists Fry as Birmingham manager.'
      when 3334 then 'Barry Fry confirmed as Birmingham City manager for League Cup semi-final second leg against Leeds on 25 Feb 1996; direct match record lists Fry as Birmingham manager.'
      when 3344 then 'Dave Merrington confirmed as Southampton manager for Leeds fixture on 3 Apr 1996. Contemporary Independent preview on the day of the match explicitly identifies Merrington as Saints manager.'
      when 3431 then 'Christian Gross confirmed as Tottenham Hotspur manager for Leeds fixture on 4 Mar 1998. Direct match sheet lists Gross as Spurs manager.'
      when 3432 then 'Mark McGhee confirmed as Wolverhampton Wanderers manager for FA Cup quarter-final against Leeds on 7 Mar 1998. Direct match sheet and contemporary reporting identify McGhee as Wolves manager.'
      when 3506 then 'Yuri Semin confirmed as Lokomotiv Moscow head coach for UEFA Cup first leg at Leeds on 21 Oct 1999. 1999 Lokomotiv managerial records list Semin as head coach and the tie chronology is continuous across both legs.'
      when 3509 then 'Yuri Semin confirmed as Lokomotiv Moscow coach for UEFA Cup second leg against Leeds on 4 Nov 1999. Contemporary Irish Times preview explicitly describes Lokomotiv as coach Yuri Syomin''s side.'
      else provenance_note
    end
where match_id in (3284,3294,3326,3331,3334,3344,3431,3432,3506,3509);
