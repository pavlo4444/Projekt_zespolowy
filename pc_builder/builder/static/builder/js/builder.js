(function () {
  function getCookie(name) {
    if (!document.cookie) return '';
    const parts = document.cookie.split(';');
    for (let i = 0; i < parts.length; i += 1) {
      const part = parts[i].trim();
      if (part.startsWith(name + '=')) {
        return decodeURIComponent(part.substring(name.length + 1));
      }
    }
    return '';
  }

  const csrftoken =
    (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || getCookie('csrftoken');

  function api(path, options = {}) {
    const headers = Object.assign(
      { 'X-CSRFToken': csrftoken || '', Accept: 'application/json' },
      options.headers || {}
    );
    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }
    return fetch(path, Object.assign({ credentials: 'same-origin' }, options, { headers }));
  }

  const modal = document.getElementById('picker-modal');
  const modalList = document.getElementById('modal-list');
  const modalTitle = document.getElementById('modal-title');
  const modalQ = document.getElementById('modal-q');
  let activeSlug = null;
  let debounceTimer = null;

  function money(s) {
    return `${s} zł`;
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function setStatusBadge(tile, status) {
    const old = tile.querySelector('.status-badge');
    if (old) old.remove();
    if (status === 'ok') {
      const badge = document.createElement('span');
      badge.className = 'status-badge status-badge--ok';
      badge.setAttribute('aria-hidden', 'true');
      tile.appendChild(badge);
      return;
    }
    if (status === 'error') {
      const badge = document.createElement('button');
      badge.type = 'button';
      badge.className = 'status-badge status-badge--error js-error-badge';
      badge.setAttribute('aria-label', 'Pokaż błędy zgodności');
      badge.setAttribute('aria-expanded', 'false');
      tile.appendChild(badge);
    }
  }

  function renderIconTiles(data) {
    const statuses = data.category_status || {};
    const byCategory = data.category_issues || {};
    const hasPsuError = (byCategory.psu || []).length > 0;
    const hasAnyPart = Object.values(data.parts || {}).some((p) => p);
    const energyLine = document.getElementById('energy-line');

    document.querySelectorAll('.icon-tile-wrap[data-slug]').forEach((wrap) => {
      const slug = wrap.dataset.slug;
      const tile = wrap.querySelector('.icon-tile');
      const tooltip = wrap.querySelector('.icon-tooltip');
      if (!tile) return;

      const status = statuses[slug] || 'empty';
      const issues = byCategory[slug] || [];

      tile.classList.remove('status-empty', 'status-ok', 'status-error');
      tile.classList.add(`status-${status}`);
      tile.dataset.status = status;
      setStatusBadge(tile, status);

      if (tooltip) {
        tooltip.classList.remove('is-open');
        if (status === 'error' && issues.length) {
          tooltip.hidden = false;
          tooltip.innerHTML =
            '<strong>Błędy zgodności</strong>' +
            issues.map((m) => `<p>${escapeHtml(m)}</p>`).join('');
        } else {
          tooltip.hidden = true;
          tooltip.innerHTML = '';
        }
      }
    });

    if (energyLine) {
      energyLine.classList.remove('energy-ok', 'energy-error');
      if (hasPsuError) {
        energyLine.classList.add('energy-error');
      } else if (hasAnyPart && data.total_power_w) {
        energyLine.classList.add('energy-ok');
      }
    }
  }

  function renderSummary(data) {
    document.getElementById('hdr-power').textContent = data.total_power_w;
    document.getElementById('hdr-price').textContent = data.total_price_pln;
    document.getElementById('sum-price').textContent = data.total_price_pln;

    renderIconTiles(data);

    Object.keys(data.parts || {}).forEach((slug) => {
      const part = data.parts[slug];
      const pick = document.getElementById(`pick-${slug}`);
      const meta = document.getElementById(`meta-${slug}`);
      const removeBtn = document.querySelector(`.js-remove[data-slug="${slug}"]`);
      if (!pick || !meta) return;
      if (!part) {
        pick.textContent = 'Nie wybrano';
        pick.classList.add('muted');
        meta.textContent = '';
        if (removeBtn) removeBtn.hidden = true;
        return;
      }
      pick.textContent = part.name;
      pick.classList.remove('muted');
      meta.innerHTML = `${money(part.price_pln)} · ${part.power_watts || 0} W`;
      if (removeBtn) removeBtn.hidden = false;
    });
  }

  async function refresh() {
    const res = await api('/api/zestaw/');
    const data = await res.json();
    renderSummary(data);
  }

  function openModal(slug, titlePl) {
    activeSlug = slug;
    modalTitle.textContent = 'Wybierz: ' + (titlePl || slug);
    modalQ.value = '';
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
    loadCategory(slug, '');
  }

  function closeModal() {
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    activeSlug = null;
    modalList.innerHTML = '';
  }

  async function loadCategory(slug, q) {
    const url = new URL(window.location.origin + `/api/kategoria/${slug}/`);
    if (q) url.searchParams.set('q', q);
    const res = await api(url.pathname + url.search);
    const data = await res.json();
    modalList.innerHTML = '';
    if (!data.items.length) {
      modalList.innerHTML = '<p class="muted" style="padding:12px">Brak wyników.</p>';
      return;
    }
    data.items.forEach((item) => {
      const row = document.createElement('button');
      row.type = 'button';
      row.className = 'pick-row' + (item.recommended ? ' pick-row--recommended' : '');
      row.dataset.id = String(item.id);
      const recBadge = item.recommended
        ? '<span class="pick-rec-badge" title="Rekomendowane" aria-label="Rekomendowane">▲</span>'
        : '';
      row.innerHTML = `
        <div>
          <div class="name">${recBadge}${escapeHtml(item.name)}</div>
          <div class="desc">${escapeHtml((item.description || '').slice(0, 140))}</div>
        </div>
        <div class="price">${escapeHtml(item.price_pln)} zł<br><span class="muted small">${item.power_watts || 0} W</span></div>
      `;
      modalList.appendChild(row);
    });
  }

  async function removePart(slug) {
    try {
      const res = await api('/api/ustaw/', {
        method: 'POST',
        body: JSON.stringify({ category: slug, component_id: null }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || 'Błąd usuwania');
        return;
      }
      renderSummary(data);
    } catch (err) {
      alert('Nie udało się usunąć części. Odśwież stronę i spróbuj ponownie.');
      console.error(err);
    }
  }

  async function selectPart(slug, id) {
    try {
      const res = await api('/api/ustaw/', {
        method: 'POST',
        body: JSON.stringify({ category: slug, component_id: id }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || 'Błąd zapisu');
        return;
      }
      renderSummary(data);
      closeModal();
    } catch (err) {
      alert('Nie udało się wybrać części. Odśwież stronę i spróbuj ponownie.');
      console.error(err);
    }
  }

  const iconStrip = document.getElementById('icon-strip');
  if (iconStrip) {
    iconStrip.addEventListener('click', (event) => {
      const badge = event.target.closest('.js-error-badge');
      if (!badge) return;
      event.stopPropagation();
      const wrap = badge.closest('.icon-tile-wrap');
      const tooltip = wrap && wrap.querySelector('.icon-tooltip');
      if (!tooltip) return;
      const open = tooltip.classList.toggle('is-open');
      badge.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  document.addEventListener('click', (event) => {
    if (event.target.closest('.js-error-badge') || event.target.closest('.icon-tooltip')) return;
    document.querySelectorAll('.icon-tooltip.is-open').forEach((tooltip) => {
      tooltip.classList.remove('is-open');
      const badge = tooltip.closest('.icon-tile-wrap')?.querySelector('.js-error-badge');
      if (badge) badge.setAttribute('aria-expanded', 'false');
    });
  });

  document.querySelectorAll('.js-open').forEach((btn) => {
    btn.addEventListener('click', () => openModal(btn.dataset.slug, btn.dataset.name));
  });

  document.querySelectorAll('.js-remove').forEach((btn) => {
    btn.addEventListener('click', (event) => {
      event.stopPropagation();
      removePart(btn.dataset.slug);
    });
  });

  document.querySelectorAll('.js-close').forEach((el) => {
    el.addEventListener('click', closeModal);
  });

  modalList.addEventListener('click', (event) => {
    const row = event.target.closest('.pick-row');
    if (!row || !activeSlug) return;
    const id = parseInt(row.dataset.id, 10);
    if (!Number.isFinite(id)) return;
    selectPart(activeSlug, id);
  });

  modalQ.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      if (activeSlug) loadCategory(activeSlug, modalQ.value.trim());
    }, 200);
  });

  document.getElementById('btn-clear').addEventListener('click', async () => {
    const res = await api('/api/wyczysc/', { method: 'POST', body: '{}' });
    const data = await res.json();
    renderSummary(data);
  });

  document.getElementById('btn-share').addEventListener('click', async () => {
    const url = window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      alert('Skopiowano link do schowka.');
    } catch (e) {
      prompt('Skopiuj link:', url);
    }
  });

  const saveBtn = document.getElementById('btn-save');
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      const title = prompt('Nazwa zestawu:', 'Mój zestaw');
      if (!title) return;
      const res = await api('/api/zapisz/', {
        method: 'POST',
        body: JSON.stringify({ title }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || 'Nie udało się zapisać');
        return;
      }
      alert('Zapisano zestaw: ' + data.title);
    });
  }

  const infoTrigger = document.getElementById('info-accordion-trigger');
  const infoBody = document.getElementById('info-accordion-body');
  const infoLink = document.getElementById('info-link');

  function setInfoOpen(open) {
    if (!infoTrigger || !infoBody) return;
    infoTrigger.setAttribute('aria-expanded', open ? 'true' : 'false');
    infoBody.hidden = !open;
  }

  function toggleInfo() {
    if (!infoTrigger) return;
    const open = infoTrigger.getAttribute('aria-expanded') !== 'true';
    setInfoOpen(open);
  }

  if (infoTrigger) {
    infoTrigger.addEventListener('click', toggleInfo);
  }

  if (infoLink) {
    infoLink.addEventListener('click', (event) => {
      event.preventDefault();
      setInfoOpen(true);
      document.getElementById('info-accordion')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  refresh();
})();
