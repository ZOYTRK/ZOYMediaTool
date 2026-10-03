/* =====================================================================
   ZOY Media Tool — Arayüz mantığı
   Python API: window.pywebview.api.*   |   Python -> JS: onJobUpdate, onFilesDropped
   ===================================================================== */
"use strict";

const S = {
  tools: [], toolMap: {}, cats: [], deps: {}, settings: {}, versions: {},
  jobs: {}, files: {}, urls: {}, opts: {}, ready: false,
};
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const api = () => window.pywebview.api;

const PINNED = ["dl_youtube", "dl_instagram", "video_convert", "audio_convert", "image_convert", "video_compress", "pdf_merge", "archive_create"];
const STATUS_TXT = { running: "Çalışıyor", done: "Tamamlandı", error: "Hata", cancelled: "İptal" };

/* ---------- yardımcılar ---------- */
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const lower = (s) => String(s ?? "").toLocaleLowerCase("tr");
function fmtSize(b) {
  if (!b) return "—";
  const u = ["B", "KB", "MB", "GB", "TB"]; let i = 0;
  while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
  return `${b.toFixed(b < 10 && i ? 1 : 0)} ${u[i]}`;
}
const baseName = (p) => String(p).split(/[\\/]/).pop();
const tile = (t, cls = "") => `<span class="tile ${cls}" style="--c:${t.color || "#3a83f1"}">${t.icon || "🔧"}</span>`;
function greet() {
  const h = new Date().getHours();
  return h < 6 ? "İyi geceler" : h < 12 ? "Günaydın" : h < 18 ? "İyi günler" : "İyi akşamlar";
}
function toolState(t) {
  if (!t.implemented) return { cls: "soon", flag: `<span class="flag">Yakında</span>` };
  if (t.missing.length) return { cls: "", flag: `<span class="flag warn">${esc(t.missing[0])} gerekli</span>` };
  return { cls: "", flag: "" };
}
const win = (icon, title, body, { sub = "", right = "", cls = "", bodyCls = "", id = "" } = {}) => `
  <section class="win ${cls}" ${id ? `id="${id}"` : ""}>
    <div class="win-title"><span class="wt-icon">${icon}</span><span>${title}</span>${sub ? `<span class="wt-sub">— ${sub}</span>` : ""}
      <span class="wt-right">${right}</span></div>
    <div class="win-body ${bodyCls}">${body}</div>
  </section>`;

/* ---------- XP balon bildirimi ---------- */
function balloon(title, text, icon = "ℹ️", onClick) {
  const el = document.createElement("div");
  el.className = "balloon";
  el.innerHTML = `<button class="b-x" aria-label="Kapat">✕</button><b>${icon} ${esc(title)}</b><div>${esc(text)}</div>`;
  const close = () => { el.classList.add("out"); setTimeout(() => el.remove(), 260); };
  el.addEventListener("click", (e) => { if (!e.target.classList.contains("b-x") && onClick) onClick(); close(); });
  $("#balloons").appendChild(el);
  setTimeout(close, 6500);
}

/* =====================================================================
   BAŞLANGIÇ
   ===================================================================== */
async function init() {
  try {
    const data = await api().get_bootstrap();
    S.tools = data.tools; S.cats = data.categories; S.deps = data.deps;
    S.settings = data.settings; S.versions = data.versions;
    S.tools.forEach((t) => (S.toolMap[t.id] = t));
    (data.jobs || []).forEach((j) => (S.jobs[j.id] = j));
    S.ready = true;
    applyTheme(S.settings.theme, false);
    $("#user-name").textContent = S.settings.username;
    $("#sm-user").textContent = S.settings.username;
    $("#user-avatar").textContent = (S.settings.username || "Z")[0].toLocaleUpperCase("tr");
    buildNav(); buildStartMenu(); updateChrome(); tickClock();
    setInterval(tickClock, 10000);
    render();
  } catch (err) {
    console.error("Init hatası:", err);
    balloon("Başlatma Hatası", String(err.message || err), "⛔");
  }
}

function applyTheme(theme, save = true) {
  theme = theme || "win2000";
  document.documentElement.dataset.theme = theme;
  document.documentElement.setAttribute("data-theme", theme);
  if (document.body) {
    document.body.dataset.theme = theme;
    document.body.setAttribute("data-theme", theme);
  }
  const sm = $("#start-menu");
  if (sm) {
    sm.dataset.theme = theme;
    sm.setAttribute("data-theme", theme);
  }
  const labels = { win2000: "Win 2000", "win2000-dark": "Win 2000 Koyu", "xp-luna": "XP Luna", "xp-dark": "XP Koyu" };
  const lbl = $("#theme-label");
  if (lbl) lbl.textContent = labels[theme] || "Win 2000";
  S.settings.theme = theme;
  if (save && window.pywebview && window.pywebview.api) api().save_settings({ theme });
  $$(".theme-opt").forEach((b) => b.classList.toggle("sel", b.dataset.theme === theme));
}

