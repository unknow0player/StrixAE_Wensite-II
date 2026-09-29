(() => {
  let busy = false;
  async function refresh() {
    if (busy || document.hidden) return;
    busy = true;
    try {
      const response = await fetch('/api/samples', {cache: 'no-store'});
      if (!response.ok) throw new Error('无法读取音频列表');
      const {slots} = await response.json();
      const samples = document.querySelectorAll('.demo-sample');
      for (const slot of slots) {
        const sample = samples[slot.sample - 1];
        if (!sample) continue;
        const index = ['ground_truth', 'tf_gridnet', 'strixae'].indexOf(slot.role);
        const container = index < 0 ? sample.querySelector('.mix-audio') : sample.querySelectorAll('.demo-grid .item')[index];
        if (!container) continue;
        const audio = container.querySelector('audio');
        if (audio.src !== new URL(slot.audio, location.origin).href) {
          audio.src = slot.audio;
          audio.load();
        }
        const img = container.querySelector('.mel img');
        if (img && slot.image && img.src !== new URL(slot.image, location.origin).href) {
          img.src = slot.image;
        }
      }
    } catch (error) {
      console.warn('后台暂时不可用，保留当前展示内容。', error);
    } finally { busy = false; }
  }
  refresh();
  window.addEventListener('focus', refresh);
  document.addEventListener('visibilitychange', refresh);
  setInterval(refresh, 10000);
})();
