/* MP2_ADDON — 番茄钟增强插件（自包含，无外部依赖）
 * 追加在 pomodoro/index.html 尾部，通过读取应用自身的 localStorage 数据工作：
 *   pomo_hist      {日期字符串: 当日番茄数}   —— 仅在「专注完成」时 +1，用作完成检测
 *   pomo_focus_log [{date, minutes, ...}]     —— 每次专注的分钟数
 *   pomo_day       {date, tom, min}
 * 新增数据写在 mp2_* 键下，不污染原应用。
 */
(function () {
  "use strict";
  if (window.__MP2_LOADED__) return;
  window.__MP2_LOADED__ = true;

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var KEY = { tasks: "mp2_tasks", active: "mp2_active", sound: "mp2_sound", zen: "mp2_zen", seen: "mp2_seen" };

  function ls(k, d) { try { var v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function dayKey(d) { return (d || new Date()).toDateString(); }

  /* ---------- 读取原应用的真实数据 ---------- */
  function hist() { return ls("pomo_hist", {}) || {}; }
  function focusLog() { var l = ls("pomo_focus_log", []); return Array.isArray(l) ? l : []; }
  function todayCount() { return hist()[dayKey()] || 0; }
  function minutesByDay() {
    var m = {};
    focusLog().forEach(function (r) { var k = r && r.date ? r.date : ""; if (!k) return; m[k] = (m[k] || 0) + (+r.minutes || 0); });
    return m;
  }
  function streakDays() {
    var h = hist(), n = 0, d = new Date();
    if (!(h[dayKey(d)] || 0)) d.setDate(d.getDate() - 1);   // 今天还没开始，从昨天往前算
    for (var i = 0; i < 400; i++) {
      if ((h[dayKey(d)] || 0) > 0) { n++; d.setDate(d.getDate() - 1); }
      else break;
    }
    return n;
  }
  function weekCount() {
    var h = hist(), d = new Date(), wd = (d.getDay() + 6) % 7, s = 0;
    var mon = new Date(d); mon.setDate(d.getDate() - wd);
    for (var i = 0; i < 7; i++) { var x = new Date(mon); x.setDate(mon.getDate() + i); if (x > d) break; s += (h[dayKey(x)] || 0); }
    return s;
  }
  function totalCount() { var h = hist(), s = 0; for (var k in h) if (Object.prototype.hasOwnProperty.call(h, k)) s += (+h[k] || 0); return s; }

  /* ---------- 读取计时器显示 ---------- */
  function readClock() {
    // 优先读 #bbTime（应用每帧写入 "HH:MM:SS"），翻页时钟的数字作兜底
    var t = $("#bbTime"), txt = t ? (t.textContent || "").trim() : "";
    if (!/^\d{1,2}:\d{2}:\d{2}$/.test(txt)) {
      var ds = $$("#flipClock .flip-digit");
      if (ds.length < 6) return null;
      var v = ds.map(function (d) { return d.getAttribute("data-v"); }).join("");
      if (!/^\d{6}$/.test(v)) return null;
      txt = v.slice(0, 2) + ":" + v.slice(2, 4) + ":" + v.slice(4, 6);
    }
    var p = txt.split(":");
    var h = +p[0], m = +p[1], s = +p[2];
    return { h: h, m: m, s: s, total: h * 3600 + m * 60 + s };
  }
  function isRunning() { var b = $("#startBtn"); return !!b && /暂停|停止/.test(b.textContent || ""); }

  /* ---------- 样式 ---------- */
  var CSS = [
    ".mp2-fab{position:fixed;left:16px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:99998;",
    "width:52px;height:52px;border-radius:50%;border:1px solid rgba(255,255,255,.18);cursor:pointer;",
    "background:linear-gradient(145deg,#ff7a6e,#ff3b30);color:#fff;font-size:22px;line-height:1;",
    "display:flex;align-items:center;justify-content:center;box-shadow:0 12px 30px rgba(255,59,48,.36);transition:transform .2s;}",
    ".mp2-fab:active{transform:scale(.92);}",
    ".mp2-fab.on{background:linear-gradient(145deg,#8b7bff,#5b47e0);box-shadow:0 12px 30px rgba(91,71,224,.4);}",
    ".mp2-panel{position:fixed;left:0;right:0;bottom:0;z-index:99999;max-height:78vh;overflow:auto;",
    "background:rgba(16,16,26,.97);backdrop-filter:blur(14px);border-top:1px solid rgba(255,255,255,.14);",
    "border-radius:20px 20px 0 0;padding:14px 16px calc(18px + env(safe-area-inset-bottom));",
    "color:#fff;font:14px/1.55 -apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',system-ui,sans-serif;",
    "transform:translateY(102%);transition:transform .28s cubic-bezier(.22,1,.36,1);box-shadow:0 -18px 50px rgba(0,0,0,.5);}",
    ".mp2-panel.show{transform:translateY(0);}",
    ".mp2-tabs{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;}",
    ".mp2-tab{flex:1 1 auto;min-width:72px;padding:8px 10px;border-radius:11px;cursor:pointer;text-align:center;",
    "background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);font-size:13px;color:rgba(255,255,255,.72);}",
    ".mp2-tab.on{background:rgba(255,94,87,.22);border-color:rgba(255,94,87,.5);color:#fff;font-weight:600;}",
    ".mp2-pane{display:none;} .mp2-pane.on{display:block;}",
    ".mp2-row{display:flex;gap:8px;align-items:center;margin-bottom:10px;flex-wrap:wrap;}",
    ".mp2-in{flex:1 1 160px;min-width:0;padding:9px 12px;border-radius:11px;border:1px solid rgba(255,255,255,.14);",
    "background:rgba(255,255,255,.06);color:#fff;font-size:14px;outline:none;}",
    ".mp2-in:focus{border-color:rgba(255,94,87,.6);}",
    ".mp2-btn{padding:9px 13px;border-radius:11px;border:1px solid rgba(255,255,255,.14);cursor:pointer;",
    "background:rgba(255,255,255,.08);color:#fff;font-size:13px;white-space:nowrap;}",
    ".mp2-btn.pri{background:linear-gradient(145deg,#ff7a6e,#ff3b30);border-color:transparent;font-weight:600;}",
    ".mp2-btn.on{background:rgba(255,94,87,.26);border-color:rgba(255,94,87,.55);}",
    ".mp2-list{list-style:none;margin:0;padding:0;max-height:44vh;overflow:auto;}",
    ".mp2-item{display:flex;align-items:center;gap:10px;padding:10px 11px;margin-bottom:8px;border-radius:12px;",
    "background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.09);}",
    ".mp2-item.act{border-color:rgba(255,94,87,.65);background:rgba(255,94,87,.14);}",
    ".mp2-item.done{opacity:.5;} .mp2-item.done .mp2-name{text-decoration:line-through;}",
    ".mp2-name{flex:1 1 auto;min-width:0;word-break:break-all;cursor:pointer;}",
    ".mp2-cnt{flex:0 0 auto;font-size:12px;color:#ffb3ae;background:rgba(255,94,87,.16);",
    "border-radius:8px;padding:3px 8px;white-space:nowrap;}",
    ".mp2-x{flex:0 0 auto;border:0;background:transparent;color:rgba(255,255,255,.45);cursor:pointer;font-size:17px;padding:0 2px;}",
    ".mp2-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(88px,1fr));gap:8px;margin-bottom:12px;}",
    ".mp2-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.09);border-radius:12px;padding:10px;text-align:center;}",
    ".mp2-card b{display:block;font-size:20px;line-height:1.2;} .mp2-card span{font-size:11px;color:rgba(255,255,255,.55);}",
    ".mp2-sec{font-size:12px;color:rgba(255,255,255,.5);margin:14px 0 8px;letter-spacing:.02em;}",
    ".mp2-heat{display:grid;grid-template-columns:repeat(10,1fr);gap:4px;}",
    ".mp2-cell{aspect-ratio:1;border-radius:4px;background:rgba(255,255,255,.07);}",
    ".mp2-bars{display:flex;align-items:flex-end;gap:6px;height:104px;}",
    ".mp2-bar{flex:1;background:linear-gradient(180deg,#ff7a6e,#ff3b30);border-radius:5px 5px 0 0;min-height:3px;position:relative;}",
    ".mp2-bar i{position:absolute;bottom:-18px;left:0;right:0;text-align:center;font-size:10px;font-style:normal;color:rgba(255,255,255,.45);}",
    ".mp2-lbl{display:flex;justify-content:space-between;font-size:11px;color:rgba(255,255,255,.45);margin-top:22px;}",
    ".mp2-hint{font-size:12px;color:rgba(255,255,255,.45);line-height:1.7;}",
    ".mp2-kbd{display:inline-block;min-width:20px;text-align:center;padding:1px 6px;margin:0 2px;border-radius:5px;",
    "background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);font-size:11px;}",
    ".mp2-zen{position:fixed;inset:0;z-index:99990;background:rgba(4,4,10,.86);backdrop-filter:blur(3px);",
    "display:flex;align-items:center;justify-content:center;flex-direction:column;gap:14px;color:#fff;}",
    ".mp2-zen .t{font-size:clamp(56px,16vw,120px);font-weight:200;letter-spacing:.02em;font-variant-numeric:tabular-nums;}",
    ".mp2-zen .m{font-size:14px;color:rgba(255,255,255,.6);}",
    ".mp2-zen .x{margin-top:10px;font-size:12px;color:rgba(255,255,255,.4);}",
    "@media (max-width:420px){.mp2-fab{width:46px;height:46px;font-size:19px;} .mp2-heat{grid-template-columns:repeat(7,1fr);}}"
  ].join("\n");

  var st = document.createElement("style");
  st.textContent = CSS;
  document.head.appendChild(st);

  /* ---------- 音频（Web Audio 实时合成，无音频文件） ---------- */
  var AC = null, amb = null, ambGain = null, ambKind = "";
  function ac() {
    if (!AC) { var C = window.AudioContext || window.webkitAudioContext; if (C) AC = new C(); }
    if (AC && AC.state === "suspended") AC.resume();
    return AC;
  }
  function noiseBuffer(sec) {
    var c = ac(), n = Math.floor(c.sampleRate * sec), b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0), last = 0;
    for (var i = 0; i < n; i++) { var w = Math.random() * 2 - 1; last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; } // brown-ish
    return b;
  }
  function startAmbient(kind) {
    stopAmbient();
    var c = ac(); if (!c) return;
    ambKind = kind;
    var src = c.createBufferSource();
    src.buffer = noiseBuffer(4); src.loop = true;
    var f = c.createBiquadFilter();
    if (kind === "rain") { f.type = "highpass"; f.frequency.value = 900; }
    else if (kind === "cafe") { f.type = "lowpass"; f.frequency.value = 620; }
    else { f.type = "bandpass"; f.frequency.value = 1200; f.Q.value = 0.6; }
    ambGain = c.createGain();
    ambGain.gain.value = 0;
    src.connect(f); f.connect(ambGain); ambGain.connect(c.destination);
    src.start();
    amb = src;
    ambGain.gain.linearRampToValueAtTime(vol(), c.currentTime + 1.2);
  }
  function stopAmbient() {
    if (amb) { try { amb.stop(); } catch (e) {} amb = null; }
    ambKind = "";
  }
  function vol() { var v = ls(KEY.sound, null); return (v && typeof v.vol === "number") ? v.vol : 0.35; }
  function setVol(v) { var s = ls(KEY.sound, {}) || {}; s.vol = v; save(KEY.sound, s); if (ambGain && ac()) ambGain.gain.linearRampToValueAtTime(v, ac().currentTime + 0.15); }

  function chime(kind) {
    var c = ac(); if (!c) return;
    var notes = kind === "break" ? [523.25, 659.25] : [659.25, 783.99, 1046.5];
    notes.forEach(function (f, i) {
      var o = c.createOscillator(), g = c.createGain(), t = c.currentTime + i * 0.16;
      o.type = "sine"; o.frequency.value = f;
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(0.28, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 1.1);
      o.connect(g); g.connect(c.destination); o.start(t); o.stop(t + 1.2);
    });
  }
  function notify(title, body) {
    try {
      if (!("Notification" in window)) return;
      if (Notification.permission === "granted") new Notification(title, { body: body, icon: "" });
      else if (Notification.permission === "default") Notification.requestPermission();
    } catch (e) {}
  }

  /* ---------- 任务清单 ---------- */
  function tasks() { var t = ls(KEY.tasks, []); return Array.isArray(t) ? t : []; }
  function activeId() { return ls(KEY.active, null); }
  function renderTasks() {
    var ul = $("#mp2TaskList"), ts = tasks(), act = activeId();
    if (!ul) return;
    ul.innerHTML = "";
    if (!ts.length) { ul.innerHTML = '<li class="mp2-hint" style="padding:6px 2px">还没有任务。添加一个，完成的番茄会自动记到它头上。</li>'; return; }
    ts.forEach(function (t) {
      var li = document.createElement("li");
      li.className = "mp2-item" + (t.done ? " done" : "") + (t.id === act ? " act" : "");
      li.innerHTML = '<span class="mp2-name"></span><span class="mp2-cnt"></span><button class="mp2-x" title="删除">×</button>';
      $(".mp2-name", li).textContent = t.name;
      $(".mp2-cnt", li).textContent = "🍅 " + (t.pomos || 0);
      $(".mp2-name", li).onclick = function () {
        save(KEY.active, (activeId() === t.id) ? null : t.id);
        renderTasks();
      };
      $(".mp2-x", li).onclick = function () {
        save(KEY.tasks, tasks().filter(function (x) { return x.id !== t.id; }));
        if (activeId() === t.id) save(KEY.active, null);
        renderTasks();
      };
      ul.appendChild(li);
    });
  }

  /* ---------- 统计图表 ---------- */
  function renderStats() {
    var box = $("#mp2Stat"); if (!box) return;
    var h = hist(), mins = minutesByDay();
    var cards = [
      ["今日", todayCount()], ["本周", weekCount()], ["累计", totalCount()], ["连续", streakDays() + "天"]
    ].map(function (c) { return '<div class="mp2-card"><b>' + c[1] + "</b><span>" + c[0] + "</span></div>"; }).join("");

    // 30 天热力图
    var cells = "", max = 1;
    for (var i = 29; i >= 0; i--) { var d = new Date(); d.setDate(d.getDate() - i); max = Math.max(max, h[dayKey(d)] || 0); }
    for (var j = 29; j >= 0; j--) {
      var dd = new Date(); dd.setDate(dd.getDate() - j);
      var n = h[dayKey(dd)] || 0;
      var a = n ? (0.25 + 0.75 * (n / max)) : 0;
      var bg = n ? "rgba(255,94,87," + a.toFixed(2) + ")" : "rgba(255,255,255,.07)";
      cells += '<div class="mp2-cell" title="' + dayKey(dd) + "：" + n + ' 个" style="background:' + bg + '"></div>';
    }
    // 近 7 天分钟柱状图
    var bars = "", labels = "", maxM = 1, days = [];
    for (var k = 6; k >= 0; k--) { var dk = new Date(); dk.setDate(dk.getDate() - k); var mv = mins[dayKey(dk)] || 0; days.push([dk, mv]); maxM = Math.max(maxM, mv); }
    days.forEach(function (p) {
      var pct = Math.round((p[1] / maxM) * 100);
      bars += '<div class="mp2-bar" style="height:' + Math.max(3, pct) + '%" title="' + p[1] + ' 分钟"></div>';
    });
    labels = '<div class="mp2-lbl"><span>' + days[0][0].getDate() + "日</span><span>近 7 天专注分钟</span><span>" + days[6][0].getDate() + "日</span></div>";

    box.innerHTML =
      '<div class="mp2-cards">' + cards + "</div>" +
      '<div class="mp2-sec">最近 30 天（颜色越深番茄越多）</div>' +
      '<div class="mp2-heat">' + cells + "</div>" +
      '<div class="mp2-sec">专注分钟</div>' +
      '<div class="mp2-bars">' + bars + "</div>" + labels;
  }

  /* ---------- 沉浸模式 ---------- */
  var zenEl = null;
  function toggleZen(force) {
    if (zenEl) { zenEl.remove(); zenEl = null; return; }
    if (force === false) return;
    zenEl = document.createElement("div");
    zenEl.className = "mp2-zen";
    zenEl.innerHTML = '<div class="t">--:--</div><div class="m">专注中</div><div class="x">按 F 或 Esc 退出沉浸模式</div>';
    document.body.appendChild(zenEl);
    zenEl.onclick = function () { toggleZen(); };
    updateZen();
  }
  function updateZen() {
    if (!zenEl) return;
    var c = readClock(), t = $(".t", zenEl);
    if (!t) return;
    t.textContent = c ? (c.h > 0 ? (c.h + ":" + pad(c.m) + ":" + pad(c.s)) : (pad(c.m) + ":" + pad(c.s))) : "--:--";
    $(".m", zenEl).textContent = isRunning() ? "专注中" : "已暂停";
  }
  function pad(n) { return (n < 10 ? "0" : "") + n; }

  /* ---------- 完成检测 ---------- */
  var lastCount = todayCount();
  function onComplete() {
    var act = activeId();
    if (act) {
      var ts = tasks().map(function (t) { if (t.id === act) { t.pomos = (t.pomos || 0) + 1; } return t; });
      save(KEY.tasks, ts);
      var t0 = ts.filter(function (x) { return x.id === act; })[0];
      if (t0) notify("🍅 番茄完成", "《" + t0.name + "》已累计 " + t0.pomos + " 个番茄");
    } else {
      notify("🍅 番茄完成", "今日第 " + todayCount() + " 个，休息一下");
    }
    chime("focus");
    renderTasks(); renderStats();
  }
  function tick() {
    var c = todayCount();
    if (c > lastCount) { lastCount = c; onComplete(); }
    else if (c < lastCount) { lastCount = c; }   // 日期切换/重置
    document.title = (function () {
      var k = readClock();
      if (!k) return "番茄钟 · 专注";
      var s = k.h > 0 ? (k.h + ":" + pad(k.m) + ":" + pad(k.s)) : (pad(k.m) + ":" + pad(k.s));
      return (isRunning() ? "▶ " : "⏸ ") + s + " · 番茄钟";
    })();
    updateZen();
  }

  /* ---------- 面板 UI ---------- */
  function build() {
    var fab = document.createElement("button");
    fab.className = "mp2-fab"; fab.id = "mp2Fab"; fab.title = "增强功能（任务 / 统计 / 音效 / 快捷键）";
    fab.textContent = "✨";
    document.body.appendChild(fab);

    var panel = document.createElement("div");
    panel.className = "mp2-panel"; panel.id = "mp2Panel";
    panel.innerHTML = [
      '<div class="mp2-tabs">',
      '  <div class="mp2-tab on" data-p="task">任务</div>',
      '  <div class="mp2-tab" data-p="stat">统计</div>',
      '  <div class="mp2-tab" data-p="snd">音效</div>',
      '  <div class="mp2-tab" data-p="key">快捷键</div>',
      "</div>",
      '<div class="mp2-pane on" data-p="task">',
      '  <div class="mp2-row"><input class="mp2-in" id="mp2NewTask" placeholder="要专注的事…" maxlength="60"><button class="mp2-btn pri" id="mp2Add">添加</button></div>',
      '  <ul class="mp2-list" id="mp2TaskList"></ul>',
      '  <div class="mp2-hint">点任务名可设为「当前任务」，之后完成的番茄会自动累计到它。</div>',
      "</div>",
      '<div class="mp2-pane" data-p="stat"><div id="mp2Stat"></div></div>',
      '<div class="mp2-pane" data-p="snd">',
      '  <div class="mp2-sec">环境音（实时合成，不占体积）</div>',
      '  <div class="mp2-row">',
      '    <button class="mp2-btn" data-amb="rain">🌧 雨声</button>',
      '    <button class="mp2-btn" data-amb="white">📻 白噪音</button>',
      '    <button class="mp2-btn" data-amb="cafe">☕ 咖啡厅</button>',
      '    <button class="mp2-btn" data-amb="off">停止</button>',
      "  </div>",
      '  <div class="mp2-row"><span style="font-size:13px;color:rgba(255,255,255,.6)">音量</span>',
      '    <input type="range" id="mp2Vol" min="0" max="1" step="0.05" style="flex:1;min-width:120px"></div>',
      '  <div class="mp2-sec">提示音</div>',
      '  <div class="mp2-row"><button class="mp2-btn" id="mp2Chime">试听完成提示音</button>',
      '    <button class="mp2-btn" id="mp2Noti">开启桌面通知</button></div>',
      '  <div class="mp2-hint">每个专注段结束会自动播放提示音并发通知（需已授权）。</div>',
      "</div>",
      '<div class="mp2-pane" data-p="key">',
      '  <div class="mp2-hint" style="font-size:13px;line-height:2">',
      '    <span class="mp2-kbd">空格</span> 开始 / 暂停<br>',
      '    <span class="mp2-kbd">S</span> 跳过当前阶段<br>',
      '    <span class="mp2-kbd">R</span> 重置<br>',
      '    <span class="mp2-kbd">F</span> 沉浸模式（全屏倒计时）<br>',
      '    <span class="mp2-kbd">Esc</span> 关闭面板 / 退出沉浸<br>',
      '    <span class="mp2-kbd">T</span> 打开本面板',
      "  </div>",
      '  <div class="mp2-sec">说明</div>',
      '  <div class="mp2-hint">标签页标题会实时显示剩余时间，切到别的标签也能看到倒计时。</div>',
      "</div>"
    ].join("");
    document.body.appendChild(panel);

    fab.onclick = function () {
      var open = panel.classList.toggle("show");
      fab.classList.toggle("on", open);
      fab.textContent = open ? "✕" : "✨";
      if (open) { renderTasks(); renderStats(); }
    };

    $$(".mp2-tab", panel).forEach(function (t) {
      t.onclick = function () {
        $$(".mp2-tab", panel).forEach(function (x) { x.classList.remove("on"); });
        $$(".mp2-pane", panel).forEach(function (x) { x.classList.remove("on"); });
        t.classList.add("on");
        var p = $('.mp2-pane[data-p="' + t.getAttribute("data-p") + '"]', panel);
        if (p) p.classList.add("on");
        if (t.getAttribute("data-p") === "stat") renderStats();
        if (t.getAttribute("data-p") === "task") renderTasks();
      };
    });

    function addTask() {
      var i = $("#mp2NewTask"), v = (i.value || "").trim();
      if (!v) return;
      var ts = tasks(); ts.push({ id: "t" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), name: v, pomos: 0, done: false });
      save(KEY.tasks, ts);
      if (!activeId()) save(KEY.active, ts[ts.length - 1].id);
      i.value = ""; renderTasks();
    }
    $("#mp2Add").onclick = addTask;
    $("#mp2NewTask").addEventListener("keydown", function (e) { if (e.key === "Enter") addTask(); });

    $$("[data-amb]", panel).forEach(function (b) {
      b.onclick = function () {
        var k = b.getAttribute("data-amb");
        $$("[data-amb]", panel).forEach(function (x) { x.classList.remove("on"); });
        if (k === "off") { stopAmbient(); return; }
        b.classList.add("on"); startAmbient(k);
      };
    });
    var vr = $("#mp2Vol"); vr.value = vol();
    vr.oninput = function () { setVol(parseFloat(vr.value)); };
    $("#mp2Chime").onclick = function () { chime("focus"); };
    $("#mp2Noti").onclick = function () {
      if (!("Notification" in window)) { alert("当前浏览器不支持桌面通知"); return; }
      Notification.requestPermission().then(function (p) { alert(p === "granted" ? "已开启桌面通知" : "通知权限：" + p); });
    };

    /* 快捷键 */
    document.addEventListener("keydown", function (e) {
      var tag = (e.target && e.target.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea" || e.metaKey || e.ctrlKey || e.altKey) return;
      var k = e.key.toLowerCase();
      if (e.code === "Space" || k === " ") { e.preventDefault(); var b = $("#startBtn"); if (b) b.click(); }
      else if (k === "s") { var s = $("#skipBtn"); if (s) s.click(); }
      else if (k === "r") { var r = $("#resetBtn"); if (r) r.click(); }
      else if (k === "f") { e.preventDefault(); toggleZen(); }
      else if (k === "t") { fab.click(); }
      else if (k === "escape") {
        if (zenEl) toggleZen();
        else if (panel.classList.contains("show")) fab.click();
      }
    });

    renderTasks(); renderStats();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();

  setInterval(tick, 1000);
  window.addEventListener("storage", function (e) { if (e.key === "pomo_hist" || e.key === "pomo_focus_log") renderStats(); });
})();
