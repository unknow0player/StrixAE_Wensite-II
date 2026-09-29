// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function () {
  console.log("✅ StrixAE 页面加载成功！");

  // 平滑滚动（论文官网必备）
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const href = this.getAttribute('href');
      if (href === '#') return;
      const target = document.getElementById(href.slice(1));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
});
