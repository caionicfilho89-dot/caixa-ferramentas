// Tela principal da Caixa (Tauri). Tudo que é dado vem do Python pela ponte:
// window.__TAURI__.core.invoke("ponte", { pedido: { op, ... } }).
"use strict";

const $ = (sel) => document.querySelector(sel);
const TAURI = window.__TAURI__;

let dados = null;          // catálogo, categorias, vitrine, usos, favoritos
let porChave = {};
let hoje = [];             // cartões do "Agora no seu PC"
let secao = "inicio";      // inicio | favoritos | <id da categoria>
let busca = "";
let respostas = [];

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

async function ponte(op, extra = {}) {
  return TAURI.core.invoke("ponte", { pedido: { op, ...extra } });
}

// ── Aviso no canto ────────────────────────────────────────
let timerAviso;
function aviso(t, erro = false) {
  const a = $("#aviso");
  a.textContent = t;
  a.classList.toggle("erro", erro);
  a.hidden = false;
  clearTimeout(timerAviso);
  timerAviso = setTimeout(() => (a.hidden = true), erro ? 6000 : 3000);
}

// ── Ações ─────────────────────────────────────────────────
async function abrir(chave) {
  const f = porChave[chave];
  aviso(`Abrindo ${f ? f.nome : chave}…`);
  try {
    await ponte("abrir", { chave });
    dados.usos[chave] = (dados.usos[chave] || 0) + 1;
  } catch (e) {
    aviso(String(e), true);
  }
}

async function acaoHoje(id) {
  try {
    const r = await ponte("acao_hoje", { cartao: id });
    aviso(`Abrindo ${r.nome}…`);
  } catch (e) {
    aviso(String(e), true);
  }
}

async function favoritar(chave) {
  try {
    dados.favoritos = await ponte("favorito", { chave });
    const eh = dados.favoritos.includes(chave);
    aviso(eh ? "⭐ Nos favoritos" : "Saiu dos favoritos");
    redesenhar(false);
  } catch (e) {
    aviso(String(e), true);
  }
}

// ── Lateral ───────────────────────────────────────────────
function itemNav(emoji, nome, alvo, num, cor) {
  const ativo = secao === alvo && !busca ? " ativo" : "";
  const ponto = cor ? ` style="--cor:${esc(cor)}"` : "";
  return `<button class="nav-item${ativo}" data-alvo="${esc(alvo)}"${ponto}>
    <span class="emoji">${emoji}</span><span class="nome">${esc(nome)}</span>
    ${num != null ? `<span class="num">${num}</span>` : ""}</button>`;
}

function desenharLateral() {
  const fav = dados.favoritos.length;
  $("#nav").innerHTML =
    itemNav("🏠", "Início", "inicio") +
    itemNav("⭐", "Favoritos", "favoritos", fav || null) +
    `<div class="nav-titulo">CATEGORIAS</div>` +
    dados.categorias.map((c) => itemNav(c.emoji, c.nome, c.id, c.total, c.cor)).join("");
}

// ── Peças ─────────────────────────────────────────────────
function bloco(f) {
  const fav = dados.favoritos.includes(f.chave);
  return `
  <div class="bloco" data-chave="${esc(f.chave)}" title="${esc(f.desc)}">
    <div class="ic">${f.emoji}</div>
    <div class="txt"><div class="n">${esc(f.nome)}</div><div class="ds">${esc(f.desc)}</div></div>
    <button class="estrela${fav ? " on" : ""}" data-fav="${esc(f.chave)}" title="${fav ? "Tirar dos favoritos" : "Favoritar"}">${fav ? "★" : "☆"}</button>
  </div>`;
}

const grade = (lista, vazio = "Nada por aqui.") =>
  lista.length ? `<div class="grade">${lista.map(bloco).join("")}</div>` : `<div class="vazio">${vazio}</div>`;

function blocoHoje(c) {
  return `<div class="bloco-hoje${c.rotulo ? "" : " sem-acao"}" ${c.rotulo ? `data-hoje="${esc(c.id)}"` : ""}>
    <div class="emoji">${esc(c.emoji)}</div>
    <div class="info">
      <div class="t">${esc(c.titulo)}</div>
      <div class="v">${esc(c.valor)}</div>
      <div class="d">${esc(c.detalhe)}</div>
    </div>
    ${c.rotulo ? `<span class="acao">${esc(c.rotulo)}<i class="seta"></i></span>` : ""}
  </div>`;
}

