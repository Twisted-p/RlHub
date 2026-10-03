(function(root) {
  function advice(data, now = Date.now()) {
    const day = new Intl.DateTimeFormat('en-CA', {timeZone:'Europe/Oslo',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
    const recent = (data.recent || []).filter(r => Date.parse(r.at) <= now && now-Date.parse(r.at) < 24*60*60*1000);
    const losses = recent.filter(r => !r.win).length;
    const wins = recent.length-losses;
    if (!data.current) return {title:'Start med et utgangspunkt', text:'Hent rank i Profile. Varm opp i fem minutter, og velg én ferdighet du vil jobbe med i dag.', reason:'Ingen rank hentet for denne spillmodusen.', action:'Hent rank', href:'./profile.html'};
    if (data.focusSeconds >= 5400) return {title:'Gi deg selv en ordentlig pause', text:'Du har vært i økten i minst 90 minutter. Ta 15 minutter uten trening eller kamp før du vurderer en ny runde.',reason:'Lang økt registrert i RL Hub.', action:'Se pausetimeren', href:'#session-focus-clock'};
    if (recent.length >= 3 && losses >= 3 && losses > wins) return {title:'Nullstill hodet, ikke målet',text:'Flere tap enn seiere i de siste kampene. Ta en pause, og se etter én situasjon du kan løse bedre neste gang. En vanskelig økt trenger ikke bli en vanskelig dag.',reason:`${losses} tap i ${recent.length} siste ranked-kamper fra siste døgn.`,action:'Se kampene',href:'./performance.html'};
    if (data.weekDelta !== null && data.weekDelta <= -20) return {title:'Bygg trygghet før du jager poeng',text:'MMR har gått ned den siste uken. Velg en kort treningspakke og fokuser på gode ballberøringer og trygge returer. Se etter én forbedring i neste kamp.',reason:`${data.weekDelta} MMR mellom målingene siste sju dager.`,action:'Finn en treningspakke',href:'./training-packs.html'};
    if (data.weekDelta !== null && data.weekDelta >= 20) return {title:'Ta med deg det som fungerer',text:'Du har løftet MMR den siste uken. Hold på rutinene som har fungert, og legg inn pauser mens du fortsatt har overskudd.',reason:`+${data.weekDelta} MMR mellom målingene siste sju dager.`,action:'Se Performance',href:'./performance.html'};
    if (recent.length >= 3 && wins >= 3) return {title:'Behold rytmen',text:'Du har flere seiere å bygge videre på. Ta fem minutter pause og en kort oppvarming før neste blokk. Gode vaner er også progresjon.',reason:`${wins} seiere i ${recent.length} siste ranked-kamper fra siste døgn.`,action:'Åpne Training',href:'./training.html'};
    const tips = [
      ['Små steg teller','Velg én ferdighet for dagens økt. Øv i fem minutter og prøv å bruke den bevisst i neste kamp.'],
      ['Gjør neste berøring litt bedre','Fokuser på hvor ballen havner etter en berøring. Fem minutter med rolige ground shots gir deg ett konkret mål for neste økt.'],
      ['Spill med et tydelig fokus','Velg én ting du vil gjøre bedre i dag: skuddplassering, ballkontroll eller returer. Vurder innsatsen på den ferdigheten etter økten.']
    ];
    const index = [...day].reduce((sum, char) => sum+char.charCodeAt(0),0)%tips.length;
    return {title:tips[index][0],text:tips[index][1],reason:data.weekDelta === null ? 'Flere rankmålinger trengs for å vurdere utviklingen.' : 'Ingen tydelig endring i MMR siste sju dager.',action:'Velg trening',href:'./training-packs.html'};
  }
  const api = {advice};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.RLProgression = api;
})(typeof window !== 'undefined' ? window : globalThis);
