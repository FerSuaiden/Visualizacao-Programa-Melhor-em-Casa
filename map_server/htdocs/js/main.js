/* ============================================
   Melhor em Casa — Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ---------- Mobile Nav ---------- */
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
    navLinks.querySelectorAll('a').forEach(a =>
      a.addEventListener('click', () => navLinks.classList.remove('open'))
    );
  }

  /* ---------- Active Page Highlight ---------- */
  const page = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(a => {
    const href = a.getAttribute('href');
    if (href === page || (page === '' && href === 'index.html')) {
      a.classList.add('active');
    }
  });

  /* ---------- Enhanced Image Viewer / Lightbox ---------- */
  const overlay = document.getElementById('lightbox');
  if (overlay) {
    const container = overlay.querySelector('.lb-img-container');
    const lbImg = container.querySelector('img');
    const zoomLabel = overlay.querySelector('.lb-zoom-level');
    const hint = overlay.querySelector('.lb-hint');

    let scale = 1;
    let panX = 0, panY = 0;
    let isDragging = false;
    let dragMoved = false;
    let startX, startY, startPanX, startPanY;
    const MIN_SCALE = 0.5;
    const MAX_SCALE = 8;
    const ZOOM_STEP = 0.25;

    function updateTransform(smooth) {
      if (!smooth) lbImg.classList.add('no-transition');
      else lbImg.classList.remove('no-transition');
      lbImg.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
      zoomLabel.textContent = Math.round(scale * 100) + '%';
    }

    function resetView() {
      scale = 1;
      panX = 0;
      panY = 0;
      updateTransform(true);
    }

    function zoomTo(newScale, centerX, centerY) {
      newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, newScale));
      if (centerX !== undefined && centerY !== undefined) {
        const rect = container.getBoundingClientRect();
        const cx = centerX - rect.left - rect.width / 2;
        const cy = centerY - rect.top - rect.height / 2;
        const factor = newScale / scale;
        panX = cx - factor * (cx - panX);
        panY = cy - factor * (cy - panY);
      }
      scale = newScale;
      updateTransform(true);
    }

    function openViewer(src, alt) {
      lbImg.src = src;
      lbImg.alt = alt;
      resetView();
      overlay.classList.add('active');
      hint.classList.remove('hidden');
      clearTimeout(hint._timer);
      hint._timer = setTimeout(() => hint.classList.add('hidden'), 3000);
    }

    function closeViewer() {
      overlay.classList.remove('active');
      lbImg.src = '';
    }

    // Bind clickable images
    function bindImages() {
      document.querySelectorAll('.card img, img.zoomable').forEach(img => {
        if (img.dataset.lbBound) return;
        img.dataset.lbBound = '1';
        img.style.cursor = 'zoom-in';
        img.addEventListener('click', () => openViewer(img.src, img.alt));
      });
    }
    bindImages();
    window.__bindLightbox = bindImages;

    // Toolbar buttons
    document.getElementById('lb-close').addEventListener('click', closeViewer);
    document.getElementById('lb-zoom-in').addEventListener('click', () => zoomTo(scale + ZOOM_STEP));
    document.getElementById('lb-zoom-out').addEventListener('click', () => zoomTo(scale - ZOOM_STEP));
    document.getElementById('lb-reset').addEventListener('click', resetView);

    document.getElementById('lb-fullscreen').addEventListener('click', () => {
      if (!document.fullscreenElement) overlay.requestFullscreen().catch(() => {});
      else document.exitFullscreen();
    });

    document.getElementById('lb-download').addEventListener('click', () => {
      const a = document.createElement('a');
      a.href = lbImg.src;
      a.download = decodeURIComponent(lbImg.src.split('/').pop()) || 'chart.png';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    });

    // Mouse wheel zoom
    container.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
      zoomTo(scale + delta, e.clientX, e.clientY);
    }, { passive: false });

    // Pan with mouse drag
    container.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      isDragging = true;
      dragMoved = false;
      startX = e.clientX;
      startY = e.clientY;
      startPanX = panX;
      startPanY = panY;
      container.classList.add('dragging');
      e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) dragMoved = true;
      panX = startPanX + dx;
      panY = startPanY + dy;
      updateTransform(false);
    });

    window.addEventListener('mouseup', () => {
      if (!isDragging) return;
      isDragging = false;
      container.classList.remove('dragging');
    });

    // Touch support (pinch zoom + pan)
    let lastTouchDist = null;

    container.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        isDragging = true;
        dragMoved = false;
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        startPanX = panX;
        startPanY = panY;
      } else if (e.touches.length === 2) {
        isDragging = false;
        lastTouchDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
      }
      e.preventDefault();
    }, { passive: false });

    container.addEventListener('touchmove', (e) => {
      if (e.touches.length === 1 && isDragging) {
        panX = startPanX + (e.touches[0].clientX - startX);
        panY = startPanY + (e.touches[0].clientY - startY);
        dragMoved = true;
        updateTransform(false);
      } else if (e.touches.length === 2 && lastTouchDist) {
        const dist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
        const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
        zoomTo(scale * (dist / lastTouchDist), cx, cy);
        lastTouchDist = dist;
      }
      e.preventDefault();
    }, { passive: false });

    container.addEventListener('touchend', () => {
      isDragging = false;
      lastTouchDist = null;
    });

    // Double-click to toggle zoom
    container.addEventListener('dblclick', (e) => {
      if (scale > 1.1) resetView();
      else zoomTo(2.5, e.clientX, e.clientY);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (!overlay.classList.contains('active')) return;
      if (e.key === 'Escape') closeViewer();
      if (e.key === '+' || e.key === '=') zoomTo(scale + ZOOM_STEP);
      if (e.key === '-') zoomTo(scale - ZOOM_STEP);
      if (e.key === '0') resetView();
    });

    // Close when clicking background (not dragging, not zoomed)
    container.addEventListener('click', (e) => {
      if (e.target === container && !dragMoved && scale <= 1) closeViewer();
    });
  }

  /* ---------- Scroll-to-top ---------- */
  const scrollBtn = document.querySelector('.scroll-top');
  if (scrollBtn) {
    window.addEventListener('scroll', () => {
      scrollBtn.classList.toggle('visible', window.scrollY > 400);
    });
    scrollBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  /* ---------- Iframe Expand/Collapse ---------- */
  function toggleIframeFullscreen(wrapper, btn) {
    const supportsNativeFullscreen = !!(
      wrapper.requestFullscreen ||
      wrapper.webkitRequestFullscreen ||
      wrapper.msRequestFullscreen
    );

    const updateButtonState = (expanded) => {
      btn.textContent = expanded ? '✕' : '⛶';
      btn.title = expanded ? 'Fechar' : 'Expandir';
      document.body.style.overflow = expanded ? 'hidden' : '';
    };

    if (supportsNativeFullscreen) {
      const isInNativeFullscreen = document.fullscreenElement === wrapper;
      if (isInNativeFullscreen) {
        document.exitFullscreen?.();
        return;
      }

      wrapper.requestFullscreen?.().catch(() => {
        const expanded = wrapper.classList.toggle('iframe-fullscreen');
        updateButtonState(expanded);
      });
      return;
    }

    const expanded = wrapper.classList.toggle('iframe-fullscreen');
    updateButtonState(expanded);
  }

  function bindIframeExpandButtons(scope = document) {
    scope.querySelectorAll('.iframe-expand').forEach(btn => {
      if (btn.dataset.expandBound) return;
      btn.dataset.expandBound = '1';
      btn.addEventListener('click', () => {
        const wrapper = btn.closest('.iframe-wrapper');
        if (!wrapper) return;
        if (btn.dataset.busy === '1') return;
        btn.dataset.busy = '1';
        toggleIframeFullscreen(wrapper, btn);
        setTimeout(() => {
          btn.dataset.busy = '0';
        }, 220);
      });
    });
  }

  bindIframeExpandButtons();

  // ESC to close expanded iframe
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const expanded = document.querySelector('.iframe-wrapper.iframe-fullscreen');
      if (expanded) {
        expanded.classList.remove('iframe-fullscreen');
        const btn = expanded.querySelector('.iframe-expand');
        if (btn) { btn.textContent = '⛶'; btn.title = 'Expandir'; }
        document.body.style.overflow = '';
      }
    }
  });

  document.addEventListener('fullscreenchange', () => {
    document.querySelectorAll('.iframe-expand').forEach(btn => {
      const wrapper = btn.closest('.iframe-wrapper');
      if (!wrapper) return;
      const expanded = document.fullscreenElement === wrapper || wrapper.classList.contains('iframe-fullscreen');
      btn.textContent = expanded ? '✕' : '⛶';
      btn.title = expanded ? 'Fechar' : 'Expandir';
    });

    if (!document.fullscreenElement) {
      document.body.style.overflow = '';
    }
  });

  /* ---------- State Selector (estadual page) ---------- */
  const ofertaStateSelect = document.getElementById('oferta-state-select');
  const ofertaMapDisplay = document.getElementById('oferta-map-display');
  const ofertaStateButtons = document.querySelectorAll('.oferta-state-btn');

  function showOfertaState(uf) {
    if (!ofertaMapDisplay) return;
    const mapPath = `Outputs%26Codigo/PARTE1/mapas_Equipes_Atencao_Domiciliar_por_estado/mapa_Equipes_Atencao_Domiciliar_${uf}.html`;

    ofertaMapDisplay.innerHTML = `
      <div class="card card-full">
        <div class="iframe-wrapper" style="padding-bottom:65%;">
          <iframe src="${mapPath}" title="Mapa de Equipes AD em ${uf}" loading="lazy"></iframe>
          <button class="iframe-expand" title="Expandir">⛶</button>
        </div>
        <div class="card-body">
          <h3>${uf}: Distribuição Espacial das Equipes</h3>
          <p>Mapa interativo com clusters automáticos e classificação por composição (EMAD/EMAP) dos estabelecimentos.</p>
        </div>
      </div>
    `;

    bindIframeExpandButtons(ofertaMapDisplay);
    ofertaStateButtons.forEach(b => b.classList.toggle('active', b.dataset.uf === uf));
    if (ofertaStateSelect) ofertaStateSelect.value = uf;
  }

  if (ofertaStateSelect) {
    ofertaStateSelect.addEventListener('change', () => showOfertaState(ofertaStateSelect.value));
  }

  ofertaStateButtons.forEach(btn => {
    btn.addEventListener('click', () => showOfertaState(btn.dataset.uf));
  });

  if (ofertaMapDisplay && (ofertaStateSelect || ofertaStateButtons.length)) {
    showOfertaState('SP');
  }

  const stateSelect = document.getElementById('state-select');
  const stateDisplay = document.getElementById('state-display');
  const stateButtons = document.querySelectorAll('.state-btn');

  function showState(uf) {
    if (!stateDisplay) return;
    const imgPath = `Outputs%26Codigo/PARTE4/visualizacoes/estados/${uf}/${uf}_equipes_conformidade.png`;

    stateDisplay.innerHTML = `
      <div class="card card-full">
        <img src="${imgPath}" alt="Conformidade ${uf}" class="zoomable" />
        <div class="card-body">
          <h3>${uf}: Conformidade das Equipes</h3>
          <p>Distribuição de equipes conformes e não-conformes no estado, por tipo de equipe (Portaria 3.005/2024).</p>
        </div>
      </div>
    `;
    if (window.__bindLightbox) window.__bindLightbox();

    stateButtons.forEach(b => b.classList.toggle('active', b.dataset.uf === uf));
    if (stateSelect) stateSelect.value = uf;
  }

  if (stateSelect) {
    stateSelect.addEventListener('change', () => showState(stateSelect.value));
  }

  stateButtons.forEach(btn => {
    btn.addEventListener('click', () => showState(btn.dataset.uf));
  });

  if (stateDisplay && (stateSelect || stateButtons.length)) {
    showState('SP');
  }
});