function cartaoResposta(r) {
  const f = porChave[r.chave_ferramenta];
  return `<div class="resposta">
    <div class="r-topo">${esc(r.titulo)}</div>
    <div class="r-valor">${esc(r.resposta)}</div>
    ${r.detalhe ? `<div class="r-det">${esc(r.detalhe)}</div>` : ""}
    <div class="r-acoes">
      <button class="r-btn" data-copiar="${esc(r.resposta)}">Copiar</button>
      ${f ? `<button class="r-btn principal" data-chave="${esc(f.chave)}">Abrir ${esc(f.nome)}</button>` : ""}
    </div>
  </div>`;
}

// ── Páginas ───────────────────────────────────────────────
function maisUsadas(n) {
  return Object.entries(dados.usos)
    .sort((a, b) => b[1] - a[1])
    .map(([c]) => porChave[c])
    .filter(Boolean)
    .slice(0, n);
}

function paginaInicio() {
  const h = new Date().getHours();
  const saud = h < 5 ? "Boa madrugada" : h < 12 ? "Bom dia" : h < 18 ? "Boa tarde" : "Boa noite";
  const data = new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "2-digit", month: "2-digit" });
  const vitrine = dados.vitrine
    .map(
      (v) => `<div class="cartao-vitrine" data-chave="${esc(v.chave)}">
        <div class="cab"><span class="em">${v.emoji}</span><span>${esc(v.nome)}</span></div>
        <div><div class="rot">substitui</div><div class="alvo">${esc(v.substitui)}</div></div>
      </div>`
    )
    .join("");
  const favs = dados.favoritos.map((c) => porChave[c]).filter(Boolean);
  const tend = dados.ferramentas.filter((f) => f.categoria === dados.tendencia).reverse().slice(0, 8);
  return `
    <div class="ola"><h1>${saud}, Caio</h1><span class="data">${esc(data)}</span></div>
    <div class="mascotes">
      <div class="mascote folha"><img src="arte/folha.svg" alt=""><span>Maconha</span></div>
      <div class="mascote po"><img src="arte/po.svg" alt=""><span>Pó</span></div>
      <div class="mascote cristal"><img src="arte/cristal.svg" alt=""><span>Azulzinho</span></div>
    </div>
    <div class="secao">Agora no seu PC</div>
    <div class="hoje" id="hoje">${hoje.length ? hoje.map(blocoHoje).join("") : `<div class="carregando">Olhando o PC…</div>`}</div>
    ${favs.length ? `<div class="secao">⭐ Favoritos</div>${grade(favs)}` : ""}
    <div class="secao">Substitui os programas famosos</div>
    <div class="vitrine">${vitrine}</div>
    <div class="secao">Mais usadas</div>
    ${grade(maisUsadas(12), "Abra algumas ferramentas e elas aparecem aqui.")}
    <div class="secao">🔥 Novas das tendências</div>
    ${grade(tend)}`;
}

function paginaBusca() {
  const q = busca.toLowerCase();
  const achadas = dados.ferramentas.filter(
    (f) => f.nome.toLowerCase().includes(q) || f.desc.toLowerCase().includes(q) || f.chave.includes(q)
  );
  const cartas = respostas.length ? `<div class="respostas">${respostas.map(cartaoResposta).join("")}</div>` : "";
  if (cartas && !achadas.length) return cartas;
  return `${cartas}
    <div class="secao">${achadas.length} ferramenta(s) para “${esc(busca)}”</div>
    ${grade(achadas, "Nenhuma ferramenta com esse nome. Tente outra palavra.")}`;
}

function paginaCategoria() {
  if (secao === "favoritos") {
    const favs = dados.favoritos.map((c) => porChave[c]).filter(Boolean);
    return `<h1>⭐ Favoritos</h1><p class="sub">Clique na estrela de qualquer ferramenta para trazer ela pra cá</p>${grade(favs, "Nenhum favorito ainda.")}`;
  }
  const cat = dados.categorias.find((c) => c.id === secao);
  const lista = dados.ferramentas.filter((f) => f.categoria === secao).sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  return `<h1>${esc(cat ? cat.emoji + " " + cat.nome : secao)}</h1><p class="sub">${lista.length} ferramentas</p>${grade(lista)}`;
}

function desenharConteudo(animar = true) {
  const html = busca ? paginaBusca() : secao === "inicio" ? paginaInicio() : paginaCategoria();
  const c = $("#conteudo");
  const topo = c.scrollTop;
  c.innerHTML = `<div class="${animar ? "entra" : ""}">${html}</div>`;
  c.scrollTop = animar ? 0 : topo;
}

function redesenhar(animar = true) {
  desenharLateral();
  desenharConteudo(animar);
}

