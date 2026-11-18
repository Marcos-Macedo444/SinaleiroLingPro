// Comportamentos da interface. Tudo é aprimoramento progressivo:
// sem JavaScript o sistema continua funcionando por completo.
(() => {
  const reduzido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const COR = { aberto: "verde", andamento: "amarelo", finalizado: "vermelho" };
  const ROTULO = { aberto: "Em aberto", andamento: "Em andamento", finalizado: "Finalizado" };
  const espera = (ms) => new Promise((r) => setTimeout(r, reduzido ? 0 : ms));

  /* ---------- Avisos: somem sozinhos após a contagem (pausa no hover) ---- */
  const fecharAviso = (aviso) => {
    if (!aviso || aviso.classList.contains("saindo")) return;
    if (reduzido) return aviso.remove();
    aviso.classList.add("saindo");
    aviso.addEventListener("animationend", () => aviso.remove(), { once: true });
  };
  document.querySelectorAll(".aviso").forEach((aviso) => {
    aviso.querySelector("[data-fechar-aviso]")?.addEventListener("click", () => fecharAviso(aviso));
    aviso.querySelector(".aviso-tempo")?.addEventListener("animationend", () => fecharAviso(aviso));
  });

  /* ---------- Foco inicial só em telas grandes (no celular abriria o teclado) */
  const focoInicial = document.querySelector("[data-foco-inicial]");
  if (focoInicial && window.matchMedia("(min-width: 821px)").matches) focoInicial.focus({ preventScroll: true });

  /* ---------- Login: sinal verde ao entrar, vermelho no erro ------------- */
  const telaLogin = document.querySelector("[data-login]");
  if (telaLogin) {
    if (telaLogin.classList.contains("negado")) {
      setTimeout(() => telaLogin.classList.remove("negado"), reduzido ? 0 : 2600);
    }
    const formLogin = telaLogin.querySelector("form");
    formLogin.addEventListener("submit", (ev) => {
      if (formLogin.dataset.liberado) return;
      ev.preventDefault();
      formLogin.dataset.liberado = "1";
      telaLogin.classList.remove("negado");
      telaLogin.classList.add("liberado");
      setTimeout(() => formLogin.submit(), reduzido ? 0 : 420);
    });
  }

  /* ---------- Mostrar / ocultar senha ------------------------------------ */
  document.querySelectorAll("[data-mostrar-senha]").forEach((btn) => {
    const input = document.getElementById(btn.getAttribute("aria-controls"));
    btn.addEventListener("click", () => {
      const mostrar = input.type === "password";
      input.type = mostrar ? "text" : "password";
      btn.textContent = mostrar ? "Ocultar" : "Mostrar";
      btn.setAttribute("aria-pressed", String(mostrar));
      input.focus();
    });
  });

  /* ---------- Botão em estado de carregamento ---------------------------- */
  document.querySelectorAll("form[data-carregando]").forEach((form) => {
    form.addEventListener("submit", (ev) => {
      const botao = ev.submitter || form.querySelector('button[type="submit"], button:not([type])');
      if (!botao) return;
      botao.classList.add("carregando");
      botao.setAttribute("aria-busy", "true");
    });
  });
  // Ao voltar pelo histórico (bfcache), devolve os botões ao normal.
  window.addEventListener("pageshow", () => {
    document.querySelectorAll(".botao.carregando").forEach((b) => {
      b.classList.remove("carregando");
      b.removeAttribute("aria-busy");
    });
  });

  /* ---------- Contadores das abas sobem do zero -------------------------- */
  if (!reduzido) {
    document.querySelectorAll("[data-contar]").forEach((el) => {
      const alvo = Number(el.dataset.contar);
      if (!alvo) return;
      const inicio = performance.now();
      const duracao = 650 + Math.min(alvo, 40) * 8;
      const passo = (agora) => {
        const t = Math.min((agora - inicio) / duracao, 1);
        el.textContent = Math.round(alvo * (1 - Math.pow(1 - t, 4)));
        if (t < 1) requestAnimationFrame(passo);
      };
      el.textContent = "0";
      requestAnimationFrame(passo);
    });
  }

  /* ---------- Erro do campo some assim que ele é corrigido --------------- */
  document.querySelectorAll('[aria-invalid="true"]').forEach((campo) => {
    const limpar = () => {
      if (!campo.value.trim()) return;
      campo.removeAttribute("aria-invalid");
      const erro = document.getElementById(campo.getAttribute("aria-describedby"));
      campo.removeAttribute("aria-describedby");
      if (!erro) return;
      if (reduzido) return erro.remove();
      erro.animate([{ opacity: 1 }, { opacity: 0, transform: "translateY(-4px)" }], { duration: 200, easing: "ease-in" })
        .finished.then(() => erro.remove());
    };
    campo.addEventListener("input", limpar);
    campo.addEventListener("change", limpar);
  });

  /* ---------- Contador de caracteres da descrição ------------------------ */
  document.querySelectorAll("[data-contador]").forEach((saida) => {
    const campo = document.getElementById(saida.dataset.contador);
    campo?.addEventListener("input", () => { saida.textContent = campo.value.length; });
  });

  /* ---------- Prévia da plaqueta de patrimônio --------------------------- */
  const previa = document.querySelector("[data-plaqueta-previa]");
  const inputEtiqueta = document.getElementById("etiqueta");
  if (previa && inputEtiqueta) {
    const desenhar = () => {
      const valor = inputEtiqueta.value.trim().toUpperCase();
      let plaqueta = previa.querySelector(".plaqueta");
      if (!valor) return plaqueta?.remove();
      if (!plaqueta) {
        plaqueta = document.createElement("span");
        plaqueta.className = "plaqueta";
        previa.append(plaqueta);
      }
      plaqueta.textContent = valor;
    };
    inputEtiqueta.addEventListener("input", desenhar);
    desenhar();
  }

  /* ---------- Admin: prévia do novo status na própria linha -------------- */
  const aplicarStatus = (linha, valor) => {
    const cor = COR[valor];
    const semaforo = linha.querySelector(".semaforo");
    const texto = linha.querySelector(".status-texto");
    semaforo.classList.remove("acende-verde", "acende-amarelo", "acende-vermelho");
    semaforo.classList.add(`acende-${cor}`);
    semaforo.setAttribute("aria-label", `Status: ${ROTULO[valor]}`);
    linha.classList.remove("linha-verde", "linha-amarelo", "linha-vermelho");
    linha.classList.add(`linha-${cor}`);
    if (texto.textContent !== ROTULO[valor]) {
      texto.textContent = ROTULO[valor];
      texto.classList.remove("trocando");
      void texto.offsetWidth; // reinicia a animação
      texto.classList.add("trocando");
    }
  };

  document.querySelectorAll("[data-status-select]").forEach((sel) => {
    const linha = sel.closest(".linha");
    const original = linha.querySelector(".status-tag").dataset.status;
    const inicial = sel.value;
    const botao = sel.form.querySelector("button");

    const atualizar = () => {
      const mudou = Boolean(sel.value) && sel.value !== inicial;
      botao.disabled = !mudou;
      botao.classList.toggle("primario", mudou);
      botao.classList.toggle("secundario", !mudou);
      linha.classList.toggle("previa", mudou);
      aplicarStatus(linha, mudou ? sel.value : original);
    };
    sel.addEventListener("change", atualizar);
    botao.disabled = true;
  });

  /* ---------- Cancelamento: confirmação em <dialog> e saída da linha ----- */
  const dialogo = document.getElementById("dialogo-cancelar");
  if (dialogo && typeof dialogo.showModal === "function") {
    let pendente = null;
    document.querySelectorAll("[data-confirmar-cancelamento]").forEach((form) => {
      form.addEventListener("submit", (ev) => {
        if (form.dataset.confirmado) return;
        ev.preventDefault();
        pendente = form;
        dialogo.querySelector("[data-dlg-numero]").textContent = "nº " + form.dataset.numero;
        dialogo.querySelector("[data-dlg-item]").textContent = form.dataset.item;
        dialogo.returnValue = "";
        dialogo.showModal();
        dialogo.querySelector('button[value="nao"]').focus();
      });
    });
    dialogo.addEventListener("close", async () => {
      const form = pendente;
      pendente = null;
      if (dialogo.returnValue !== "sim" || !form) return;
      form.dataset.confirmado = "1";
      form.closest(".linha")?.classList.add("saindo");
      await espera(430);
      form.requestSubmit();
    });
  }
})();
