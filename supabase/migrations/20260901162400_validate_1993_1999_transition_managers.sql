-- Opposition Managers Gold forensic validation batch: 1993-1999.
-- No canonical identity or authority corrections in this migration.
-- Preserve matches.opposition_manager_raw as immutable provenance.

update public.managerial_assignments
set assignment_certainty='confirmed',
    provenance_status='forensically_validated',
    provenance_note=case match_id
      when 3219 then 'John Gorman confirmed as Swindon Town manager for Leeds fixture on 27 Nov 1993; season records and match-specific sources place him in charge.'
      when 3247 then 'John Gorman confirmed as Swindon Town manager for Leeds fixture on 7 May 1994; he remained manager throughout Swindon''s 1993/94 Premier League season.'
      when 3238 then 'Phil Neal confirmed as Coventry City manager for Leeds fixture on 19 Mar 1994; Coventry appointed him after Bobby Gould resigned in Oct 1993.'
      when 3253 then 'Phil Neal confirmed as Coventry City manager for Leeds fixture on 17 Sep 1994; match-specific sources name him as manager.'
      when 3254 then 'Andy King confirmed as Mansfield Town manager for League Cup first leg versus Leeds on 21 Sep 1994.'
      when 3257 then 'Andy King confirmed as Mansfield Town manager for League Cup second leg versus Leeds on 4 Oct 1994; contemporary reporting names him as Mansfield manager.'
      when 3258 then 'John Deehan confirmed as Norwich City manager for Leeds fixture on 8 Oct 1994; match-specific historical source identifies Deehan as Norwich manager.'
      when 3276 then 'Graeme Sharp confirmed as Oldham Athletic player-manager for Leeds FA Cup fixture on 28 Jan 1995; he took over in Nov 1994.'
      when 3403 then 'John Ward confirmed as Bristol City manager for League Cup first leg versus Leeds on 17 Sep 1997; his Bristol City managerial spell began in Mar 1997.'
      when 3407 then 'John Ward confirmed as Bristol City manager for League Cup second leg versus Leeds on 30 Sep 1997; his Bristol City managerial spell continued through 1998.'
      when 3470 then 'Brian Kidd confirmed as Blackburn Rovers manager for Leeds fixture on 9 Jan 1999; contemporary reporting describes his recent arrival as manager.'
      when 3504 then 'Brian Kidd confirmed as Blackburn Rovers manager for League Cup fixture at Leeds on 13 Oct 1999; contemporary match report names him as Blackburn manager.'
      when 3510 then 'Egil Olsen confirmed as Wimbledon manager for Leeds fixture on 7 Nov 1999; contemporary reporting describes Wimbledon under his guidance.'
      when 3511 then 'Paul Jewell confirmed as Bradford City manager for Leeds fixture on 20 Nov 1999; match-specific source names him as Bradford manager.'
      else provenance_note
    end
where match_id in (3219,3247,3238,3253,3254,3257,3258,3276,3403,3407,3470,3504,3510,3511);