function tickClock() {
  const d = new Date();
  $("#clock").textContent = d.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
}

/* ---------- kenar menüsü ---------- */
function buildNav() {
  const groups = {};
  S.cats.forEach((c) => (groups[c.group] ||= []).push(c));
  const count = (cid) => S.tools.filter((t) => t.category === cid).length;
  let html = `<div class="nav-group"><div class="nav-head">Ana Menü</div>
    <button class="nav-link" data-route="#/dashboard"><span class="ni">🏠</span>Dashboard</button>
    <button class="nav-link" data-route="#/all"><span class="ni">🧰</span>Tüm Araçlar<span class="count">${S.tools.length}</span></button>
    <button class="nav-link" data-route="#/jobs"><span class="ni">📋</span>İşlem Kuyruğu<span class="count" id="nav-jobs-count">0</span></button>
  </div>`;
  for (const [g, cats] of Object.entries(groups)) {
    html += `<div class="nav-group"><div class="nav-head">${esc(g)}</div>`;
    html += cats.map((c) => `<button class="nav-link" data-route="#/cat/${c.id}"><span class="ni">${c.icon}</span>${esc(c.name)}<span class="count">${count(c.id)}</span></button>`).join("");
    html += `</div>`;
  }
  $("#nav").innerHTML = html;
}

function highlightNav() {
  const h = location.hash || "#/dashboard";
  let key = h;
  if (h.startsWith("#/tool/")) {
    const t = S.toolMap[h.slice(7)];
    key = t ? `#/cat/${t.category}` : h;
  }
  $$(".nav-link[data-route]").forEach((b) => b.classList.toggle("active", b.dataset.route === key));
}

/* ---------- başlat menüsü ---------- */
function buildStartMenu() {
  const sm = $("#start-menu");
  if (sm && S.settings.theme) {
    sm.dataset.theme = S.settings.theme;
    sm.setAttribute("data-theme", S.settings.theme);
  }
  $("#sm-left").innerHTML = PINNED.map((id) => S.toolMap[id]).filter(Boolean).map((t) => `
    <button class="sm-item" data-route="#/tool/${t.id}">${tile(t, "sm")}<span><b>${esc(t.name)}</b><small>${esc(t.desc.slice(0, 38))}…</small></span></button>`).join("")
    + `<div class="sm-sep"></div><button class="sm-item" data-route="#/all">🧰 <b>Tüm Araçlar ▸</b></button>`;
  $("#sm-right").innerHTML = `
    <button class="sm-item" data-act="open-folder">📁 Çıktı Klasörüm</button>
    <button class="sm-item" data-route="#/jobs">📋 İşlem Kuyruğu</button>
    <div class="sm-sep"></div>`
    + S.cats.map((c) => `<button class="sm-item" data-route="#/cat/${c.id}">${c.icon} ${esc(c.name)}</button>`).join("")
    + `<div class="sm-sep"></div><button class="sm-item" data-route="#/settings">⚙️ Denetim Masası</button>`;
}
function toggleStart(force) {
  const m = $("#start-menu");
  const open = force ?? m.hidden;
  m.hidden = !open;
  $("#start-btn").classList.toggle("open", open);
}

/* =====================================================================
   YÖNLENDİRME
   ===================================================================== */
function setHeader(title, crumb) {
  $("#page-title").textContent = title;
  $("#page-crumb").textContent = crumb;
  document.title = `${title} — ZOY Media Tool`;
}

function render() {
  if (!S.ready) return;
  const h = location.hash || "#/dashboard";
  const [, page, arg] = h.split("/");
  const c = $("#content");
  if (page === "tool" && S.toolMap[arg]) c.innerHTML = pageTool(S.toolMap[arg]);
  else if (page === "cat") c.innerHTML = pageCategory(arg);
  else if (page === "all") c.innerHTML = pageAll();
  else if (page === "jobs") c.innerHTML = pageJobs();
  else if (page === "settings") c.innerHTML = pageSettings();
  else if (page === "search") c.innerHTML = pageSearch(decodeURIComponent(arg || ""));
  else c.innerHTML = pageDashboard();
  if (page === "tool" && S.toolMap[arg]) bindToolForm(S.toolMap[arg]);
  highlightNav();
  c.scrollTop = 0;
}

