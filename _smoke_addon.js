/* 冒烟测试：用最小 DOM 跑一遍注入到 pomodoro/index.html 的 MP2 插件，捕获运行时错误。 */
const fs = require('fs');
const path = require('path');
const JSDOM_MOD = process.env.JSDOM_MOD || 'jsdom';
const { JSDOM, VirtualConsole } = require(JSDOM_MOD);

const HTML_PATH = path.join(__dirname, 'pomodoro', 'index.html');
const BEGIN = '<!-- MP2_ADDON_BEGIN -->';
const END = '<!-- MP2_ADDON_END -->';

const html = fs.readFileSync(HTML_PATH, 'utf8');
const a = html.indexOf(BEGIN), b = html.indexOf(END);
if (a < 0 || b < 0) { console.error('FAIL: 未找到注入块'); process.exit(1); }
const block = html.slice(a, b);
const m = block.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error('FAIL: 注入块里没有 script'); process.exit(1); }
const addon = m[1];
console.log('取到插件代码 ' + (addon.length / 1024).toFixed(1) + ' KB');

// 构造最小页面：只包含插件依赖的元素
const page = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>番茄钟 · 专注</title></head><body>
<button class="btn primary" id="startBtn">开始</button>
<button class="btn" id="resetBtn">重置</button>
<button class="btn" id="skipBtn">跳过</button>
<div class="flip-clock" id="flipClock"><div class="flip-group">
<div class="flip-digit" data-v="0"><span class="d">0</span></div>
<div class="flip-digit" data-v="0"><span class="d">0</span></div></div><div class="colon">:</div>
<div class="flip-group"><div class="flip-digit" data-v="2"><span class="d">2</span></div>
<div class="flip-digit" data-v="5"><span class="d">5</span></div></div><div class="colon">:</div>
<div class="flip-group"><div class="flip-digit" data-v="0"><span class="d">0</span></div>
<div class="flip-digit" data-v="0"><span class="d">0</span></div></div></div>
<script>${addon}<\/script>
</body></html>`;

const errors = [];
const dom = new JSDOM(page, {
  runScripts: 'dangerously',
  url: 'https://example.com/pomodoro/',
  pretendToBeVisual: true,
  virtualConsole: new VirtualConsole()
    .on('jsdomError', e => errors.push('jsdomError: ' + e.message))
    .on('error', (...a) => errors.push('console.error: ' + a.join(' ')))
});

const { window } = dom;
const doc = window.document;

function ok(label, cond, extra) {
  console.log((cond ? '  PASS  ' : '  FAIL  ') + label + (extra ? '  ' + extra : ''));
  if (!cond) process.exitCode = 1;
}

// 预置数据（模拟原应用写入的 localStorage）
const today = new Date();
const y1 = new Date(today); y1.setDate(y1.getDate() - 1);
const y2 = new Date(today); y2.setDate(y2.getDate() - 2);
const hist = {}; hist[today.toDateString()] = 3; hist[y1.toDateString()] = 5; hist[y2.toDateString()] = 2;
window.localStorage.setItem('pomo_hist', JSON.stringify(hist));
window.localStorage.setItem('pomo_focus_log', JSON.stringify([
  { date: today.toDateString(), minutes: 25 }, { date: y1.toDateString(), minutes: 50 },
  { date: y2.toDateString(), minutes: 25 }
]));

// 依赖 localStorage 的函数在脚本运行时才读取，需重新触发一次渲染
window.__MP2_TEST_RERENDER__ = true;

setTimeout(() => {
  console.log('\n=== DOM 构建 ===');
  ok('悬浮按钮 #mp2Fab 已创建', !!doc.querySelector('#mp2Fab'));
  ok('面板 #mp2Panel 已创建', !!doc.querySelector('#mp2Panel'));
  ok('注入了 <style>', doc.querySelectorAll('style').length >= 1);
  ok('任务输入框存在', !!doc.querySelector('#mp2NewTask'));
  ok('统计容器存在', !!doc.querySelector('#mp2Stat'));

  console.log('\n=== 任务清单 ===');
  const input = doc.querySelector('#mp2NewTask');
  input.value = '写周报';
  doc.querySelector('#mp2Add').click();
  const items = doc.querySelectorAll('#mp2TaskList .mp2-item');
  ok('添加任务后出现 1 条', items.length === 1, '实际 ' + items.length);
  ok('任务名正确', items[0] && items[0].querySelector('.mp2-name').textContent === '写周报');
  ok('已写入 localStorage', JSON.parse(window.localStorage.getItem('mp2_tasks') || '[]').length === 1);

  console.log('\n=== 统计图表 ===');
  doc.querySelector('.mp2-tab[data-p="stat"]').click();
  const stat = doc.querySelector('#mp2Stat');
  ok('渲染了 4 张概览卡', stat.querySelectorAll('.mp2-card').length === 4);
  ok('热力图 30 格', stat.querySelectorAll('.mp2-cell').length === 30);
  ok('柱状图 7 根', stat.querySelectorAll('.mp2-bar').length === 7);
  const cardVals = Array.from(stat.querySelectorAll('.mp2-card b')).map(e => e.textContent);
  ok('累计=10（3+5+2）', cardVals[2] === '10', '概览: ' + cardVals.join(' / '));

  console.log('\n=== 快捷键 ===');
  let clicked = null;
  doc.querySelector('#startBtn').addEventListener('click', () => { clicked = 'start'; });
  doc.querySelector('#skipBtn').addEventListener('click', () => { clicked = 'skip'; });
  window.document.dispatchEvent(new window.KeyboardEvent('keydown', { key: ' ', code: 'Space', bubbles: true }));
  ok('空格触发开始/暂停', clicked === 'start', '实际 ' + clicked);
  clicked = null;
  window.document.dispatchEvent(new window.KeyboardEvent('keydown', { key: 's', bubbles: true }));
  ok('S 触发跳过', clicked === 'skip', '实际 ' + clicked);

  console.log('\n=== 标题倒计时 ===');
  ok('标题已更新为倒计时', /▶|⏸/.test(doc.title), 'title=' + doc.title);

  console.log('\n=== 音频（jsdom 无 AudioContext，应安全跳过）===');
  let audioErr = null;
  try { doc.querySelector('[data-amb="rain"]').click(); } catch (e) { audioErr = e.message; }
  ok('点击环境音未抛错', audioErr === null, audioErr || '');

  console.log('\n=== 运行时错误 ===');
  ok('无未捕获错误', errors.length === 0, errors.join(' | '));

  console.log('\n' + (process.exitCode ? '❌ 有用例失败' : '✅ 全部通过'));
  try { dom.window.close(); } catch (e) {}
  process.exit(process.exitCode || 0);
}, 1200);
