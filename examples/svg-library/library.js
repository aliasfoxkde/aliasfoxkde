(() => {
  const byId = (id) => document.getElementById(id);
  const controls = ['widget', 'name', 'tagline', 'variant', 'accent', 'stat-a', 'stat-b', 'stat-c'];
  const glyphs = {
    a:'01110/10001/10001/11111/10001/10001/10001', b:'11110/10001/10001/11110/10001/10001/11110', c:'01111/10000/10000/10000/10000/10000/01111',
    d:'11110/10001/10001/10001/10001/10001/11110', e:'11111/10000/10000/11110/10000/10000/11111', f:'11111/10000/10000/11110/10000/10000/10000',
    g:'01111/10000/10000/10111/10001/10001/01111', h:'10001/10001/10001/11111/10001/10001/10001', i:'111/010/010/010/010/010/111',
    j:'00111/00010/00010/00010/00010/10010/01100', k:'10001/10010/10100/11000/10100/10010/10001', l:'100/100/100/100/100/100/111',
    m:'100001/110011/101101/101101/100001/100001/100001', n:'10001/11001/10101/10011/10001/10001/10001', o:'01110/10001/10001/10001/10001/10001/01110',
    p:'11110/10001/10001/11110/10000/10000/10000', q:'01110/10001/10001/10001/10101/10010/01101', r:'11110/10001/10001/11110/10100/10010/10001',
    s:'01111/10000/10000/01110/00001/00001/11110', t:'11111/00100/00100/00100/00100/00100/00100', u:'10001/10001/10001/10001/10001/10011/01101',
    v:'10001/10001/10001/10001/10001/01010/00100', w:'100001/100001/100001/101101/101101/101101/010010', x:'10001/01010/00100/00100/00100/01010/10001',
    y:'10001/10001/10001/01010/00100/00100/00100', z:'11111/00001/00010/00100/01000/10000/11111',
    0:'01110/10001/10011/10101/11001/10001/01110', 1:'00100/01100/00100/00100/00100/00100/01110', 2:'01110/10001/00001/00010/00100/01000/11111',
    3:'11110/00001/00001/01110/00001/00001/11110', 4:'00010/00110/01010/10010/11111/00010/00010', 5:'11111/10000/10000/11110/00001/00001/11110',
    6:'01110/10000/10000/11110/10001/10001/01110', 7:'11111/00001/00010/00100/01000/01000/01000', 8:'01110/10001/10001/01110/10001/10001/01110',
    9:'01110/10001/10001/01111/00001/00001/01110', '-':'00000/00000/00000/11111/00000/00000/00000', '_':'00000/00000/00000/00000/00000/00000/11111'
  };
  let objectUrl = null;
  let format = 'svg';

  function xml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[char]));
  }
  function cleanText(value, max) { return String(value).trim().slice(0, max); }
  function color() { const value = byId('accent').value; return /^#[0-9a-f]{6}$/i.test(value) ? value : '#88e0c2'; }
  function wrapWords(value, max = 46) {
    const words = value.split(/\s+/).filter(Boolean).map((word) => word.length > max ? `${word.slice(0,max-1)}…` : word);
    const lines = [''];
    words.forEach((word) => {
      const current = lines[lines.length - 1];
      if (current && `${current} ${word}`.length > max && lines.length < 2) lines.push(word);
      else if (current) lines[lines.length - 1] = `${current} ${word}`;
      else lines[0] = word;
    });
    if (lines.length === 2 && lines[1].length > max) lines[1] = `${lines[1].slice(0,max-1)}…`;
    return lines;
  }
  function header(name, tagline, accent, variant) {
    const palettes = {
      aurora:['#101725','#2c244c','#b9f1d8'],
      blueprint:['#10243b','#193a52','#d4edff'],
      ember:['#2a1b2d','#653943','#ffe0aa']
    };
    const palette = palettes[variant] || palettes.aurora;
    const motif = variant === 'blueprint'
      ? '<path d="M0 40H900M0 80H900M0 120H900M0 160H900M0 200H900M100 0V260M200 0V260M300 0V260M400 0V260M500 0V260M600 0V260M700 0V260M800 0V260" stroke="#b7ddf2" stroke-opacity=".12"/><circle cx="740" cy="122" r="84" fill="none" stroke="#d4edff" stroke-opacity=".18"/><circle cx="740" cy="122" r="58" fill="none" stroke="#d4edff" stroke-opacity=".16"/>'
      : '<circle cx="760" cy="-8" r="158" fill="url(#orb)" opacity=".22"/><circle cx="846" cy="206" r="94" fill="none" stroke="url(#orb)" stroke-width="2" opacity=".55"/><path d="M620 216C680 152 726 254 804 181S881 127 927 166" fill="none" stroke="url(#orb)" stroke-width="2" opacity=".7"/>';
    const titleSize = name.length > 29 ? 28 : name.length > 21 ? 36 : 48;
    const taglineLines = wrapWords(tagline);
    const taglineSvg = taglineLines.map((line,index)=>`<tspan x="78" dy="${index ? 24 : 0}">${xml(line)}</tspan>`).join('');
    const strapY = taglineLines.length > 1 ? 207 : 195;
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 260" role="img" aria-labelledby="title desc"><title id="title">${xml(name)} profile header</title><desc id="desc">${xml(tagline)}</desc><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${palette[0]}"/><stop offset="1" stop-color="${palette[1]}"/></linearGradient><linearGradient id="orb" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${accent}"/><stop offset="1" stop-color="${palette[2]}"/></linearGradient></defs><rect width="900" height="260" rx="22" fill="url(#bg)"/>${motif}<rect x="42" y="42" width="5" height="176" rx="2.5" fill="${accent}"/><text x="76" y="116" fill="#fff" font-family="system-ui,-apple-system,Segoe UI,sans-serif" font-size="${titleSize}" font-weight="760" letter-spacing="-1.2">${xml(name)}</text><text x="78" y="157" fill="#e5e7ef" font-family="system-ui,-apple-system,Segoe UI,sans-serif" font-size="19">${taglineSvg}</text><text x="78" y="${strapY}" fill="${accent}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" letter-spacing="2">OPEN SOURCE · BUILD · SHARE</text></svg>`;
  }
  function summary(name, accent, values) {
    const labels = ['Public repositories','Project stars','Project forks'];
    const xs = [42, 335, 628];
    const blocks = labels.map((label,index) => { const size=values[index].length>9?22:values[index].length>6?30:40; return `<g transform="translate(${xs[index]} 28)"><rect width="260" height="144" rx="15" fill="#fff" stroke="#ded9ef"/><rect width="260" height="5" rx="2.5" fill="${accent}"/><text x="22" y="57" fill="#625c75" font-family="system-ui,sans-serif" font-size="14">${label}</text><text x="22" y="111" fill="#211b37" font-family="system-ui,sans-serif" font-size="${size}" font-weight="750">${xml(values[index])}</text></g>`; }).join('');
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 200" role="img" aria-labelledby="title"><title id="title">${xml(name)} project summary</title><rect width="900" height="200" rx="22" fill="#f7f6ff"/>${blocks}</svg>`;
  }
  function snake(name, accent) {
    const chars = [...cleanText(name, 18).toLowerCase()].filter((char) => char === ' ' || Object.hasOwn(glyphs, char));
    const safeChars = chars.length ? chars : [...'aliasfoxkde'];
    const cell = 6, gap = 1, stride = cell + gap, charGap = 3;
    let origin = 15;
    const pixels = [];
    const path = [];
    safeChars.forEach((char) => {
      if (char === ' ') { origin += 4 * stride + charGap; return; }
      const rows = glyphs[char].split('/');
      rows.forEach((row, rowIndex) => [...row].forEach((bit, columnIndex) => {
        if (bit !== '1') return;
        const x = origin + columnIndex * stride;
        const y = 15 + rowIndex * stride;
        pixels.push(`<rect x="${x}" y="${y}" width="${cell}" height="${cell}" rx="1.5" fill="${accent}"/>`);
        path.push([x + cell/2, y + cell/2]);
      }));
      origin += Math.max(...rows.map((row) => row.length)) * stride + charGap;
    });
    const width = Math.max(170, origin + 8);
    const points = path.map(([x,y]) => `${x},${y}`).join(' ');
    const first = path[0] || [18,18];
    const motion = points ? `<animate attributeName="cx" values="${path.map(([x])=>x).join(';')}" dur="${Math.max(6,path.length*.12)}s" repeatCount="indefinite" calcMode="discrete"/><animate attributeName="cy" values="${path.map(([,y])=>y).join(';')}" dur="${Math.max(6,path.length*.12)}s" repeatCount="indefinite" calcMode="discrete"/>` : '';
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} 78" role="img" aria-labelledby="title desc"><title id="title">Pixel snake spelling ${xml(safeChars.join(''))}</title><desc id="desc">A snake-style pixel wordmark. It is decorative and does not represent contribution activity.</desc><rect width="${width}" height="78" rx="12" fill="#111a20"/><g>${pixels.join('')}</g><circle cx="${first[0]}" cy="${first[1]}" r="4.2" fill="#f5ff9f" stroke="#173a27" stroke-width="1.5">${motion}</circle><circle cx="${first[0]+1}" cy="${first[1]-1}" r=".7" fill="#173a27"/><polyline points="${points}" fill="none" stroke="none"/></svg>`;
  }
  function current() {
    const name = cleanText(byId('name').value || 'aliasfoxkde', 40);
    const tagline = cleanText(byId('tagline').value || 'Open-source builder', 90);
    const accent = color();
    const widget = byId('widget').value;
    if (widget === 'stats') return {svg:summary(name,accent,[byId('stat-a').value,byId('stat-b').value,byId('stat-c').value]),width:900,height:200,file:'profile-summary.svg',alt:`${name} editable project summary`};
    if (widget === 'snake') return {svg:snake(name,accent),width:'auto',height:78,file:'profile-snake.svg',alt:`Pixel snake spelling ${name}`};
    return {svg:header(name,tagline,accent,byId('variant').value),width:900,height:260,file:'profile-header.svg',alt:`${name} profile header`};
  }
  function render() {
    const result = current();
    const blob = new Blob([result.svg],{type:'image/svg+xml;charset=utf-8'});
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(blob);
    const image = byId('preview-image'); image.src = objectUrl; image.alt = result.alt;
    byId('dimensions').textContent = result.width === 'auto' ? `Responsive width × ${result.height} · SVG` : `${result.width} × ${result.height} · SVG`;
    const snippet = `![${cleanText(byId('name').value || 'Profile',40)} profile graphic](./assets/${result.file})`;
    byId('output').value = format === 'svg' ? result.svg : snippet;
    document.querySelectorAll('[data-format]').forEach((button)=>button.setAttribute('aria-pressed',String(button.dataset.format===format)));
  }
  function announce(text) { byId('status').textContent = text; }
  async function copy(value, label) {
    try { await navigator.clipboard.writeText(value); announce(`${label} copied.`); }
    catch { byId('output').focus(); byId('output').select(); announce(`Copy access was unavailable. The ${label.toLowerCase()} is selected; copy it now.`); }
  }
  controls.forEach((id)=>byId(id).addEventListener('input',render));
  controls.forEach((id)=>byId(id).addEventListener('change',render));
  document.querySelectorAll('[data-format]').forEach((button)=>button.addEventListener('click',()=>{format=button.dataset.format;render();}));
  byId('download').addEventListener('click',()=>{const result=current();const blob=new Blob([result.svg],{type:'image/svg+xml;charset=utf-8'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=result.file;const url=link.href;link.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);announce(`${result.file} downloaded.`);});
  byId('copy-svg').addEventListener('click',()=>copy(current().svg,'SVG source'));
  byId('copy-markdown').addEventListener('click',()=>{const result=current();copy(`![${cleanText(byId('name').value || 'Profile',40)} profile graphic](./assets/${result.file})`,'Markdown embed');});
  render();
})();
