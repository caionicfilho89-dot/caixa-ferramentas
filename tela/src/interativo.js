// Interações do tema Viagem: letras-ímã nos títulos, comprimidos que inclinam em 3D,
// estouro de comprimidos no clique, fumacinha atrás do cursor e fundo com profundidade.
// Tudo desliga no tema Pichação e com "reduzir animações" do Windows.
"use strict";

(function () {
  const calmo = window.matchMedia("(prefers-reduced-motion: reduce)");
  const ligado = () => document.body.classList.contains("viagem") && !calmo.matches;

  // ── Letras dos títulos viram peças soltas ────────────────
  const SELETOR_TITULOS = ".marca-nome, .nav-titulo, #conteudo h1, #conteudo .secao";
  let letras = [];

  function quebrarEmLetras(el) {
    if (el.querySelector("span.letra:not(.elem)")) return; // já está em letras
    const novos = [];
    el.childNodes.forEach((no) => {
      if (no.nodeType === Node.TEXT_NODE) {
        for (const ch of no.textContent) {
          if (/\s/.test(ch)) { novos.push(document.createTextNode(ch)); continue; }
          const s = document.createElement("span");
          s.className = "letra";
          s.textContent = ch;
          novos.push(s);
        }
      } else {
        if (no.classList && no.classList.contains("elem")) no.classList.add("letra");
        novos.push(no);
      }
    });
    el.replaceChildren(...novos);
  }

  function prepararTitulos() {
    if (!ligado()) { letras = []; return; }
    document.querySelectorAll(SELETOR_TITULOS).forEach(quebrarEmLetras);
    letras = Array.from(document.querySelectorAll(".letra"));
  }

  // a tela redesenha conteúdo e menu: refaz as letras depois de cada redesenho
  // (só olha #conteudo, #nav e o nome da Caixa — fumaça e estouros no body não contam)
  let pendente = false;
  const refazer = () => {
    if (pendente) return;
    pendente = true;
    requestAnimationFrame(() => { pendente = false; prepararTitulos(); });
  };
  const obs = new MutationObserver(refazer);
  ["conteudo", "nav"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) obs.observe(el, { childList: true });
  });
  const nome = document.querySelector(".marca-nome");
  if (nome) obs.observe(nome, { childList: true });
  document.getElementById("tema")?.addEventListener("click", () => setTimeout(refazer, 0));

  // ── Mouse: ímã nas letras + fundo com profundidade ───────
  let mx = -9999, my = -9999, quadro = 0;
  function animar() {
    quadro = 0;
    const muro = document.getElementById("muro");
    if (muro) {
      const dx = (mx / innerWidth - 0.5) * -18, dy = (my / innerHeight - 0.5) * -12;
      muro.style.transform = ligado() && mx > -9000 ? `translate(${dx.toFixed(1)}px, ${dy.toFixed(1)}px)` : "";
    }
    for (const l of letras) {
      const r = l.getBoundingClientRect();
      if (r.bottom < 0 || r.top > innerHeight) continue;
      const d = Math.hypot(r.left + r.width / 2 - mx, r.top + r.height / 2 - my);
      const f = Math.max(0, 1 - d / 110);
      if (f > 0) {
        l.style.transform = `translateY(${(-5 * f).toFixed(1)}px) scale(${(1 + 0.14 * f).toFixed(3)})`;
        l.classList.add("perto");
      } else if (l.style.transform) {
        l.style.transform = "";
        l.classList.remove("perto");
      }
    }
  }
  addEventListener("mousemove", (e) => {
    mx = e.clientX; my = e.clientY;
    if (!quadro && ligado()) quadro = requestAnimationFrame(animar);
    fumaca(e);
    inclinar(e);
  }, { passive: true });
  document.addEventListener("mouseleave", () => { mx = my = -9999; if (ligado()) animar(); });

  // ── Comprimidos inclinam em 3D seguindo o mouse ──────────
  let ultimoBloco = null;
  function inclinar(e) {
    const b = ligado() ? e.target.closest(".bloco") : null;
    if (ultimoBloco && ultimoBloco !== b) {
      ultimoBloco.style.removeProperty("--rx");
      ultimoBloco.style.removeProperty("--ry");
      ultimoBloco.style.removeProperty("--gx");
      ultimoBloco.style.removeProperty("--gtx");
      ultimoBloco.style.removeProperty("--inclina");
    }
    ultimoBloco = b;
    if (!b) return;
    const r = b.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
    b.style.setProperty("--ry", ((x - 0.5) * 18).toFixed(1) + "deg");
    b.style.setProperty("--rx", ((0.5 - y) * 22).toFixed(1) + "deg");
    b.style.setProperty("--gx", ((x - 0.5) * 40).toFixed(1) + "%");
    // os grânulos têm peso: escorregam pro lado que desceu
    b.style.setProperty("--gtx", ((x - 0.5) * -8).toFixed(1) + "px");
    b.style.setProperty("--inclina", ((x - 0.5) * -10).toFixed(1) + "deg");
  }

  // ── Fumacinha atrás do cursor ────────────────────────────
  let ultimaFumaca = 0, vivas = 0;
  function fumaca(e) {
    if (!ligado()) return;
    const agora = performance.now();
    if (agora - ultimaFumaca < 45 || vivas > 22) return;
    ultimaFumaca = agora;
    const f = document.createElement("i");
    f.className = "fumaca";
    const t = 10 + Math.random() * 14;
    f.style.cssText = `left:${e.clientX - 2}px;top:${e.clientY - 2}px;width:${t}px;height:${t}px;` +
      `--dx:${(Math.random() * 30 - 15).toFixed(0)}px`;
    document.body.appendChild(f);
    vivas++;
    f.addEventListener("animationend", () => { f.remove(); vivas--; });
  }

  // ── Clique: estouro de comprimidos e brilhos ─────────────
  const PECAS = ["💊", "✨", "💊", "✨"];
  const CORES_GRAO = ["#fffaf0"];
  function derramar(b) {
    b.classList.add("abrindo");
    setTimeout(() => b.classList.remove("abrindo"), 650);
    const r = b.getBoundingClientRect();
    const bocaX = r.left + r.width * 0.36, bocaY = r.top + r.height * 0.5;
    for (let i = 0; i < 10; i++) {
      const g = document.createElement("i");
      g.className = "grao-caindo";
      const d = 8 + Math.random() * 10;
      const cor = CORES_GRAO[i % CORES_GRAO.length];
      g.style.cssText = `left:${(bocaX + Math.random() * 10 - 5).toFixed(0)}px;top:${(bocaY + Math.random() * 16 - 8).toFixed(0)}px;` +
        `width:${d.toFixed(1)}px;height:${d.toFixed(1)}px;` +
        `background:radial-gradient(circle, rgba(255,250,240,.85), rgba(255,250,240,0) 70%);` +
        `--x:${(Math.random() * 50 - 35).toFixed(0)}px;animation-delay:${(Math.random() * 0.15).toFixed(2)}s`;
      document.body.appendChild(g);
      g.addEventListener("animationend", () => g.remove());
    }
  }

  document.addEventListener("pointerdown", (e) => {
    if (!ligado() || e.button !== 0) return;
    const capsula = e.target.closest(".bloco");
    if (capsula) { derramar(capsula); return; }
    if (!e.target.closest(".bloco, .cartao-vitrine, .bloco-hoje, .r-btn, .nav-item, .letra")) return;
    for (let i = 0; i < 5; i++) {
      const p = document.createElement("i");
      p.className = "estouro";
      p.textContent = PECAS[i % PECAS.length];
      const ang = Math.random() * Math.PI * 2, dist = 30 + Math.random() * 40;
      p.style.cssText = `left:${e.clientX}px;top:${e.clientY}px;` +
        `--x:${(Math.cos(ang) * dist).toFixed(0)}px;--y:${(Math.sin(ang) * dist - 30).toFixed(0)}px;` +
        `--r:${(Math.random() * 540 - 270).toFixed(0)}deg;font-size:${(14 + Math.random() * 12).toFixed(0)}px`;
      document.body.appendChild(p);
      p.addEventListener("animationend", () => p.remove());
    }
  });

  // ── Letras: clique faz o título inteiro dar um pulo em onda ─
  document.addEventListener("click", (e) => {
    const t = ligado() && e.target.closest(SELETOR_TITULOS);
    if (!t) return;
    t.querySelectorAll(".letra").forEach((l, i) => {
      l.style.animation = "none";
      void l.offsetWidth;
      l.style.animation = `onda .55s ${i * 0.035}s cubic-bezier(.3, 1.8, .5, 1)`;
    });
  });

  prepararTitulos();
})();
