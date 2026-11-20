// Desenho gerado (grade de pixels) — ver comentários em carro.js abaixo.
const CARRO_PIXELS = {"corpo":[".........................KKKKKKKKKKKKKKKKKKKKKKKKK................","........................KRRRRRRRRRRRRRRRRRRRRRRRRRK...............",".......................KKRRRRRRRRRRRRRRRRRRRRRRRRRKKKKK...........",".....................KKCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCK..........","....................KCKKKKKKKKKKBBKKKKKKKKKKBBKKKKKKKKBBK.........","..................KKKKJJJJJJJJJJKKGGGGGGGGGGKKGGGGGGGGKBK.........",".................KCKJJJJJJJJJJJJKKGGGGGggGGGKKGGGGGgGGKBBK........","................KCKJJJJJJJJJJJJJKKGGGGggGGGGKKGGGGgGGGKBBK........","..............KKKKJJJJJJJJJJJJJJKKGGGggGGGGGKKGGGgGGGGKBBK........",".............KCKJJJJJJJJJJJJJJJJKKGGggGGGGGGKKGGgGGGGGKBBK........","....KKKKKKKKKCKJJJJJJJJJJJJJJJJJKKGGGGGGGGGGKKGGGGGGGGKBBK.KKK....","..KKCCCCCCCCCLBKKKKKKKKKKKKKKKKKBBKKKKKKKKKKBBKKKKKKKKBBBKKSSSK...",".KBLLLLLLLLLLLLLLLLLLLLLLLLLLLLLkLLLLLLLLLLLkLLLLLLLLLLLLLBSSSSK..",".KBLLLLLLLLLLLLOOLLLLLLLLLLLLLLLkLLLLLLLLLLLkLLLLLLLLLLLLLBSSSSSK.",".KWWHHBBBBBBDDDDBBBBBBBBBhhhBBBBkBBBBBhhhBBBkBBBDDDDBBBBBTTSssSSK.",".KHHHHBBBBDDKKKKDDBBBBBBBBBBBBBBkBBBBBBBBBBBkBDDKKKKDDBBBTTSssSSK.",".KBBBBBBDDKK....KKDDBBBBBBBBBBBBkBBBBBBBBBBBDDKK....KKDDBTTSssSSK.",".KMMMMMDDK........KDDMMMMMMMMMMMkMMMMMMMMMMDDK........KDDMMSssSSK.",".KDDDDDDK..........KDDDDDDDDDDDDkDDDDDDDDDDDK..........KDDDSssSSK.",".KYYDDDK............KDDDDDDDDDDDkDDDDDDDDDDK............KDDSSSSSK.",".KDDDDDK............KDDDDDDDDDDDkDDDDDDDDDDK............KDDSSSSK..",".KDDDDK..............KDDDDDDDDDDkDDDDDDDDDK..............KDSSSK...",".KDDDDK..............KDUUUUUUUUUUUUUUUUUUDK..............KDKKK....","..KKKK................KKKKKKKKKKKKKKKKKKKK................K.......","..................................................................","..................................................................","..................................................................","..................................................................","..................................................................",".................................................................."],"roda":[[".....KKKKK.....","...KKPPPPPKK...","..KKPPPPPPPKK..",".KKPPPPwPPPPKK.",".KPPPwqwqwPPPK.","KPPPwqqwqqwPPPK","KPPPqqqKqqqPPPK","KPPwwwKKKwwwPPK","KPPPqqqKqqqPPPK","KPPPwqqwqqwPPPK",".KPPPwqwqwPPPK.",".KKPPPPwPPPPKK.","..KKPPPPPPPKK..","...KKPPPPPKK...",".....KKKKK....."],[".....KKKKK.....","...KKPPPPPKK...","..KKPPPPPPPKK..",".KKPPPPwPPPPKK.",".KPPwwqqqwwPPK.","KPPPwwqqqwwPPPK","KPPPqqqKqqqPPPK","KPPwqqKKKqqwPPK","KPPPqqqKqqqPPPK","KPPPwwqqqwwPPPK",".KPPwwqqqwwPPK.",".KKPPPPwPPPPKK.","..KKPPPPPPPKK..","...KKPPPPPKK...",".....KKKKK....."]],"rodas":[[7,15],[43,15]]};

