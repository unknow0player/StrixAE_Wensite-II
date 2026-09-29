const $ = id => document.getElementById(id);
let csrf = '', slots = [], loading = false;
function status(message, error = false) { $('status').textContent = message; $('status').className = error ? 'error' : ''; }
async function api(path, options = {}) {
  const response = await fetch(path, {...options, headers: {...options.headers, 'X-CSRF-Token': csrf}, cache: 'no-store'});
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401) { $('manager').hidden = true; $('login-panel').hidden = false; }
    throw new Error(result.error || '请求失败，请重试。');
  }
  return result;
}
function base() { return `/api/slots/${$('sample').value}/${$('role').value}`; }
function setBusy(value) {
  loading = value;
  document.querySelectorAll('#manager button, #manager input, #manager select').forEach(el => el.disabled = value);
}
async function refresh() {
  slots = (await api('/api/samples')).slots;
  await preview();
}
async function preview() {
  const path = base();
  const slot = slots.find(s => s.sample === Number($('sample').value) && s.role === $('role').value);
  $('preview-title').textContent = `Sample ${slot.sample} · ${slot.label}`;
  $('metadata').textContent = slot.id ? `${slot.filename} · ${slot.duration} 秒 · ${slot.sample_rate} Hz · ${slot.channels} 声道` : '原始页面内容';
  $('preview-audio').src = slot.audio;
  $('preview-image').hidden = !slot.image;
  if (slot.image) $('preview-image').src = slot.image;
  $('no-image').textContent = slot.image ? '' : '原始 Mixture 未配置频谱图，上传后可在这里预览。';
  $('history').textContent = '正在读取…';
  const result = await api(path + '/history');
  if (base() !== path) return;
  $('history').replaceChildren();
  if (!result.versions.length) $('history').textContent = '这个位置还没有上传记录。';
  for (const item of result.versions) {
    const row = document.createElement('div'); row.className = 'version';
    const label = document.createElement('span');
    label.textContent = `${new Date(item.created_at).toLocaleString()} · ${item.filename} · ${item.duration} 秒${slot.id === item.id ? ' · 当前版本' : ''}`;
    const button = document.createElement('button'); button.className = 'secondary';
    button.textContent = slot.id === item.id ? '正在使用' : '恢复此版本'; button.disabled = slot.id === item.id;
    button.onclick = () => restore(item.id);
    row.append(label, button); $('history').append(row);
  }
}
async function restore(version) {
  if (loading || !confirm(`确认恢复 Sample ${$('sample').value} / ${$('role').selectedOptions[0].textContent} 的${version ? '所选历史版本' : '原始内容'}？`)) return;
  setBusy(true);
  try {
    await api(base() + '/restore', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({version_id: version})});
    await refresh(); status('已恢复。展示页刷新或等待最多 10 秒后更新。');
  } catch (error) { status(error.message, true); }
  finally { setBusy(false); }
}
$('login').onsubmit = async event => {
  event.preventDefault();
  const button = event.submitter; button.disabled = true;
  try {
    const result = await api('/api/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({password: $('password').value})});
    csrf = result.csrf; $('password').value = '';
    $('login-panel').hidden = true; $('manager').hidden = false;
    await refresh(); status('已连接，可以上传音频。');
  } catch (error) { status(error.message, true); }
  finally { button.disabled = false; }
};
$('upload').onsubmit = async event => {
  event.preventDefault(); if (loading) return;
  const file = $('file').files[0]; if (!file) return;
  if (file.size > 25 * 1024 * 1024) return status('文件不能超过 25 MB。', true);
  const form = new FormData(); form.append('file', file);
  setBusy(true); status('正在上传并生成频谱图，请等待完成…');
  try {
    await api(base() + '/upload', {method: 'POST', body: form});
    $('file').value = ''; await refresh();
    status('上传完成，音频与频谱图已一起发布。展示页刷新或等待最多 10 秒后更新。');
  } catch (error) { status(error.message, true); }
  finally { setBusy(false); }
};
$('sample').onchange = $('role').onchange = () => preview().catch(error => status(error.message, true));
$('reset').onclick = () => restore(null);
$('logout').onclick = async () => {
  try { await api('/api/logout', {method: 'POST'}); location.reload(); }
  catch (error) { status(error.message, true); }
};
(async () => {
  try {
    const result = await api('/api/session'); csrf = result.csrf;
    $('login-panel').hidden = result.authenticated; $('manager').hidden = !result.authenticated;
    if (result.authenticated) await refresh();
    status(result.authenticated ? '已连接，可以上传音频。' : '请使用本机生成的管理密码登录。');
  } catch (error) { status(error.message, true); }
})();