/* ---------- DASHBOARD ---------- */
function pageDashboard() {
  setHeader("Dashboard", "Genel Bakış");
  const jobs = Object.values(S.jobs);
  const by = (s) => jobs.filter((j) => j.status === s).length;
  const outputs = jobs.reduce((n, j) => n + (j.outputs?.length || 0), 0);
  const ready = S.tools.filter((t) => t.implemented && !t.missing.length).length;
  const depsOk = Object.values(S.deps).filter((d) => d.ok).length;
  const quick = PINNED.map((id) => S.toolMap[id]).filter(Boolean);

  const stats = [
    ["🧰", "#3a83f1", "Toplam Araç", S.tools.length], ["✅", "#43a047", "Kullanıma Hazır", ready],
    ["⚙️", "#fb8c00", "Aktif İşlem", by("running")], ["🏁", "#00897b", "Tamamlanan", by("done")],
    ["⚠️", "#e53935", "Hatalı", by("error")], ["📄", "#8e24aa", "Oluşan Dosya", outputs],
  ];
  const recent = jobs.sort((a, b) => b.started - a.started).slice(0, 5);
  const depsHtml = Object.entries(S.deps).map(([k, d]) => `
    <div class="dep ${d.ok ? "ok" : ""}"><span class="dot"></span>${esc(d.name)}
      ${d.ok ? `<span style="margin-left:auto;opacity:.8">Hazır</span>` : `<button class="dep-act" data-act="open-url" data-url="${esc(d.url)}">Kur ↗</button>`}
    </div>`).join("");

  return `
    <div class="welcome">
      <span class="tile lg" style="--c:#2563d1">👋</span>
      <div><h2>${greet()}, ${esc(S.settings.username)}!</h2>
        <p>Medya indir, dosya dönüştür, PDF düzenle — hepsi tek yerde, tamamen çevrimdışı.</p></div>
      <div class="actions">
        <button class="xp-btn sm" data-route="#/tool/dl_youtube">▶️ YouTube İndir</button>
        <button class="xp-btn sm" data-route="#/tool/video_convert">🎞️ Video Dönüştür</button>
        <button class="xp-btn sm" data-route="#/cat/pdf-org">📑 PDF Araçları</button>
      </div>
    </div>

    <div class="row cols-side">
      ${win("🛡️", "Sistem Durumu", `
        <div class="status-card">
          <div class="big">${depsOk}/${Object.keys(S.deps).length}<small>bileşen hazır • yt-dlp ${esc(S.versions.yt_dlp)}</small></div>
          <div class="dep-list">${depsHtml}</div>
        </div>`, { right: `<button class="wt-link" data-route="#/settings">Detay</button>`, bodyCls: "flush" })}
      ${win("⚡", "Hızlı İşlemler", `<div class="quick-grid">${quick.map((t) => `
          <button class="quick" data-route="#/tool/${t.id}">${tile(t)}<b>${esc(t.name)}</b><span class="q-sub">${esc(S.cats.find((c) => c.id === t.category)?.name || "")}</span></button>`).join("")}
        </div>`, { sub: "Sık kullanılan araçlar", right: `<button class="wt-link" data-route="#/all">Tüm Araçlar (${S.tools.length})</button>` })}
    </div>

    <div class="stats">${stats.map(([i, c, l, v]) => `
      <div class="stat"><span class="tile" style="--c:${c}">${i}</span><div><div class="lbl">${l}</div><div class="val">${v}</div></div></div>`).join("")}
    </div>

    <div class="row cols-2">
      ${win("🕘", "Son İşlemler", recent.length ? `<div class="job-list" data-joblist="recent">${recent.map(jobHTML).join("")}</div>`
        : emptyHTML("📭", "Henüz işlem yok", "Bir araç seçip ilk işlemini başlat."), { right: `<button class="wt-link" data-route="#/jobs">Tümü</button>` })}
      ${win("🗂️", "Kategoriler", `<div class="cat-grid">${S.cats.map((c) => `
        <button class="cat" data-route="#/cat/${c.id}"><span class="tile sm" style="--c:${catColor(c.id)}">${c.icon}</span>
          <span><b>${esc(c.name)}</b><small>${S.tools.filter((t) => t.category === c.id).length} araç</small></span></button>`).join("")}</div>`)}
    </div>`;
}
const catColor = (id) => ({ dl: "#e53935", video: "#1e88e5", audio: "#8e24aa", image: "#00897b", doc: "#1565c0", archive: "#6d4c41" }[id] || "#c62828");
const emptyHTML = (i, t, s) => `<div class="empty"><div class="e-icon">${i}</div><b>${esc(t)}</b><div>${esc(s)}</div></div>`;

/* ---------- KATEGORİ / TÜM ARAÇLAR / ARAMA ---------- */
function toolCards(list) {
  if (!list.length) return emptyHTML("🔍", "Sonuç bulunamadı", "Farklı bir kelime deneyin.");
  return `<div class="tool-grid">${list.map((t, i) => {
    const st = toolState(t);
    return `<button class="tool-card ${st.cls}" style="animation-delay:${Math.min(i * 18, 300)}ms" data-route="#/tool/${t.id}">
      ${tile(t, "lg")}<div><h3>${esc(t.name)}</h3><p>${esc(t.desc)}</p></div>${st.flag}</button>`;
  }).join("")}</div>`;
}
function pageCategory(cid) {
  const c = S.cats.find((x) => x.id === cid);
  if (!c) return pageDashboard();
  setHeader(c.name, `${c.group} › ${c.name}`);
  return `<div class="section-title">${c.icon} ${esc(c.name)}</div>${toolCards(S.tools.filter((t) => t.category === cid))}`;
}
function pageAll() {
  setHeader("Tüm Araçlar", `${S.tools.length} araç`);
  return S.cats.map((c) => `<div class="section-title" style="margin-top:14px">${c.icon} ${esc(c.name)}</div>
    ${toolCards(S.tools.filter((t) => t.category === c.id))}`).join("");
}
function pageSearch(q) {
  setHeader("Arama", `"${q}" için sonuçlar`);
  const words = lower(q).split(/\s+/).filter(Boolean);
  const list = S.tools.filter((t) => {
    const hay = lower(`${t.name} ${t.desc} ${t.id} ${(t.accept || []).join(" ")}`);
    return words.every((w) => hay.includes(w));
  });
  return `<div class="section-title">🔍 ${list.length} araç bulundu</div>${toolCards(list)}`;
}