// ── Hoje (atualiza a cada 60 s) ───────────────────────────
async function atualizarHoje() {
  try {
    hoje = await ponte("hoje");
  } catch (e) {
    hoje = [];
  }
  const alvo = $("#hoje");
  if (alvo) alvo.innerHTML = hoje.length ? hoje.map(blocoHoje).join("") : `<div class="carregando">Sem novidades no PC agora.</div>`;
}

// ── Barra: busca + respostas ──────────────────────────────
let timerResp;
let pedidoResp = 0;
function aoDigitar(v) {
  busca = v.trim();
  respostas = [];
  redesenhar();
  clearTimeout(timerResp);
  if (!busca) return;
  const meu = ++pedidoResp;
  timerResp = setTimeout(async () => {
    try {
      const r = await ponte("responder", { texto: busca });
      if (meu !== pedidoResp) return;
      respostas = (r || []).filter((x) => x.resposta);
      if (respostas.length) desenharConteudo(false);
    } catch (_) {
      /* a barra continua buscando por nome */
    }
  }, 220);
}

// ── Eventos ───────────────────────────────────────────────
document.addEventListener("click", (e) => {
  const fav = e.target.closest("[data-fav]");
  if (fav) {
    e.stopPropagation();
    favoritar(fav.dataset.fav);
    return;
  }
  const copiar = e.target.closest("[data-copiar]");
  if (copiar) {
    navigator.clipboard.writeText(copiar.dataset.copiar).then(() => aviso("Copiado ✔"));
    return;
  }
  const nav = e.target.closest(".nav-item");
  if (nav) {
    secao = nav.dataset.alvo;
    busca = "";
    respostas = [];
    $("#busca").value = "";
    redesenhar();
    return;
  }
  const h = e.target.closest("[data-hoje]");
  if (h) {
    acaoHoje(h.dataset.hoje);
    return;
  }
  const alvo = e.target.closest("[data-chave]");
  if (alvo) abrir(alvo.dataset.chave);
});

document.addEventListener("contextmenu", (e) => {
  const b = e.target.closest(".bloco");
  if (b) {
    e.preventDefault();
    favoritar(b.dataset.chave);
  }
});

$("#busca").addEventListener("input", (e) => aoDigitar(e.target.value));
$("#busca").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    const primeiro = respostas[0]?.chave_ferramenta || document.querySelector(".grade .bloco")?.dataset.chave;
    if (primeiro) abrir(primeiro);
  }
});

$("#classica").addEventListener("click", async () => {
  aviso("Abrindo a Caixa clássica…");
  try {
    await ponte("classica");
  } catch (e) {
    aviso(String(e), true);
  }
});

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key.toLowerCase() === "k") {
    e.preventDefault();
    $("#busca").focus();
    $("#busca").select();
  }
  if (e.key === "Escape" && busca) {
    $("#busca").value = "";
    aoDigitar("");
  }
});

TAURI.event.listen("buscar", (ev) => {
  $("#busca").value = ev.payload;
  aoDigitar(ev.payload);
});

TAURI.event.listen("focar-busca", () => {
  $("#busca").focus();
  $("#busca").select();
});