/* =========================================================================
   O carrinho do Sinaleiro
   Um SUV em pixel art passa pela estrada no rodapé do site, freia, abaixa o
   vidro e o motorista cumprimenta. As rodas giram de acordo com a
   velocidade real do carro, então desaceleram junto com ele na freada.
   ========================================================================= */
(() => {
  const estrada = document.querySelector("[data-estrada]");
  if (!estrada) return;

  const reduzido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const FALA_IDA = "Oii, Edgar!!\nEsse trabalho vale 10 pontos";
  const FALA_VOLTA = "Olha lá, hein!\nVamos cobrar nossos 10 pontos! rsrs";
  const COLS = 66, LINHAS = 30;

  const PALETA = {
    K: "#15171B", R: "#3A3F47", C: "#8FD0FA", L: "#4FA3EE", B: "#2B6FD6", M: "#2459B4",
    D: "#1C4596", k: "#173A80", h: "#B9D6F5", G: "#2C3542", g: "#56677C", J: "#1B2028",
    H: "#F4F6F8", W: "#FFFFFF", Y: "#F6D66B", O: "#F07A1A", T: "#B8321F", U: "#2A2D33",
    S: "#2F3245", s: "#4A4E66", P: "#3F4263", w: "#E9ECF2", q: "#9AA1AE",
    // motorista
    c: "#4A2E1B", f: "#F2C29B", e: "#15171B", m: "#9B3B2A", r: "#E0312A", b: "#F29A8E",
  };

  // Motorista (posição relativa à janela; '.' = transparente)
  const BONECO = { x: 24, y: 5, grade: [
    ".cccccc.",
    "cccccccc",
    "cfefffe.",
    "cfbfffb.",
    ".ffmmff.",
    "rrrrrrrr",
  ]};
  const MAOS = [
    { x: 20, y: 5, grade: ["ff..", "ff..", ".rr.", "..rr"] },   // mão para cima
    { x: 19, y: 6, grade: ["ff...", "ff...", ".rrr.", "...rr"] }, // mão inclinada
  ];

  // Junta pixels vizinhos da mesma cor em retângulos (SVG bem mais leve).
  function pixels(grade, ox = 0, oy = 0, filtro = () => true, cor = null) {
    let s = "";
    grade.forEach((linha, y) => {
      let x = 0;
      while (x < linha.length) {
        const ch = linha[x];
        if (ch === "." || !filtro(ch)) { x++; continue; }
        let fim = x;
        while (fim + 1 < linha.length && linha[fim + 1] === ch) fim++;
        s += `<rect x="${x + ox}" y="${y + oy}" width="${fim - x + 1}" height="1" fill="${cor || PALETA[ch]}"/>`;
        x = fim + 1;
      }
    });
    return s;
  }

  const corpo = CARRO_PIXELS.corpo;
  // Janela do motorista: células 'J' viram a máscara do vidro e do boneco.
  let mascara = "";
  corpo.forEach((linha, y) => [...linha].forEach((ch, x) => {
    if (ch === "J") mascara += `M${x} ${y}h1v1h-1z`;
  }));
  const vidro = corpo.map((linha, y) => [...linha].map((ch, x) =>
    ch !== "J" ? "." : ((x + y) % 9 === 0 || (x + y) % 9 === 1) && y < 10 ? "g" : "G").join(""));

  const roda = (frame) => pixels(CARRO_PIXELS.roda[frame]);
  const svg = `
<svg class="carro-svg" viewBox="0 0 ${COLS} ${LINHAS}" shape-rendering="crispEdges" aria-hidden="true">
  <defs><clipPath id="janela-motorista"><path d="${mascara}"/></clipPath></defs>
  <g class="c-carroceria">
    ${pixels(corpo, 0, 0, (ch) => ch !== "T")}
    <g class="c-lanterna">${pixels(corpo, 0, 0, (ch) => ch === "T")}</g>
    <g clip-path="url(#janela-motorista)">
      <g class="c-boneco">
        ${pixels(BONECO.grade, BONECO.x, BONECO.y)}
        <g class="c-boca">${pixels(["ee", "mm"], 27, 9)}</g>
        <g class="c-mao c-mao-0">${pixels(MAOS[0].grade, MAOS[0].x, MAOS[0].y)}</g>
        <g class="c-mao c-mao-1">${pixels(MAOS[1].grade, MAOS[1].x, MAOS[1].y)}</g>
      </g>
      <g class="c-vidro">${pixels(vidro)}</g>
    </g>
  </g>
  ${CARRO_PIXELS.rodas.map(([x, y]) => `
  <g class="c-roda" transform="translate(${x} ${y})">
    <g class="c-roda-0">${roda(0)}</g><g class="c-roda-1">${roda(1)}</g>
  </g>`).join("")}
</svg>`;

  const carro = document.createElement("div");
  carro.className = "carro";
  carro.innerHTML = `${svg}<span class="buzina-fx">BI-BI!</span><div class="balao" role="presentation"><span class="balao-texto"></span></div>`;
  estrada.querySelector(".estrada-pista").append(carro);

  const carroceria = carro.querySelector(".c-carroceria");
  const vidroEl = carro.querySelector(".c-vidro");
  const boneco = carro.querySelector(".c-boneco");
  const balao = carro.querySelector(".balao");
  const balaoTexto = carro.querySelector(".balao-texto");

  const espera = (ms) => new Promise((r) => setTimeout(r, ms));

  /* ---------- Som: buzina sintetizada e falas gravadas -------------------- *
   * Navegadores (principalmente o Safari do iPhone) só liberam áudio dentro de
   * um toque/clique. No primeiro toque o código "destrava" tudo de uma vez:
   * retoma o AudioContext, toca um buffer mudo e pré-aquece os <audio> das
   * falas — depois disso eles podem tocar sozinhos no meio da animação.   */
  const Som = {
    ctx: null,
    desbloqueado: false,
    ligado: (() => { try { return localStorage.getItem("sinaleiro-som") !== "off"; } catch { return true; } })(),
    falas: {
      ida: criarAudio(estrada.dataset.audioIda),
      volta: criarAudio(estrada.dataset.audioVolta),
    },
    contexto() {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      if (!this.ctx) this.ctx = new AC();
      if (this.ctx.state !== "running") this.ctx.resume().catch(() => {});
      return this.ctx;
    },
    /* Precisa rodar de forma síncrona dentro do evento de toque/clique. */
    desbloquear() {
      // iOS: trata como reprodução de mídia (toca mesmo com a chave de silencioso).
      try { if (navigator.audioSession) navigator.audioSession.type = "playback"; } catch {}
      const ctx = this.contexto();
      if (ctx) {
        const buffer = ctx.createBuffer(1, 1, 22050);
        const fonte = ctx.createBufferSource();
        fonte.buffer = buffer; fonte.connect(ctx.destination); fonte.start(0);
      }
      Object.values(this.falas).forEach((audio) => {
        if (!audio || audio.dataset.pronto || !audio.paused) return;
        audio.muted = true;
        audio.play().then(() => {
          audio.pause(); audio.currentTime = 0; audio.muted = false; audio.dataset.pronto = "1";
        }).catch(() => { audio.muted = false; });
      });
      this.desbloqueado = true;
      mostrarAvisoSom(false);
    },
    liberado() {
      return this.desbloqueado || Boolean(this.ctx && this.ctx.state === "running"
        && navigator.userActivation && navigator.userActivation.hasBeenActive);
    },
    avisarBloqueio() {
      if (this.ligado && !this.liberado()) mostrarAvisoSom(true);
    },
    bipe() {   // confirmação curta ao ativar o som
      const ctx = this.contexto();
      if (!ctx) return;
      const t = ctx.currentTime + 0.03;
      [[660, 0], [990, 0.09]].forEach(([freq, atraso]) => {
        const osc = ctx.createOscillator(), vol = ctx.createGain();
        osc.type = "square"; osc.frequency.value = freq;
        vol.gain.setValueAtTime(0.08, t + atraso);
        vol.gain.exponentialRampToValueAtTime(0.0001, t + atraso + 0.08);
        osc.connect(vol).connect(ctx.destination);
        osc.start(t + atraso); osc.stop(t + atraso + 0.09);
      });
    },
    buzina() {
      if (!this.ligado) return;
      const ctx = this.contexto();
      if (!ctx) return;
      this.avisarBloqueio();
      const t0 = ctx.currentTime + 0.02;
      const toque = (inicio, dur) => {
        const volume = ctx.createGain();
        volume.gain.setValueAtTime(0.0001, inicio);
        volume.gain.exponentialRampToValueAtTime(0.22, inicio + 0.015);
        volume.gain.setValueAtTime(0.22, inicio + dur - 0.04);
        volume.gain.exponentialRampToValueAtTime(0.0001, inicio + dur);
        const filtro = ctx.createBiquadFilter();
        filtro.type = "lowpass"; filtro.frequency.value = 2100; filtro.Q.value = 2;
        filtro.connect(volume).connect(ctx.destination);
        [392, 494].forEach((freq) => {          // dois tons, como buzina de carro
          const osc = ctx.createOscillator();
          osc.type = "square"; osc.frequency.value = freq;
          osc.connect(filtro); osc.start(inicio); osc.stop(inicio + dur + 0.02);
        });
      };
      toque(t0, 0.16);          // bi
      toque(t0 + 0.24, 0.36);   // biii
    },
    /* Toca a fala gravada; resolve quando termina (ou na hora, se bloqueada). */
    tocarFala(nome) {
      const audio = this.falas[nome];
      if (!this.ligado || !audio) return Promise.resolve();
      return new Promise((pronto) => {
        const limite = setTimeout(pronto, ((audio.duration || 5) + 1.5) * 1000);
        const fim = () => { clearTimeout(limite); pronto(); };
        audio.onended = fim;
        audio.muted = false;
        audio.currentTime = 0;
        audio.play().catch(() => { mostrarAvisoSom(true); fim(); });
      });
    },
    parar() {
      Object.values(this.falas).forEach((audio) => audio && audio.pause());
    },
  };

  function criarAudio(url) {
    if (!url) return null;
    const audio = new Audio(url);
    audio.preload = "auto";
    audio.setAttribute("playsinline", "");
    return audio;
  }

  const avisoSom = estrada.querySelector("[data-som-aviso]");
  function mostrarAvisoSom(mostrar) {
    if (!avisoSom) return;
    avisoSom.hidden = !mostrar;
    estrada.classList.toggle("som-bloqueado", mostrar);
  }
  // touchend/click são os eventos que o iOS aceita para liberar áudio.
  ["touchend", "click", "keydown"].forEach((ev) =>
    document.addEventListener(ev, () => { if (Som.ligado) Som.desbloquear(); }, { capture: true }));

  const botaoSom = estrada.querySelector("[data-som]");
  const atualizarBotaoSom = () => {
    if (!botaoSom) return;
    botaoSom.setAttribute("aria-pressed", String(Som.ligado));
    botaoSom.querySelector(".som-rotulo").textContent = Som.ligado ? "Som ligado" : "Som desligado";
    estrada.classList.toggle("som-mudo", !Som.ligado);
  };
  botaoSom?.addEventListener("click", (ev) => {
    ev.stopPropagation();
    Som.ligado = !Som.ligado;
    try { localStorage.setItem("sinaleiro-som", Som.ligado ? "on" : "off"); } catch {}
    if (Som.ligado) { Som.desbloquear(); Som.bipe(); } else { Som.parar(); mostrarAvisoSom(false); }
    atualizarBotaoSom();
  });
  botaoSom?.addEventListener("keydown", (ev) => ev.stopPropagation());
  atualizarBotaoSom();

  // Tocar no aviso libera o som e, se o carro já passou, chama ele de novo.
  avisoSom?.addEventListener("click", (ev) => {
    ev.stopPropagation();
    if (!Som.ligado) { Som.ligado = true; try { localStorage.setItem("sinaleiro-som", "on"); } catch {} atualizarBotaoSom(); }
    Som.desbloquear();
    Som.bipe();
    if (!rodando) setTimeout(cena, 300);
  });
  avisoSom?.addEventListener("keydown", (ev) => ev.stopPropagation());

  // Ao abrir a tela: se o navegador ainda não liberou o áudio, mostra o aviso.
  if (Som.ligado) {
    const ctx = Som.contexto();
    const semClique = navigator.userActivation ? !navigator.userActivation.hasBeenActive : true;
    setTimeout(() => { if (!Som.desbloqueado && (semClique || (ctx && ctx.state !== "running"))) mostrarAvisoSom(true); }, 300);
  }

  const tamanhoPixel = () => (window.innerWidth < 640 ? 3 : 4);
  const posicaoX = () => new DOMMatrixReadOnly(getComputedStyle(carro).transform).m41;

  /* Rodas e suspensão acompanham a velocidade: a cada ~2 pixels percorridos
     o desenho da roda troca de quadro; a carroceria balança a cada ~9. */
  let motor = null;
  function ligarMotor(px) {
    let ultimoX = posicaoX(), giro = 0, balanco = 0, quadro = 0, sobe = false;
    const passo = () => {
      const x = posicaoX();
      const dx = Math.abs(x - ultimoX);
      ultimoX = x;
      giro += dx; balanco += dx;
      if (giro >= px * 2.2) { quadro ^= 1; carro.dataset.roda = quadro; giro = 0; }
      if (balanco >= px * 9) { sobe = !sobe; carroceria.style.translate = sobe ? "0 -1px" : "0 0"; balanco = 0; }
      motor = requestAnimationFrame(passo);
    };
    motor = requestAnimationFrame(passo);
  }
  function desligarMotor() {
    cancelAnimationFrame(motor);
    carroceria.style.translate = "0 0";
  }

  // sentido: -1 = andando para a esquerda (desenho original), +1 = para a direita (espelhado)
  function fumaca(px, sentido) {
    const xEscape = sentido < 0 ? 58 : COLS - 60;
    for (let i = 0; i < 4; i++) {
      const p = document.createElement("i");
      p.className = "fumaca";
      p.style.left = `${xEscape * px}px`;
      p.style.bottom = `${7 * px}px`;
      p.style.setProperty("--s", `${px * (2 + (i % 2))}px`);
      carro.append(p);
      const dx = -sentido * (18 + i * 10) * (px / 4);
      p.animate(
        [{ transform: "translate(0,0) scale(1)", opacity: .85 },
         { transform: `translate(${dx}px, ${-(10 + i * 7) * (px / 4)}px) scale(2.2)`, opacity: 0 }],
        { duration: 700 + i * 160, delay: i * 90, easing: "steps(6)", fill: "forwards" },
      ).finished.then(() => p.remove());
    }
  }

  async function digitar(texto) {
    balaoTexto.textContent = "";
    for (const letra of texto) {
      balaoTexto.textContent += letra;
      await espera(letra === "\n" ? 520 : letra === "," ? 180 : 52);
    }
  }

  /* Posiciona o balão acima da janela do motorista sem sair da tela. */
  function posicionarBalao(texto, px, xCarro, sentido) {
    balaoTexto.textContent = texto;
    const largura = balao.offsetWidth;
    balaoTexto.textContent = "";
    const janela = (sentido < 0 ? 26 : COLS - 26) * px;     // centro da janela, dentro do carro
    const pista = estrada.clientWidth;
    let esquerda = janela - largura * (sentido < 0 ? .3 : .7);
    esquerda = Math.max(12 - xCarro, Math.min(esquerda, pista - 12 - largura - xCarro));
    balao.style.setProperty("--balao-x", `${Math.round(esquerda)}px`);
    balao.style.setProperty("--cauda", `${Math.round(Math.max(16, Math.min(largura - 24, janela - esquerda)))}px`);
  }

  function limparAnimacoes() {
    [carro, vidroEl, boneco, carroceria].forEach((el) => el.getAnimations().forEach((a) => a.cancel()));
  }

  /* Uma passagem: entra por um lado, freia, cumprimenta e sai pelo outro. */
  async function passagem({ sentido, fala, audio, buzinar, paradaRel }) {
    const px = tamanhoPixel();
    carro.style.setProperty("--px", `${px}px`);
    carro.classList.toggle("virado", sentido > 0);
    const largura = COLS * px;
    const pista = estrada.clientWidth;
    // Para antes da faixa de pedestres, do lado de onde vem.
    const faixa = estrada.querySelector(".faixa-pedestre");
    const folga = px * 3;
    let alvo = pista * paradaRel - largura / 2;
    if (faixa) {
      alvo = sentido < 0 ? faixa.offsetLeft + faixa.offsetWidth + folga
                         : faixa.offsetLeft - folga - largura;
    }
    const parada = Math.round(Math.max(16, Math.min(pista - largura - 16, alvo)));
    const foraDireita = pista + 20, foraEsquerda = -largura - 60;
    const [inicio, fim] = sentido < 0 ? [foraDireita, foraEsquerda] : [foraEsquerda, foraDireita];
    posicionarBalao(fala, px, parada, sentido);
    carro.classList.add("visivel");

    if (reduzido) {
      carro.style.transform = `translateX(${parada}px)`;
      vidroEl.style.transform = "translateY(7px)";
      boneco.style.transform = "none";
      balaoTexto.textContent = fala;
      balao.classList.add("aberto");
      await espera(4200);
      balao.classList.remove("aberto");
      vidroEl.style.transform = boneco.style.transform = "";
      carro.classList.remove("visivel");
      return;
    }

    // 1. Chega e freia até parar.
    ligarMotor(px);
    const chegada = carro.animate(
      [{ transform: `translateX(${inicio}px)` }, { transform: `translateX(${parada}px)` }],
      { duration: 2600, easing: "cubic-bezier(.22,.75,.32,1)", fill: "forwards" },
    );
    const freio = setTimeout(() => carro.classList.add("freando"), 1500);
    await chegada.finished;
    desligarMotor();
    carroceria.animate(   // mergulho da frente na freada
      [{ rotate: "0deg" }, { rotate: "-1.6deg" }, { rotate: ".4deg" }, { rotate: "0deg" }],
      { duration: 520, easing: "ease-out" },
    );
    await espera(380);

    // Buzina (só na ida) antes de abaixar o vidro.
    if (buzinar) {
      Som.buzina();
      carro.classList.add("buzinando");
      carroceria.animate(
        [{ translate: "0 0" }, { translate: "0 -1px" }, { translate: "0 0" }, { translate: "0 -1px" }, { translate: "0 0" }],
        { duration: 600, easing: "steps(5)" },
      );
      await espera(900);
      carro.classList.remove("buzinando");
    }

    // 2. Abaixa o vidro, o motorista aparece e acena.
    await vidroEl.animate([{ transform: "translateY(0)" }, { transform: "translateY(7px)" }],
      { duration: 650, easing: "steps(7)", fill: "forwards" }).finished;
    await boneco.animate([{ transform: "translateY(7px)" }, { transform: "translateY(0)" }],
      { duration: 320, easing: "steps(4)", fill: "forwards" }).finished;
    const aceno = setInterval(() => carro.classList.toggle("acenando"), 220);

    // 3. Fala, letra por letra.
    balao.classList.add("aberto");
    await espera(240);
    const boca = setInterval(() => carro.classList.toggle("falando"), 110);
    const falaPronta = Som.tocarFala(audio);   // voz gravada
    await digitar(fala);
    await falaPronta;
    clearInterval(boca);
    carro.classList.remove("falando");
    await espera(2200);

    // 4. Fecha a janela e arranca.
    balao.classList.remove("aberto");
    clearInterval(aceno);
    carro.classList.remove("acenando");
    await boneco.animate([{ transform: "translateY(0)" }, { transform: "translateY(7px)" }],
      { duration: 240, easing: "steps(3)", fill: "forwards" }).finished;
    await vidroEl.animate([{ transform: "translateY(7px)" }, { transform: "translateY(0)" }],
      { duration: 520, easing: "steps(7)", fill: "forwards" }).finished;
    clearTimeout(freio);
    carro.classList.remove("freando");
    fumaca(px, sentido);
    await espera(260);
    carroceria.animate([{ rotate: "0deg" }, { rotate: "1.2deg" }, { rotate: "0deg" }], { duration: 600, easing: "ease-out" });
    ligarMotor(px);
    const veloz = setTimeout(() => carro.classList.add("veloz"), 500);
    await carro.animate(
      [{ transform: `translateX(${parada}px)` }, { transform: `translateX(${fim}px)` }],
      { duration: 1900, easing: "cubic-bezier(.55,0,.85,.45)", fill: "forwards" },
    ).finished;
    clearTimeout(veloz);
    desligarMotor();
    carro.classList.remove("visivel", "veloz");
    limparAnimacoes();
    balaoTexto.textContent = "";
  }

  var rodando = false;   // var: lido também pelo aviso de som, declarado acima
  async function cena() {
    if (rodando) return;
    rodando = true;
    try {
      await passagem({ sentido: -1, fala: FALA_IDA, audio: "ida", buzinar: true, paradaRel: .6 });      // ida
      await espera(reduzido ? 300 : 1100);
      await passagem({ sentido: +1, fala: FALA_VOLTA, audio: "volta", buzinar: false, paradaRel: .42 }); // volta
    } finally {
      rodando = false;
    }
  }

  // O carro passa em todas as telas, para todos os usuários.
  // Clicar na estrada (ou Enter/Espaço nela) chama o carro de novo.
  setTimeout(cena, document.querySelector(".tela-login") ? 1400 : 900);
  estrada.addEventListener("click", cena);
  estrada.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); cena(); }
  });
})();