/* ---------- ARAÇ SAYFASI ---------- */
function pageTool(t) {
  const cat = S.cats.find((c) => c.id === t.category);
  setHeader(t.name, `${cat?.group || ""} › ${cat?.name || ""} › ${t.name}`);
  const back = `<button class="wt-ctrl" title="Geri" data-route="#/cat/${t.category}">‹</button><button class="wt-ctrl close" title="Kapat" data-route="#/dashboard">✕</button>`;

  if (!t.implemented) {
    return win(t.icon, t.name, `
      <div class="empty"><div class="e-icon">🚧</div><b>Bu araç bir sonraki güncellemede aktif olacak</b>
      <div style="margin:6px 0 14px">${esc(t.desc)}</div>
      <button class="xp-btn" data-route="#/cat/${t.category}">‹ Kategoriye dön</button></div>`, { right: back });
  }

  const warn = t.missing.length ? `<div class="welcome" style="border-color:var(--warn)">
      <span class="tile" style="--c:#fb8c00">⚠️</span><div><h2>${esc(t.missing.join(", "))} gerekli</h2>
      <p>Bu aracı kullanmak için ilgili bileşeni kurun, ardından uygulamayı yeniden başlatın.</p></div>
      <div class="actions"><button class="xp-btn sm" data-route="#/settings">Bileşenler</button></div></div>` : "";

  const input = t.input === "url" ? `
      <div class="field">
        <label class="lbl" for="url-input">Bağlantılar (her satıra bir URL)</label>
        <textarea class="xp-textarea" id="url-input" placeholder="https://www.youtube.com/watch?v=...\nhttps://www.instagram.com/reel/...">${esc(S.urls[t.id] || "")}</textarea>
        <div class="hint">Birden fazla bağlantıyı alt alta yapıştırarak toplu indirme yapabilirsin.</div>
      </div>
      <div style="display:flex;gap:6px;margin-top:8px">
        <button class="xp-btn sm" id="btn-paste">📋 Panodan Yapıştır</button>
        <button class="xp-btn sm" id="btn-clear-urls">🧹 Temizle</button>
      </div>`
    : `
      <div class="dropzone" id="dropzone" role="button" tabindex="0">
        <div class="dz-icon">📂</div>
        <h3>Dosya seçmek için tıkla veya sürükleyip bırak</h3>
        <p>${t.multiple ? "Birden fazla dosya seçebilirsin" : "Tek dosya seç"}${t.min_files > 1 ? ` • en az ${t.min_files} dosya` : ""}</p>
        ${t.accept ? `<div class="ext-list">${t.accept.map((e) => e.toUpperCase()).join(" • ")}</div>` : ""}
      </div>
      <div class="file-list" id="file-list"></div>`;

  return `${warn}
    <div class="row cols-tool">
      ${win(t.icon, t.name, input, { sub: t.input === "url" ? "Bağlantı" : "Dosyalar", right: back, id: "win-input" })}
      ${win("⚙️", "Ayarlar", `
        <div class="form" id="opt-form">${t.options.map((o) => optionHTML(t, o)).join("") || `<div class="muted">Bu araç için ek ayar yok.</div>`}</div>
        <fieldset class="xp-fieldset" style="margin-top:14px"><legend>Çıktı</legend>
          <div class="path-box"><input class="xp-input" id="out-dir" readonly value="${esc(S.settings.output_dir)}">
          <button class="xp-btn sm" data-act="change-dir">Değiştir</button></div>
        </fieldset>
        <div style="display:flex;gap:8px;margin-top:14px;justify-content:flex-end">
          <button class="xp-btn" data-act="open-folder">📁 Klasörü Aç</button>
          <button class="xp-btn primary lg" id="btn-run" ${t.missing.length ? "disabled" : ""}>▶ Başlat</button>
        </div>`, { sub: t.desc })}
    </div>
    ${win("📋", "Bu Araçtaki İşlemler", `<div class="job-list" data-joblist="tool:${t.id}">${toolJobs(t.id)}</div>`)}`;
}
function toolJobs(tid) {
  const list = Object.values(S.jobs).filter((j) => j.tool === tid).sort((a, b) => b.started - a.started);
  return list.length ? list.map(jobHTML).join("") : emptyHTML("⏳", "Henüz işlem yok", "Dosyalarını ekleyip Başlat'a bas.");
}