// ── Muro pichado: tags, throw-ups, respingos e escorridos (sorteio com semente fixa) ──
function pintarMuro() {
  const muro = $("#muro");
  if (!muro) return;
  let semente = 1907; // sempre o mesmo muro
  const rnd = () => ((semente = (semente * 16807) % 2147483647) / 2147483647);
  const pega = (l) => l[Math.floor(rnd() * l.length)];
  const viagem = document.body.classList.contains("viagem");
  const cores = viagem
    ? ["#39ff14", "#ff1fd1", "#3ad0ff", "#fff200", "#ff8a00", "#9d4dff", "#ffffff"]
    : ["#ff2d95", "#c6ff00", "#00e5ff", "#ffe600", "#ff6a00", "#ffffff"];
  const palavras = viagem ? [
    "MACONHA", "420", "BECK", "BASEADO", "THC", "LARICA", "BRISA", "PÓ", "FARINHA", "BRANQUINHA",
    "CARREIRA", "AZULZINHO", "CRISTAL", "METH", "LSD", "DOCE", "BALA", "MD", "DMT", "KETA",
    "LANÇA", "COGUMELO", "CHAPADO", "LOMBRA", "VIAJOU", "TÔ DE BOA", "SÓ NA PAZ", "🍄", "💊", "🌿", "💉", "❄️", "💎",
  ] : [
    "CAIXA", "PIXO", "OFFLINE", "769", "ZL", "SP", "CAIO", "FAZ VC MESMO", "SEM NUVEM",
    "TMJ", "VILA", "QUEBRADA", "100% LOCAL", "CRIA", "ATÉ O FIM", "♛", "★", "↯", "PAZ",
    "CORRE", "NOIS", "RESPEITA", "011", "TUDO NOSSO", "LIVRE",
  ];
  let html = "";
  for (let i = 0; i < 34; i++) {
    const estilo = pega(["pingo", "pingo", "marcador", "marcador", "contorno"]);
    const c = pega(cores);
    const tam = estilo === "marcador" ? 18 + rnd() * 46 : 34 + rnd() * 110;
    const op = (estilo === "contorno" ? 0.10 : 0.055) + rnd() * 0.06;
    const halo = rnd() < 0.3 ? " halo" : "";
    html += `<span class="tag ${estilo}${halo}" style="left:${(rnd() * 108 - 6).toFixed(1)}%;top:${(rnd() * 108 - 6).toFixed(1)}%;` +
      `font-size:${tam.toFixed(0)}px;color:${c};--c:${c};opacity:${op.toFixed(3)};` +
      `transform:rotate(${(rnd() * 34 - 17).toFixed(1)}deg) skewX(${(rnd() * 16 - 8).toFixed(1)}deg)">${pega(palavras)}</span>`;
  }
  for (let i = 0; i < 70; i++) { // respingos de spray
    const c = pega(cores);
    const d = 2 + rnd() * (rnd() < 0.15 ? 26 : 8);
    html += `<span class="respingo" style="left:${(rnd() * 100).toFixed(1)}%;top:${(rnd() * 100).toFixed(1)}%;` +
      `width:${d.toFixed(1)}px;height:${d.toFixed(1)}px;background:${c};opacity:${(0.05 + rnd() * 0.12).toFixed(3)};` +
      `box-shadow:0 0 ${(d * 1.5).toFixed(0)}px ${c}"></span>`;
  }
  for (let i = 0; i < 22; i++) { // tinta escorrendo
    const c = pega(cores);
    html += `<span class="escorrido" style="left:${(rnd() * 100).toFixed(1)}%;top:${(rnd() * 85).toFixed(1)}%;` +
      `height:${(30 + rnd() * 140).toFixed(0)}px;--c:${c};opacity:${(0.07 + rnd() * 0.1).toFixed(3)}"></span>`;
  }
  if (viagem) { // mascotes apagados espalhados pelo muro
    ["folha", "po", "cristal", "folha", "cristal", "po", "folha"].forEach((b) => {
      html += `<img class="bicho" src="arte/${b}.svg" alt="" style="left:${(rnd() * 96 - 4).toFixed(1)}%;` +
        `top:${(rnd() * 96 - 4).toFixed(1)}%;width:${(120 + rnd() * 160).toFixed(0)}px;` +
        `opacity:${(0.07 + rnd() * 0.06).toFixed(3)};transform:rotate(${(rnd() * 50 - 25).toFixed(0)}deg)">`;
    });
  }
  muro.innerHTML = html;
}

// ── Tema: Viagem (padrão) ou Pichação ─────────────────────
function aplicarTema(tema) {
  document.body.classList.toggle("viagem", tema === "viagem");
  $("#tema").textContent = tema === "viagem" ? "🍄 Tema: Viagem" : "🎨 Tema: Pichação";
  try { localStorage.setItem("caixa_tema", tema); } catch (_) { /* sem memória, segue o padrão */ }
  pintarMuro();
  if (dados) redesenhar(false);
}
let temaAtual = "viagem";
try { temaAtual = localStorage.getItem("caixa_tema") || "viagem"; } catch (_) { /* padrão */ }
$("#tema").addEventListener("click", () => {
  temaAtual = temaAtual === "viagem" ? "pichacao" : "viagem";
  aplicarTema(temaAtual);
});
aplicarTema(temaAtual);

// ── Início ────────────────────────────────────────────────
(async function iniciar() {
  try {
    dados = await ponte("dados");
  } catch (e) {
    $("#conteudo").innerHTML = `<div class="vazio">Não consegui falar com a Caixa: ${esc(e)}<br><br>
      <button class="r-btn principal" id="recarregar">Tentar de novo</button></div>`;
    $("#recarregar").addEventListener("click", () => location.reload());
    return;
  }
  porChave = Object.fromEntries(dados.ferramentas.map((f) => [f.chave, f]));
  $("#total").textContent = `${dados.total} ferramentas · v${dados.versao}`;
  redesenhar();
  $("#busca").focus();
  atualizarHoje();
  setInterval(atualizarHoje, 60000);
})();
