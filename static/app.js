(() => {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem('hotel-theme');
  if (savedTheme === 'dark') root.classList.add('dark-mode');

  // Cinematic Loader Dismissal
  const loader = document.getElementById('cinematic-loader');
  if (loader) {
    const dismissLoader = () => {
      loader.classList.add('fade-out');
    };
    if (document.readyState === 'complete') {
      setTimeout(dismissLoader, 900);
    } else {
      window.addEventListener('load', () => setTimeout(dismissLoader, 900));
    }
    // Safety timeout fallback
    setTimeout(dismissLoader, 3000);
  }

  const toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      toggle.classList.remove('is-changing');
      void toggle.offsetWidth;
      toggle.classList.add('is-changing');
      root.classList.toggle('dark-mode');
      localStorage.setItem('hotel-theme', root.classList.contains('dark-mode') ? 'dark' : 'light');
      window.setTimeout(() => toggle.classList.remove('is-changing'), 850);
    });
  }

  const clock = document.getElementById('live-time');

  // Keep native calendar selection while allowing friendly keyboard date entry.
  document.querySelectorAll('input[type="date"]').forEach((dateInput) => {
    const picker = dateInput.cloneNode(true);
    const wrapper = document.createElement('div');
    const button = document.createElement('button');
    picker.removeAttribute('name');
    picker.removeAttribute('id');
    picker.className = 'native-date-picker';
    picker.tabIndex = -1;
    picker.setAttribute('aria-hidden', 'true');
    dateInput.type = 'text';
    dateInput.inputMode = 'numeric';
    dateInput.autocomplete = 'off';
    dateInput.placeholder = 'DD-MM-YYYY';
    wrapper.className = 'date-input';
    button.type = 'button';
    button.className = 'date-picker-button';
    button.innerHTML = '<svg class="calendar-icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4.5" width="18" height="17" rx="3"></rect><path d="M7 2.5v4M17 2.5v4M3 9.5h18M8 13h.01M12 13h.01M16 13h.01M8 17h.01M12 17h.01M16 17h.01"></path></svg>';
    button.title = 'Open calendar';
    button.setAttribute('aria-label', 'Open calendar');
    dateInput.parentNode.insertBefore(wrapper, dateInput);
    wrapper.append(dateInput, button, picker);
    const normalize = () => {
      let value = dateInput.value.trim().replace(/[/.]/g, '-');
      const ddmmyyyy = value.match(/^(\d{1,2})-(\d{1,2})-(\d{4})$/);
      if (ddmmyyyy) value = `${ddmmyyyy[3]}-${ddmmyyyy[2].padStart(2, '0')}-${ddmmyyyy[1].padStart(2, '0')}`;
      const yyyymmdd = value.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
      if (yyyymmdd) value = `${yyyymmdd[1]}-${yyyymmdd[2].padStart(2, '0')}-${yyyymmdd[3].padStart(2, '0')}`;
      if (/^\d{4}-\d{2}-\d{2}$/.test(value)) dateInput.value = value;
      picker.value = dateInput.value;
    };
    button.addEventListener('click', () => {
      normalize();
      button.classList.remove('is-opening');
      void button.offsetWidth;
      button.classList.add('is-opening');
      if (picker.showPicker) picker.showPicker(); else picker.click();
    });
    picker.addEventListener('change', () => { dateInput.value = picker.value; dateInput.dispatchEvent(new Event('change', { bubbles: true })); });
    dateInput.addEventListener('blur', normalize);
    dateInput.form?.addEventListener('submit', normalize);
  });

  const roomFilters = document.querySelector('.room-filters');
  const roomRows = [...document.querySelectorAll('.room-row')];
  if (roomFilters && roomRows.length) {
    const search = document.getElementById('room-search');
    const typeButton = roomFilters.querySelectorAll('.room-filter')[1];
    const sortButton = roomFilters.querySelectorAll('.room-filter')[0];
    const roomTypes = [...new Set(roomRows.map((row) => row.dataset.roomType))];
    let selectedType = 'all';
    let selectedSort = 'popular';
    const makeMenu = (button, options, onSelect) => {
      const wrapper = document.createElement('div');
      const menu = document.createElement('div');
      wrapper.className = 'room-filter-menu-wrap';
      menu.className = 'room-filter-menu';
      button.firstChild.textContent = `${options[0].label} `;
      button.parentNode.insertBefore(wrapper, button);
      wrapper.append(button, menu);
      options.forEach((option, index) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = `room-filter-option${index === 0 ? ' selected' : ''}`;
        item.textContent = option.label;
        item.addEventListener('click', () => {
          wrapper.querySelectorAll('.room-filter-option').forEach((entry) => entry.classList.remove('selected'));
          item.classList.add('selected');
          button.firstChild.textContent = `${option.label} `;
          wrapper.classList.remove('open');
          onSelect(option.value);
        });
        menu.appendChild(item);
      });
      button.addEventListener('click', (event) => {
        event.stopPropagation();
        document.querySelectorAll('.room-filter-menu-wrap.open').forEach((openMenu) => openMenu !== wrapper && openMenu.classList.remove('open'));
        wrapper.classList.toggle('open');
      });
    };
    const applyRoomFilters = () => {
      const query = (search?.value || '').toLowerCase().trim();
      const visibleRows = roomRows.filter((row) => (selectedType === 'all' || row.dataset.roomType === selectedType) && (!query || row.dataset.roomName.includes(query) || row.dataset.roomType.includes(query)));
      const results = document.getElementById('room-results');
      const orderedRows = [...roomRows].sort((a, b) => {
        if (selectedSort === 'name') return a.dataset.roomType.localeCompare(b.dataset.roomType);
        if (selectedSort === 'price') return Number(a.dataset.roomRate || 0) - Number(b.dataset.roomRate || 0);
        if (selectedSort === 'availability') return Number(b.dataset.available || 0) - Number(a.dataset.available || 0);
        return roomRows.indexOf(a) - roomRows.indexOf(b);
      });
      orderedRows.forEach((row) => results.appendChild(row.closest('.room-row-link') || row));
      roomRows.forEach((row) => { row.hidden = !visibleRows.includes(row); });
    };
    makeMenu(sortButton, [{ value: 'popular', label: 'Popular' }, { value: 'availability', label: 'Most available' }, { value: 'price', label: 'Price: low to high' }, { value: 'name', label: 'Name: A–Z' }], (value) => { selectedSort = value; applyRoomFilters(); });
    makeMenu(typeButton, [{ value: 'all', label: 'All room types' }, ...roomTypes.map((type) => ({ value: type, label: type.replace(/\b\w/g, (letter) => letter.toUpperCase()) }))], (value) => { selectedType = value; applyRoomFilters(); });
    roomRows.forEach((row) => {
      row.dataset.roomRate = (row.querySelector('.room-rate')?.textContent || '').replace(/[^0-9.]/g, '');
      row.dataset.available = (row.querySelector('.badge')?.textContent || '').replace(/[^0-9]/g, '') || '0';
    });
    search?.addEventListener('input', applyRoomFilters);
    document.addEventListener('click', () => document.querySelectorAll('.room-filter-menu-wrap.open').forEach((menu) => menu.classList.remove('open')));
    applyRoomFilters();
  }

  const userChip = document.querySelector('.user-chip');
  if (userChip) {
    userChip.setAttribute('role', 'button');
    userChip.setAttribute('tabindex', '0');
    userChip.setAttribute('aria-label', 'Sign out');
    userChip.title = 'Sign out';
    const signOut = () => { window.location.href = '/logout'; };
    userChip.addEventListener('click', signOut);
    userChip.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); signOut(); }
    });
  }

  const updateClock = () => {
    if (clock) clock.textContent = new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date());
  };
  updateClock();
  window.setInterval(updateClock, 30000);

  document.querySelectorAll('.panel, .stat-card, .room-card, .quick-link, .record-metrics > div').forEach((element, index) => {
    element.style.setProperty('--delay', `${Math.min(index * 45, 260)}ms`);
    element.classList.add('reveal-item');

    // Add interactive gold spotlight glare tracking for luxury aesthetic
    if (element.classList.contains('panel') || element.classList.contains('stat-card') || element.classList.contains('room-card') || element.closest('.record-metrics')) {
      element.classList.add('gold-glare');
      element.addEventListener('pointermove', (e) => {
        const rect = element.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        element.style.setProperty('--mouse-x', `${x}px`);
        element.style.setProperty('--mouse-y', `${y}px`);
      });
      if (element.closest('.record-metrics')) {
        element.addEventListener('pointerleave', () => {
          element.style.setProperty('--mouse-x', '-999px');
          element.style.setProperty('--mouse-y', '-999px');
        });
      }
    }
  });

  document.querySelectorAll('select').forEach((select) => {
    select.addEventListener('change', () => select.classList.add('has-value'));
  });

  const landingObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        landingObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.14 });
  document.querySelectorAll('.landing-reveal').forEach((element) => landingObserver.observe(element));

  const hero = document.querySelector('.landing-hero');
  if (hero && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    hero.addEventListener('pointermove', (event) => {
      const x = (event.clientX / window.innerWidth - 0.5) * 2;
      const y = (event.clientY / window.innerHeight - 0.5) * 2;
      hero.style.setProperty('--mouse-x', `${x * 9}px`);
      hero.style.setProperty('--mouse-y', `${y * 7}px`);
    });
    hero.addEventListener('pointerleave', () => {
      hero.style.setProperty('--mouse-x', '0px');
      hero.style.setProperty('--mouse-y', '0px');
    });
  }

  document.querySelectorAll('.stay-card').forEach((card) => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let frame = 0;
    let pointer = null;
    card.addEventListener('pointermove', (event) => {
      pointer = { x: event.clientX, y: event.clientY };
      if (frame) return;
      frame = requestAnimationFrame(() => {
        const box = card.getBoundingClientRect();
        const rotateY = ((pointer.x - box.left) / box.width - 0.5) * 6;
        const rotateX = ((pointer.y - box.top) / box.height - 0.5) * -5;
        card.style.setProperty('--tilt-x', `${rotateX}deg`);
        card.style.setProperty('--tilt-y', `${rotateY}deg`);
        card.style.setProperty('--spot-x', `${pointer.x - box.left}px`);
        card.style.setProperty('--spot-y', `${pointer.y - box.top}px`);
        frame = 0;
      });
      card.classList.add('is-hovered');
    });
    card.addEventListener('pointerleave', () => {
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
      card.style.setProperty('--tilt-x', '0deg');
      card.style.setProperty('--tilt-y', '0deg');
      card.classList.remove('is-hovered');
    });
  });

  const roomShowcaseTarget = document.querySelector('.landing-cta');
  if (roomShowcaseTarget && !document.querySelector('.rooms-showcase')) {
    const section = document.createElement('section');
    section.className = 'rooms-showcase landing-reveal';
    section.innerHTML = `<div class="rooms-showcase-head"><div><div class="section-label">03 <span></span> STAY YOUR WAY</div><h2>Rooms for every<br><em>kind of stay.</em></h2></div><a class="underlined-link" href="/login">View live availability <span>↗</span></a></div><div class="showcase-grid"><a class="showcase-room" href="/login"><img src="https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=900&q=88" alt="Single room"><div><span>01 — SINGLE</span><h3>Quiet, considered.</h3><small>1 guest · 22 m²</small></div></a><a class="showcase-room" href="/login"><img src="https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=88" alt="Double room"><div><span>02 — DOUBLE</span><h3>Made to share.</h3><small>2 guests · 30 m²</small></div></a><a class="showcase-room" href="/login"><img src="https://images.unsplash.com/photo-1584132967334-10e028bd69f7?auto=format&fit=crop&w=900&q=88" alt="Triple room"><div><span>03 — TRIPLE</span><h3>Space to gather.</h3><small>3 guests · 42 m²</small></div></a><a class="showcase-room" href="/login"><img src="https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=900&q=88" alt="Quad room"><div><span>04 — QUAD</span><h3>Room to linger.</h3><small>4 guests · 58 m²</small></div></a></div>`;
    roomShowcaseTarget.parentNode.insertBefore(section, roomShowcaseTarget);
    landingObserver.observe(section);
  }

  // Password side eye toggle
  const passToggleBtn = document.getElementById('toggle-password');
  const passInput = document.getElementById('password-input');
  if (passToggleBtn && passInput) {
    passToggleBtn.addEventListener('click', () => {
      const isPassword = passInput.type === 'password';
      passInput.type = isPassword ? 'text' : 'password';
      const eyeOpen = passToggleBtn.querySelector('.eye-open');
      const eyeClosed = passToggleBtn.querySelector('.eye-closed');
      if (eyeOpen && eyeClosed) {
        eyeOpen.classList.toggle('hidden', isPassword);
        eyeClosed.classList.toggle('hidden', !isPassword);
      }
    });
  }

  // Instant client-side table search/filtering
  const bindTableFilter = (inputId, tableId) => {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    if (!input || !table) return;
    input.addEventListener('input', () => {
      const term = input.value.toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr');
      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
      });
    });
  };
  bindTableFilter('table-search-guests', 'guests-table');
  bindTableFilter('table-search-staff', 'staff-table');

  // Custom Confirmation Modal
  const modal = document.getElementById('confirm-modal');
  const modalMessage = document.getElementById('modal-message');
  const modalCancel = document.getElementById('modal-cancel');
  const modalConfirm = document.getElementById('modal-confirm');
  let pendingForm = null;

  if (modal && modalCancel && modalConfirm) {
    document.querySelectorAll('form[data-confirm]').forEach((form) => {
      form.addEventListener('submit', (e) => {
        if (form.dataset.confirmed === 'true') return;
        e.preventDefault();
        pendingForm = form;
        if (modalMessage) modalMessage.textContent = form.dataset.confirm || 'Are you sure you want to proceed?';
        modal.classList.remove('hidden');
      });
    });

    modalCancel.addEventListener('click', () => {
      modal.classList.add('hidden');
      pendingForm = null;
    });

    modalConfirm.addEventListener('click', () => {
      if (pendingForm) {
        pendingForm.dataset.confirmed = 'true';
        modal.classList.add('hidden');
        pendingForm.submit();
      }
    });

    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.add('hidden');
        pendingForm = null;
      }
    });
  }

  // ----------------------------------------------------
  // LUXURY TEXT SPLIT & PRINT REVEAL ANIMATIONS
  // ----------------------------------------------------
  const splitTextToWords = (el) => {
    const content = el.innerHTML.trim();
    if (!content) return;
    
    const temp = document.createElement('div');
    temp.innerHTML = content;
    const fragment = document.createDocumentFragment();
    
    const process = (node, parent) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const words = node.textContent.split(/(\s+)/);
        words.forEach(word => {
          if (word.trim() !== '') {
            const wrap = document.createElement('span');
            wrap.className = 'word-wrap';
            const inner = document.createElement('span');
            inner.className = 'word-inner';
            inner.textContent = word;
            wrap.appendChild(inner);
            parent.appendChild(wrap);
          }
        });
      } else {
        const clone = node.cloneNode(false);
        parent.appendChild(clone);
        node.childNodes.forEach(child => process(child, clone));
      }
    };
    
    temp.childNodes.forEach(child => process(child, fragment));
    el.innerHTML = '';
    el.appendChild(fragment);
    
    let delay = 0;
    el.querySelectorAll('.word-inner').forEach((wordEl) => {
      wordEl.style.transitionDelay = `${delay}s`;
      delay += 0.045; // 45ms step for wave print effect
    });
  };

  document.querySelectorAll('.landing-hero h1, .section-heading h2, .serif-display, .landing-cta h2, .contact-intro h2, .landing-lede, .intro-description, .section-heading > p').forEach(el => {
    splitTextToWords(el);
  });
})();