function optionHTML(t, o) {
  const saved = S.opts[t.id] || (S.opts[t.id] = {});
  const v = saved[o.id] ?? o.default;
  saved[o.id] = v;
  const id = `opt-${o.id}`;
  let ctrl = "";
  if (o.type === "select") {
    ctrl = `<select class="xp-select" id="${id}" data-opt="${o.id}">${o.choices.map(([val, lab]) =>
      `<option value="${esc(val)}" ${String(val) === String(v) ? "selected" : ""}>${esc(lab)}</option>`).join("")}</select>`;
  } else if (o.type === "range") {
    ctrl = `<div class="range-wrap"><input type="range" id="${id}" data-opt="${o.id}" min="${o.min}" max="${o.max}" step="${o.step}" value="${v}">
      <output>${v}${esc(o.suffix || "")}</output></div>`;
  } else if (o.type === "checkbox") {
    return `<div class="field" data-field="${o.id}"><label class="check"><input type="checkbox" id="${id}" data-opt="${o.id}" ${v ? "checked" : ""}>${esc(o.label)}</label></div>`;
  } else if (o.type === "number") {
    ctrl = `<input class="xp-input" type="number" id="${id}" data-opt="${o.id}" value="${esc(v)}" ${o.min != null ? `min="${o.min}"` : ""} ${o.max != null ? `max="${o.max}"` : ""}>`;
  } else {
    ctrl = `<input class="xp-input" type="text" id="${id}" data-opt="${o.id}" value="${esc(v)}" placeholder="${esc(o.placeholder || "")}">`;
  }
  return `<div class="field" data-field="${o.id}"><label class="lbl" for="${id}">${esc(o.label)}</label>${ctrl}</div>`;
}

function applyShowIf(t) {
  const vals = S.opts[t.id] || {};
  t.options.forEach((o) => {
    if (!o.show_if) return;
    const ok = Object.entries(o.show_if).every(([k, allowed]) => allowed.map(String).includes(String(vals[k])));
    const f = $(`[data-field="${o.id}"]`);
    if (f) f.hidden = !ok;
  });
}

function renderFiles(t) {
  const box = $("#file-list");
  if (!box) return;
  const files = S.files[t.id] || [];
  box.innerHTML = files.map((f, i) => `
    <div class="file-row"><span class="ext-chip">${esc(f.ext || "?")}</span><span class="fname" title="${esc(f.path)}">${esc(f.name)}</span>
      <span class="fsize">${fmtSize(f.size)}</span>
      ${files.length > 1 ? `<button class="icon-btn" data-act="file-up" data-i="${i}" title="Yukarı">▲</button><button class="icon-btn" data-act="file-down" data-i="${i}" title="Aşağı">▼</button>` : ""}
      <button class="icon-btn" data-act="file-del" data-i="${i}" title="Kaldır">✕</button></div>`).join("")
    + (files.length ? `<div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px">
        <span class="muted" style="font-size:11px">${files.length} dosya • ${fmtSize(files.reduce((n, f) => n + f.size, 0))}</span>
        <button class="xp-btn sm" data-act="files-clear">🧹 Tümünü kaldır</button></div>` : "");
}

function addFiles(t, list) {
  if (!list?.length) return;
  const cur = S.files[t.id] || (S.files[t.id] = []);
  const known = new Set(cur.map((f) => f.path));
  let skipped = 0;
  for (const f of list) {
    if (known.has(f.path)) continue;
    if (t.accept && f.ext && !t.accept.includes(f.ext)) { skipped++; continue; }
    if (!t.multiple) cur.length = 0;
    cur.push(f); known.add(f.path);
  }
  if (skipped) balloon("Bazı dosyalar atlandı", `${skipped} dosya bu araç tarafından desteklenmiyor.`, "⚠️");
  renderFiles(t);
}

function bindToolForm(t) {
  applyShowIf(t);
  renderFiles(t);
  const form = $("#opt-form");
  form?.addEventListener("input", (e) => {
    const el = e.target.closest("[data-opt]");
    if (!el) return;
    const o = t.options.find((x) => x.id === el.dataset.opt);
    let val = el.type === "checkbox" ? el.checked : el.value;
    if (o.type === "range" || o.type === "number") val = Number(val);
    S.opts[t.id][o.id] = val;
    if (o.type === "range") el.nextElementSibling.textContent = `${val}${o.suffix || ""}`;
    applyShowIf(t);
  });
  const dz = $("#dropzone");
  if (dz) {
    const pick = async () => addFiles(t, await api().pick_files(t.id));
    dz.addEventListener("click", pick);
    dz.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && pick());
  }
  const ta = $("#url-input");
  ta?.addEventListener("input", () => (S.urls[t.id] = ta.value));
  $("#btn-paste")?.addEventListener("click", async () => {
    try { const txt = await navigator.clipboard.readText(); ta.value = (ta.value.trim() ? ta.value.trim() + "\n" : "") + txt.trim(); S.urls[t.id] = ta.value; }
    catch { balloon("Pano okunamadı", "Bağlantıyı Ctrl+V ile yapıştırabilirsin.", "📋"); ta.focus(); }
  });
  $("#btn-clear-urls")?.addEventListener("click", () => { ta.value = ""; S.urls[t.id] = ""; });
  $("#btn-run")?.addEventListener("click", () => runTool(t));
}

async function runTool(t) {
  const inputs = t.input === "url"
    ? (S.urls[t.id] || "").split(/\r?\n/).map((s) => s.trim()).filter(Boolean)
    : (S.files[t.id] || []).map((f) => f.path);
  if (!inputs.length) {
    balloon("Girdi eksik", t.input === "url" ? "Lütfen en az bir bağlantı yapıştır." : "Lütfen önce dosya ekle.", "⚠️");
    return;
  }
  const btn = $("#btn-run");
  btn.disabled = true;
  try {
    const res = await api().run_tool(t.id, inputs, S.opts[t.id] || {});
    if (res.error) { balloon("Başlatılamadı", res.error, "⛔"); return; }
    S.jobs[res.id] = res;
    if (t.input === "url") { S.urls[t.id] = ""; const ta = $("#url-input"); if (ta) ta.value = ""; }
    else { S.files[t.id] = []; renderFiles(t); }
    refreshJobLists(); updateChrome();
  } finally { btn.disabled = false; }
}

/* ---------- İŞ KARTI ---------- */
function jobHTML(j) {
  const t = S.toolMap[j.tool] || { icon: j.icon, color: "#3a83f1" };
  const pct = Math.round((j.progress || 0) * 100);
  const indet = j.status === "running" && pct === 0;
  const actions = j.status === "running"
    ? `<button class="xp-btn sm danger" data-act="cancel" data-id="${j.id}">İptal</button>`
    : `${j.outputs?.length ? `<button class="xp-btn sm" data-act="reveal" data-path="${esc(j.outputs[0])}">📂 Göster</button>` : ""}`;
  const outs = j.status === "done" && j.outputs?.length ? `<div class="outputs">${j.outputs.slice(0, 6).map((p) => `
      <div class="out-file">📄<span title="${esc(p)}">${esc(baseName(p))}</span>
        <button class="icon-btn" data-act="open" data-path="${esc(p)}" title="Aç">↗</button></div>`).join("")}
      ${j.outputs.length > 6 ? `<div class="muted" style="font-size:11px">+${j.outputs.length - 6} dosya daha</div>` : ""}</div>` : "";
  return `<div class="job ${j.status}" data-job="${j.id}">
    ${tile(t)}
    <div style="min-width:0">
      <div class="job-title">${esc(j.tool_name)} — ${esc(j.title)}</div>
      <div class="job-meta">${esc(STATUS_TXT[j.status] || "")} • ${esc(j.message || "")}</div>
      <div class="progress ${j.status} ${indet ? "indeterminate" : ""}"><div class="fill" style="width:${j.status === "done" ? 100 : pct}%"></div></div>
    </div>
    <div class="job-actions">${actions}</div>${outs}
  </div>`;
}

function refreshJobLists() {
  $$("[data-joblist]").forEach((box) => {
    const k = box.dataset.joblist;
    if (k.startsWith("tool:")) box.innerHTML = toolJobs(k.slice(5));
    else if (k === "all") box.innerHTML = allJobsHTML();
  });
}

function updateChrome() {
  const jobs = Object.values(S.jobs);
  const running = jobs.filter((j) => j.status === "running");
  const b = $("#jobs-badge");
  b.textContent = running.length; b.classList.toggle("zero", !running.length);
  $("#tray-active").textContent = running.length;
  const nc = $("#nav-jobs-count"); if (nc) nc.textContent = jobs.length;
  $("#task-items").innerHTML = running.slice(0, 5).map((j) => `
    <div class="task-item" data-route="#/tool/${j.tool}" title="${esc(j.title)}">${esc(j.icon || "⚙️")}<span>${esc(j.tool_name)}</span><b>%${Math.round(j.progress * 100)}</b></div>`).join("");
  const missing = Object.values(S.deps).filter((d) => !d.ok).map((d) => d.name);
  $("#tray-deps").title = missing.length ? `Eksik: ${missing.join(", ")}` : "Tüm bileşenler hazır";
  $("#tray-deps").textContent = missing.length ? "⚠️" : "🛡️";
}

/* Python -> JS: iş ilerlemesi */
window.onJobUpdate = (j) => {
  const prev = S.jobs[j.id];
  S.jobs[j.id] = j;
  $$(`[data-job="${j.id}"]`).forEach((el) => (el.outerHTML = jobHTML(j)));
  if (!$(`[data-job="${j.id}"]`)) refreshJobLists();
  updateChrome();
  if (prev && prev.status === "running" && j.status !== "running") {
    if (j.status === "done") balloon("İşlem tamamlandı", `${j.tool_name}: ${j.outputs.length} dosya hazır. Görmek için tıkla.`, "✅",
      () => j.outputs[0] && api().reveal_path(j.outputs[0]));
    else if (j.status === "error") balloon("İşlem başarısız", j.error || j.message, "⛔");
  }
};

/* Python -> JS: sürükle-bırak */
window.onFilesDropped = (files) => {
  document.body.classList.remove("dragging");
  const [, page, arg] = (location.hash || "").split("/");
  const t = page === "tool" ? S.toolMap[arg] : null;
  if (!t || t.input !== "files" || !t.implemented) {
    balloon("Önce bir araç seç", "Dosyaları bırakmak için bir dönüştürme aracı açık olmalı.", "💡");
    return;
  }
  addFiles(t, files);
};

/* ---------- İŞLEM KUYRUĞU ---------- */
function allJobsHTML() {
  const list = Object.values(S.jobs).sort((a, b) => b.started - a.started);
  return list.length ? list.map(jobHTML).join("") : emptyHTML("📭", "Kuyruk boş", "Başlattığın işlemler burada görünecek.");
}
function pageJobs() {
  setHeader("İşlem Kuyruğu", "Tüm işlemler");
  return win("📋", "İşlem Kuyruğu", `<div class="job-list" data-joblist="all">${allJobsHTML()}</div>`, {
    right: `<button class="wt-link" data-act="clear-jobs">Bitenleri temizle</button><button class="wt-link" data-act="open-folder">Klasörü aç</button>`,
  });
}

/* ---------- AYARLAR ---------- */
function pageSettings() {
  setHeader("Ayarlar", "Denetim Masası");
  const th = S.settings.theme;
  const deps = Object.entries(S.deps).map(([k, d]) => `
    <div class="file-row"><span class="dot" style="width:10px;height:10px;border-radius:50%;background:${d.ok ? "var(--ok)" : "var(--err)"}"></span>
      <span class="fname">${esc(d.name)}</span><span class="fsize" title="${esc(d.path)}">${d.ok ? esc(d.path) : "Kurulu değil"}</span>
      ${d.ok ? "" : `<button class="xp-btn sm blue" data-act="open-url" data-url="${esc(d.url)}">İndir ↗</button>`}</div>`).join("");
  return `
    <div class="row cols-2">
      ${win("🎨", "Görünüm", `
        <div class="theme-pick" style="grid-template-columns: repeat(2, 1fr); gap: 8px;">
          <button class="theme-opt ${th === "win2000" ? "sel" : ""}" data-act="theme" data-theme="win2000">
            <div class="theme-prev" style="background:#3a6ea5;display:flex;align-items:center;justify-content:center"><div style="width:70%;height:60%;background:#d4d0c8;border:2px outset #fff"></div></div>
            <b>Windows 2000</b><div class="muted" style="font-size:11px">Klasik gri 3D pencereler</div></button>
          <button class="theme-opt ${th === "win2000-dark" ? "sel" : ""}" data-act="theme" data-theme="win2000-dark">
            <div class="theme-prev" style="background:#14171d;display:flex;align-items:center;justify-content:center"><div style="width:70%;height:60%;background:#24272e;border:2px outset #4a5260"></div></div>
            <b>Win 2000 Koyu</b><div class="muted" style="font-size:11px">Retro siyah/kömür 3D</div></button>
          <button class="theme-opt ${th === "xp-dark" ? "sel" : ""}" data-act="theme" data-theme="xp-dark">
            <div class="theme-prev dark"><div class="tp-side"></div><div class="tp-main"><div class="tp-win"><div class="tp-bar"></div></div></div></div>
            <b>XP Koyu</b><div class="muted" style="font-size:11px">Koyu dashboard</div></button>
          <button class="theme-opt ${th === "xp-luna" ? "sel" : ""}" data-act="theme" data-theme="xp-luna">
            <div class="theme-prev luna"><div class="tp-side"></div><div class="tp-main"><div class="tp-win"><div class="tp-bar"></div></div></div></div>
            <b>XP Luna</b><div class="muted" style="font-size:11px">Klasik XP mavi/bej</div></button>
        </div>`)}
      ${win("👤", "Genel", `
        <div class="form">
          <div class="field"><label class="lbl" for="set-user">Kullanıcı adı</label>
            <input class="xp-input" id="set-user" value="${esc(S.settings.username)}"></div>
          <div class="field"><label class="lbl">Varsayılan çıktı klasörü</label>
            <div class="path-box"><input class="xp-input" id="out-dir" readonly value="${esc(S.settings.output_dir)}">
            <button class="xp-btn sm" data-act="change-dir">Değiştir</button></div></div>
          <div style="display:flex;justify-content:flex-end"><button class="xp-btn blue" data-act="save-user">💾 Kaydet</button></div>
        </div>`)}
    </div>
    ${win("🧩", "Bileşenler", `<div class="file-list" style="max-height:none;margin:0">${deps}</div>
      <div class="hint muted" style="margin-top:8px;font-size:11px">FFmpeg medya motoru, dahili RapidOCR ve Python ofis dönüştürücüsü aktiftir. Ekstra harici program kurulumu gerekmez.</div>`,
      { right: `<button class="wt-link" data-act="refresh-deps">Yenile</button>` })}
    <div style="height:14px"></div>
    ${win("ℹ️", "Hakkında", `<div class="kv">
        <span class="k">Uygulama</span><span>ZOY Media Tool 2.0</span>
        <span class="k">yt-dlp</span><span>${esc(S.versions.yt_dlp)}</span>
        <span class="k">GitHub</span><span><a href="#" data-act="open-url" data-url="https://github.com/ZOYTRK/ZOYMediaTool">github.com/ZOYTRK/ZOYMediaTool</a></span>
      </div>`)}`;
}

/* =====================================================================
   OLAYLAR
   ===================================================================== */
document.addEventListener("click", async (e) => {
  const sm = $("#start-menu");
  if (!sm.hidden && !e.target.closest("#start-menu") && !e.target.closest("#start-btn")) toggleStart(false);

  const r = e.target.closest("[data-route]");
  if (r) { e.preventDefault(); toggleStart(false); if (location.hash === r.dataset.route) render(); else location.hash = r.dataset.route; return; }

  const a = e.target.closest("[data-act]");
  if (!a) return;
  e.preventDefault();
  const act = a.dataset.act;
  const [, page, arg] = (location.hash || "").split("/");
  const t = page === "tool" ? S.toolMap[arg] : null;

  if (act === "open-folder") { toggleStart(false); api().open_output_dir(); }
  else if (act === "open-url") api().open_url(a.dataset.url);
  else if (act === "cancel") api().cancel_job(a.dataset.id);
  else if (act === "reveal") api().reveal_path(a.dataset.path);
  else if (act === "open") api().open_path(a.dataset.path);
  else if (act === "theme") applyTheme(a.dataset.theme);
  else if (act === "clear-jobs") {
    const list = await api().clear_jobs();
    S.jobs = {}; list.forEach((j) => (S.jobs[j.id] = j));
    refreshJobLists(); updateChrome();
  } else if (act === "change-dir") {
    const d = await api().pick_folder();
    if (d) { S.settings = await api().save_settings({ output_dir: d }); $$("#out-dir").forEach((i) => (i.value = d)); }
  } else if (act === "save-user") {
    const name = $("#set-user").value.trim() || "Kullanıcı";
    S.settings = await api().save_settings({ username: name });
    $("#user-name").textContent = name; $("#sm-user").textContent = name;
    $("#user-avatar").textContent = name[0].toLocaleUpperCase("tr");
    balloon("Kaydedildi", "Ayarların güncellendi.", "💾");
  } else if (act === "refresh-deps") {
    S.deps = await api().refresh_deps(); render(); updateChrome();
  } else if (t && act.startsWith("file")) {
    const f = S.files[t.id] || [], i = Number(a.dataset.i);
    if (act === "file-del") f.splice(i, 1);
    else if (act === "files-clear") f.length = 0;
    else if (act === "file-up" && i > 0) [f[i - 1], f[i]] = [f[i], f[i - 1]];
    else if (act === "file-down" && i < f.length - 1) [f[i + 1], f[i]] = [f[i], f[i + 1]];
    renderFiles(t);
  }
});

$("#start-btn").addEventListener("click", () => toggleStart());
$("#sm-close").addEventListener("click", () => toggleStart(false));
$("#sm-settings").addEventListener("click", () => { toggleStart(false); location.hash = "#/settings"; });
$("#btn-theme").addEventListener("click", () => {
  const cycle = { win2000: "win2000-dark", "win2000-dark": "xp-dark", "xp-dark": "xp-luna", "xp-luna": "win2000" };
  applyTheme(cycle[S.settings.theme] || "win2000");
});
$("#btn-folder").addEventListener("click", () => api().open_output_dir());
$("#btn-sidebar-folder").addEventListener("click", () => api().open_output_dir());
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") toggleStart(false);
  if (e.ctrlKey && e.key.toLowerCase() === "k") { e.preventDefault(); $("#search-input").focus(); }
});

let searchTimer;
$("#search-input").addEventListener("input", (e) => {
  clearTimeout(searchTimer);
  const q = e.target.value.trim();
  searchTimer = setTimeout(() => {
    if (q) location.hash = `#/search/${encodeURIComponent(q)}`;
    else if (location.hash.startsWith("#/search")) location.hash = "#/dashboard";
  }, 180);
});

let dragDepth = 0;
document.addEventListener("dragenter", (e) => { e.preventDefault(); dragDepth++; document.body.classList.add("dragging"); });
document.addEventListener("dragleave", () => { if (--dragDepth <= 0) { dragDepth = 0; document.body.classList.remove("dragging"); } });
document.addEventListener("dragover", (e) => e.preventDefault());
document.addEventListener("drop", (e) => { e.preventDefault(); dragDepth = 0; document.body.classList.remove("dragging"); });

window.addEventListener("hashchange", render);
if (window.pywebview?.api?.get_bootstrap) init();
else window.addEventListener("pywebviewready", init);
