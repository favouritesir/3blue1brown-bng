/**
 * 3Blue1Brown Bengali Platform — Extended Lesson Components (v1.0.0)
 * ====================================================================
 * Canonical component set for lesson shell migration (Lesson 01 baseline).
 *
 * Designed to satisfy the strict 5-point parity mandate:
 *  - Zero text dropping (every DOM block is narratable)
 *  - 1:1 visual sequence (figures carry full spoken captions)
 *  - Exact quizzes with rich feedback
 *  - Universal day/night sync (MutationObserver on <html>)
 *  - Mobile-responsive, non-clipping navigation
 *
 * CRITICAL CONTRACT:
 *  Every content-bearing component renders SYNCHRONOUSLY inside
 *  connectedCallback so that narration_engine.js -> parseContent()
 *  (triggered on DOMContentLoaded) observes the final DOM tree.
 *
 * Components defined here:
 *   <b1b-article>            — Article container
 *   <b1b-narration-banner>   — Teacher-audio top card
 *   <b1b-bookmarks>          — Timestamp jump ribbon
 *   <b1b-bookmark>           — Single bookmark item
 *   <b1b-vector-decomposer>  — Basis-vector component analyzer lab
 *   <b1b-vector-plane>       — Draggable 2D vector SVG plane
 */
(function () {
  'use strict';

  let UID_COUNTER = 0;
  const nextUid = (prefix) => `${prefix}-${(++UID_COUNTER).toString(36)}`;

  /* ------------------------------------------------------------------ */
  /* Shared helpers                                                      */
  /* ------------------------------------------------------------------ */
  function isDarkTheme() {
    return document.documentElement.classList.contains('dark') ||
      document.documentElement.getAttribute('data-theme') === 'dark';
  }

  function renderMath(scope) {
    if (typeof window.renderMathInElement === 'function') {
      window.renderMathInElement(scope, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false },
          { left: '\\[', right: '\\]', display: true }
        ],
        throwOnError: false
      });
    }
  }

  function observeTheme(el, cb) {
    if (!el || !cb) return;
    const obs = new MutationObserver((muts) => {
      for (const m of muts) {
        if (m.attributeName === 'data-theme' || m.attributeName === 'class') {
          cb();
          break;
        }
      }
    });
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'class'] });
  }

  /* ------------------------------------------------------------------ */
  /* <b1b-article>                                                       */
  /* ------------------------------------------------------------------ */
  class B1bArticle extends HTMLElement {
    connectedCallback() {
      if (this.dataset.rendered) return;
      this.dataset.rendered = '1';
      // Move existing children so nested components keep their event listeners.
      const article = document.createElement('article');
      article.className = 'article';
      while (this.firstChild) article.appendChild(this.firstChild);
      this.innerHTML = '';
      this.appendChild(article);
    }
  }

  /* ------------------------------------------------------------------ */
  /* <b1b-narration-banner>                                              */
  /* ------------------------------------------------------------------ */
  class B1bNarrationBanner extends HTMLElement {
    connectedCallback() {
      if (this.dataset.rendered) return;
      this.dataset.rendered = '1';
      const title = this.getAttribute('title') ||
        'শিক্ষক অডিও বিবরণ ও লাইভ কারাওকে সহকারী';
      const desc = this.getAttribute('desc') ||
        'দরদী শিক্ষকের কণ্ঠে প্রতিটি অনুচ্ছেদ, গাণিতিক সূত্র ও চিত্র বিবরণ শুনুন — সাথে রিয়েলটাইম হাইলাইটার ও কন্ট্রোল।';
      const cta = this.getAttribute('cta') || '🎙️ শিক্ষকের কণ্ঠে শুনুন';
      this.innerHTML = `
        <div class="narration-card fade-up">
          <div class="narration-card-left">
            <div class="narration-icon-box">🎙️</div>
            <div>
              <h4>${title} <span class="badge-live">TEACHER VOICE</span></h4>
              <p>${desc}</p>
            </div>
          </div>
          <div class="narration-card-right">
            <button id="btnListenFullArticle" class="btn-read-full" type="button">${cta}</button>
          </div>
        </div>
      `;
    }
  }

  /* ------------------------------------------------------------------ */
  /* <b1b-bookmark> / <b1b-bookmarks>                                    */
  /* ------------------------------------------------------------------ */
  class B1bBookmark extends HTMLElement {
    connectedCallback() {
      if (this.dataset.rendered) return;
      this.dataset.rendered = '1';
      this.style.display = 'none';
    }
  }

  class B1bBookmarks extends HTMLElement {
    connectedCallback() {
      if (this.dataset.rendered) return;
      this.dataset.rendered = '1';
      const label = this.getAttribute('label') ||
        '⏱️ অধ্যায়ের টাইমস্ট্যাম্প বুকমার্ক — যেকোনো অংশে সরাসরি জাম্প করুন:';
      const items = Array.from(this.querySelectorAll('b1b-bookmark')).map((b) => ({
        time: b.getAttribute('time') || '0',
        timeBn: b.getAttribute('time-bn') || '০০:০০',
        text: b.innerHTML.trim()
      }));
      const chips = items.map((it) => `
        <button class="bookmark-chip" type="button" onclick="jumpToLessonTime(${Number(it.time) || 0}, this)">
          <span class="bookmark-time">${it.timeBn}</span>
          <span>${it.text}</span>
        </button>
      `).join('');
      this.innerHTML = `
        <div class="bookmark-ribbon fade-up">
          <div class="bookmark-ribbon-title"><span>${label}</span></div>
          <div class="bookmark-grid">${chips}</div>
        </div>
      `;
    }
  }

  /* ------------------------------------------------------------------ */
  /* <b1b-vector-decomposer>                                             */
  /* ------------------------------------------------------------------ */
  class B1bVectorDecomposer extends HTMLElement {
    connectedCallback() {
      if (this.dataset.rendered) return;
      this.dataset.rendered = '1';
      const uid = nextUid('decomp');
      // Preserve slotted narrative paragraph — it is a real narration cue.
      const introHtml = this.innerHTML.trim();
      this._uid = uid;
      const xId = `${uid}-x`;
      const yId = `${uid}-y`;
      const resId = `${uid}-result`;

      const defaults = (this.getAttribute('initial') || '3,-2').split(',');
      const initX = parseFloat(defaults[0]) || 0;
      const initY = parseFloat(defaults[1]) || 0;

      this.innerHTML = `
        <div class="interactive-calc-box" id="${uid}-box">
          <div class="calc-header">
            <div class="calc-title">
              <span>⚡ ইন্টারেক্টিভ ল্যাব: ভিত্তি ভেক্টর বিশ্লেষণ ও উপাংশ পরীক্ষক</span>
            </div>
            <div class="code-badge">Live Math Engine</div>
          </div>
          ${introHtml ? `<div class="decomp-intro">${introHtml}</div>` : ''}
          <div class="calc-grid">
            <div class="calc-input-group">
              <label for="${xId}">এক্স উপাংশ ($x$ বা $\\hat{i}$ এর স্কেলার গুণক):</label>
              <div class="calc-input-row">
                <input type="number" id="${xId}" class="calc-input" value="${initX}" step="0.5" />
              </div>
            </div>
            <div class="calc-input-group">
              <label for="${yId}">ওয়াই উপাংশ ($y$ বা $\\hat{j}$ এর স্কেলার গুণক):</label>
              <div class="calc-input-row">
                <input type="number" id="${yId}" class="calc-input" value="${initY}" step="0.5" />
              </div>
            </div>
          </div>
          <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px;">
            <span style="font-size:0.85rem; color:var(--text-muted); align-self:center;">প্রিসেট ট্রাই করুন:</span>
            <button type="button" class="viz-tool-btn" data-preset="3,-2">[3, -2]</button>
            <button type="button" class="viz-tool-btn" data-preset="-4,3">[-4, 3]</button>
            <button type="button" class="viz-tool-btn" data-preset="5,0">[5, 0]</button>
            <button type="button" class="viz-tool-btn" data-preset="-2,-3.5">[-2, -3.5]</button>
          </div>
          <div class="calc-result-panel" id="${resId}"></div>
        </div>
      `;

      const xInput = this.querySelector(`#${xId}`);
      const yInput = this.querySelector(`#${yId}`);
      const res = this.querySelector(`#${resId}`);
      const uidRef = uid;

      const update = () => {
        const x = parseFloat(xInput.value) || 0;
        const y = parseFloat(yInput.value) || 0;
        const mag = Math.hypot(x, y);
        const ang = (Math.atan2(y, x) * 180 / Math.PI).toFixed(1);
        const signY = y >= 0 ? '+' : '−';
        const absY = Math.abs(y);
        const ux = mag > 0 ? (x / mag).toFixed(3) : 0;
        const uy = mag > 0 ? (y / mag).toFixed(3) : 0;
        const signUY = uy >= 0 ? '+' : '−';
        const absUY = Math.abs(uy);

        res.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:8px;">
            <div><strong>১. ভিত্তি ভেক্টর প্রকাশ:</strong> $\\vec{v} = ${x}\\hat{i} ${signY} ${absY}\\hat{j} = \\begin{bmatrix} ${x} \\\\ ${y} \\end{bmatrix}$</div>
            <div><strong>২. ভেক্টরের দৈর্ঘ্য (Magnitude):</strong> $\\|\\vec{v}\\| = \\sqrt{(${x})^2 + (${y})^2} = \\sqrt{${(x * x + y * y).toFixed(2)}} \\approx \\mathbf{${mag.toFixed(2)}}$</div>
            <div><strong>৩. দিক কোণ (Direction Angle $\\theta$):</strong> $\\theta = \\arctan2(${y}, ${x}) \\approx \\mathbf{${ang}^\\circ}$</div>
            <div><strong>৪. প্রমিত একক ভেক্টর (Unit Vector $\\hat{u}$):</strong> $\\hat{u} = \\frac{\\vec{v}}{\\|\\vec{v}\\|} \\approx \\mathbf{${ux}\\hat{i} ${signUY} ${absUY}\\hat{j}}$</div>
          </div>
        `;
        renderMath(res);
        this.dispatchEvent(new CustomEvent('b1b-vector-change', {
          detail: { x, y, magnitude: mag, angle: parseFloat(ang) },
          bubbles: true
        }));
      };

      xInput.addEventListener('input', update);
      yInput.addEventListener('input', update);
      this.querySelectorAll('[data-preset]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const [px, py] = btn.dataset.preset.split(',').map(Number);
          xInput.value = px;
          yInput.value = py;
          update();
        });
      });

      this._update = update;
      this._uidRef = uidRef;
      update();
    }
  }

  /* ------------------------------------------------------------------ */
  /* <b1b-vector-plane>                                                  */
  /* ------------------------------------------------------------------ */
  class B1bVectorPlane extends HTMLElement {
    connectedCallback() {
      if (this.dataset.rendered) return;
      this.dataset.rendered = '1';
      const uid = nextUid('vplane');
      this._uid = uid;
      const id = (n) => `${uid}-${n}`;

      const initial = (this.getAttribute('initial') || '3,-2').split(',');
      let vx = parseFloat(initial[0]) || 3;
      let vy = parseFloat(initial[1]) || -2;
      let isDragging = false;
      const SCALE = 40;

      this.innerHTML = `
        <div class="viz-wrapper" id="${id('wrapper')}">
          <div class="viz-header">
            <div class="viz-header-left">
              <span>🔬 ভেক্টর কোঅর্ডিনেট সমতল — ড্র্যাগ করে পরীক্ষা করো!</span>
            </div>
            <div class="viz-header-tools">
              <button type="button" class="viz-tool-btn" id="${id('reset')}">↺ রিসেট</button>
              <button type="button" class="viz-tool-btn" id="${id('fs')}">⛶ ফুলস্ক্রিন</button>
            </div>
          </div>

          <div class="viz-svg-container" id="${id('container')}">
            <svg id="${id('svg')}" class="viz-svg" viewBox="-300 -200 600 400" role="img" aria-label="ইন্টারেক্টিভ ভেক্টর সমতল">
              <defs>
                <marker id="${id('arrow-v')}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#ff4757"/>
                </marker>
                <marker id="${id('arrow-scaled')}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#f7c948"/>
                </marker>
                <marker id="${id('arrow-i')}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#3a86ff"/>
                </marker>
                <marker id="${id('arrow-j')}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#00b4d8"/>
                </marker>
              </defs>
              <g id="${id('grid')}"></g>
              <g id="${id('axes')}"></g>
              <g id="${id('basis')}">
                <line x1="0" y1="0" x2="40" y2="0" stroke="#3a86ff" stroke-width="2.5" marker-end="url(#${id('arrow-i')})"/>
                <text x="46" y="-6" fill="#3a86ff" font-family="'JetBrains Mono', monospace" font-size="13" font-weight="bold">î</text>
                <line x1="0" y1="0" x2="0" y2="-40" stroke="#00b4d8" stroke-width="2.5" marker-end="url(#${id('arrow-j')})"/>
                <text x="6" y="-46" fill="#00b4d8" font-family="'JetBrains Mono', monospace" font-size="13" font-weight="bold">ĵ</text>
              </g>
              <line id="${id('scaledLine')}" x1="0" y1="0" x2="120" y2="80" stroke="#f7c948" stroke-width="3" stroke-dasharray="6,4" marker-end="url(#${id('arrow-scaled')})"/>
              <text id="${id('scaledText')}" x="125" y="95" fill="#f7c948" font-family="'JetBrains Mono', monospace" font-size="12" font-weight="bold"></text>
              <line id="${id('vectorLine')}" x1="0" y1="0" x2="120" y2="80" stroke="#ff4757" stroke-width="3.5" marker-end="url(#${id('arrow-v')})"/>
              <text id="${id('vectorText')}" x="125" y="75" fill="#ff4757" font-family="'JetBrains Mono', monospace" font-size="13" font-weight="bold">v = [3, -2]</text>
              <circle id="${id('handle')}" class="svg-handle" cx="120" cy="80" r="8" fill="#ff4757" stroke="#ffffff" stroke-width="2.5" tabindex="0" aria-label="ভেক্টরের শীর্ষবিন্দু টেনে পরিবর্তন করুন"/>
            </svg>
          </div>

          <div class="viz-controls">
            <div class="viz-slider-row">
              <label for="${id('slider')}">স্কেলার গুণক ($c$):</label>
              <input type="range" id="${id('slider')}" min="-3" max="3" step="0.05" value="1"/>
              <span class="viz-val" id="${id('scalarVal')}">১.০০</span>
            </div>
          </div>
          <div class="viz-info" id="${id('info')}"></div>
        </div>
      `;

      const el = (n) => this.querySelector(`#${id(n)}`);
      const svg = el('svg');
      const gridLayer = el('grid');
      const axesLayer = el('axes');
      const vectorLine = el('vectorLine');
      const vectorText = el('vectorText');
      const handle = el('handle');
      const scaledLine = el('scaledLine');
      const scaledText = el('scaledText');
      const slider = el('slider');
      const valEl = el('scalarVal');
      const infoEl = el('info');

      const buildGrid = () => {
        let gridHtml = '';
        const dark = isDarkTheme();
        const gridColor = dark ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.18)';
        const axisColor = dark ? 'rgba(255,255,255,0.65)' : 'rgba(0,0,0,0.65)';
        const textColor = dark ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.7)';

        for (let x = -280; x <= 280; x += SCALE) {
          gridHtml += `<line x1="${x}" y1="-190" x2="${x}" y2="190" stroke="${gridColor}" stroke-width="1.2"/>`;
        }
        for (let y = -160; y <= 160; y += SCALE) {
          gridHtml += `<line x1="-290" y1="${y}" x2="290" y2="${y}" stroke="${gridColor}" stroke-width="1.2"/>`;
        }
        gridLayer.innerHTML = gridHtml;

        let axesHtml = `
          <line x1="-290" y1="0" x2="290" y2="0" stroke="${axisColor}" stroke-width="2"/>
          <line x1="0" y1="-190" x2="0" y2="190" stroke="${axisColor}" stroke-width="2"/>
          <text x="275" y="16" fill="${axisColor}" font-family="'JetBrains Mono', monospace" font-size="12" font-weight="bold">x</text>
          <text x="8" y="-175" fill="${axisColor}" font-family="'JetBrains Mono', monospace" font-size="12" font-weight="bold">y</text>
        `;
        for (let i = -6; i <= 6; i++) {
          if (i === 0) continue;
          axesHtml += `<text x="${i * SCALE}" y="15" fill="${textColor}" font-family="'JetBrains Mono', monospace" font-size="10" text-anchor="middle">${i}</text>`;
        }
        for (let j = -4; j <= 4; j++) {
          if (j === 0) continue;
          axesHtml += `<text x="-8" y="${-j * SCALE + 4}" fill="${textColor}" font-family="'JetBrains Mono', monospace" font-size="10" text-anchor="end">${j}</text>`;
        }
        axesLayer.innerHTML = axesHtml;
      };

      const update = () => {
        const sx = vx * SCALE;
        const sy = -vy * SCALE;
        const c = parseFloat(slider.value) || 1;
        const cx = c * vx;
        const cy = c * vy;

        vectorLine.setAttribute('x2', sx);
        vectorLine.setAttribute('y2', sy);
        handle.setAttribute('cx', sx);
        handle.setAttribute('cy', sy);
        vectorText.setAttribute('x', sx + 10);
        vectorText.setAttribute('y', sy - 6);
        vectorText.textContent = `v = [${vx.toFixed(1)}, ${vy.toFixed(1)}]`;

        if (Math.abs(c - 1) > 0.05) {
          scaledLine.style.display = 'block';
          scaledText.style.display = 'block';
          scaledLine.setAttribute('x2', cx * SCALE);
          scaledLine.setAttribute('y2', -cy * SCALE);
          scaledText.setAttribute('x', cx * SCALE + 10);
          scaledText.setAttribute('y', -cy * SCALE + 14);
          scaledText.textContent = `c·v = [${cx.toFixed(1)}, ${cy.toFixed(1)}]`;
        } else {
          scaledLine.style.display = 'none';
          scaledText.style.display = 'none';
        }

        valEl.textContent = c.toFixed(2);
        infoEl.textContent = `ভেক্টর v: [${vx.toFixed(2)}, ${vy.toFixed(2)}] | দৈর্ঘ্য ||v||: ${Math.hypot(vx, vy).toFixed(2)} | কোণ: ${Math.round(Math.atan2(vy, vx) * 180 / Math.PI)}° | c·v: [${cx.toFixed(2)}, ${cy.toFixed(2)}]`;
        this.dispatchEvent(new CustomEvent('b1b-vector-change', {
          detail: { x: vx, y: vy, scalar: c, scaledX: cx, scaledY: cy },
          bubbles: true
        }));
      };

      const getCoords = (evt) => {
        const pt = svg.createSVGPoint();
        pt.x = evt.clientX || (evt.touches && evt.touches[0].clientX);
        pt.y = evt.clientY || (evt.touches && evt.touches[0].clientY);
        const p = pt.matrixTransform(svg.getScreenCTM().inverse());
        return [p.x / SCALE, -p.y / SCALE];
      };

      const drag = (evt) => {
        if (!isDragging) return;
        const [rawX, rawY] = getCoords(evt);
        vx = Math.min(Math.max(Math.round(rawX * 4) / 4, -6.5), 6.5);
        vy = Math.min(Math.max(Math.round(rawY * 4) / 4, -4.5), 4.5);
        update();
      };

      const startDrag = (evt) => {
        evt.preventDefault();
        isDragging = true;
        handle.classList.add('dragging');
      };

      const endDrag = () => {
        if (!isDragging) return;
        isDragging = false;
        handle.classList.remove('dragging');
      };

      handle.addEventListener('mousedown', startDrag);
      handle.addEventListener('touchstart', startDrag, { passive: false });
      window.addEventListener('mousemove', drag);
      window.addEventListener('touchmove', drag, { passive: false });
      window.addEventListener('mouseup', endDrag);
      window.addEventListener('touchend', endDrag);

      slider.addEventListener('input', update);
      el('reset').addEventListener('click', () => {
        vx = 3; vy = -2; slider.value = 1; update();
      });
      // When wrapped in <b1b-fullscreen>, the generic wrapper owns fullscreen.
      if (this.closest('b1b-fullscreen')) el('fs').style.display = 'none';
      el('fs').addEventListener('click', () => {
        if (typeof window.toggleVizFullscreen === 'function') {
          window.toggleVizFullscreen(id('wrapper'));
        } else {
          el('wrapper').classList.toggle('fullscreen');
        }
      });

      buildGrid();
      update();
      observeTheme(this, () => { buildGrid(); update(); });
    }
  }

  /* ------------------------------------------------------------------ */
  /* <b1b-fullscreen> — reusable fullscreen wrapper for ANY tool        */
  /* ------------------------------------------------------------------ */
  class B1bFullscreen extends HTMLElement {
    connectedCallback() {
      if (this.dataset.rendered) return;
      this.dataset.rendered = '1';

      if (!document.getElementById('b1b-fullscreen-styles')) {
        const st = document.createElement('style');
        st.id = 'b1b-fullscreen-styles';
        st.textContent = `
          b1b-fullscreen { display: block; }
          .b1b-fs-host { position: relative; }
          .b1b-fs-btn {
            position: absolute; top: 10px; right: 12px; z-index: 3;
            background: rgba(116,192,227,.18); color: var(--theme, #74C0E3);
            border: 1px solid rgba(116,192,227,.4); border-radius: 8px;
            padding: 5px 10px; font-size: .8rem; font-weight: 700;
            cursor: pointer; font-family: inherit;
          }
          .b1b-fs-btn:hover { background: rgba(116,192,227,.3); }
          .b1b-fs-host.b1b-fs-active {
            position: fixed; inset: 0; z-index: 100000;
            margin: 0; padding: 16px; border-radius: 0;
            background: var(--bg, #0f1117); overflow: auto;
            display: flex; flex-direction: column;
          }
          .b1b-fs-host.b1b-fs-active > *:not(.b1b-fs-btn) { flex: 1 1 auto; }
        `;
        document.head.appendChild(st);
      }

      const host = document.createElement('div');
      host.className = 'b1b-fs-host';
      while (this.firstChild) host.appendChild(this.firstChild);

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'b1b-fs-btn';
      btn.textContent = this.getAttribute('label') || '⛶ ফুলস্ক্রিন';
      btn.setAttribute('aria-label', 'ফুলস্ক্রিন টগল');

      host.appendChild(btn);
      this.innerHTML = '';
      this.appendChild(host);

      const toggle = () => {
        const active = host.classList.toggle('b1b-fs-active');
        btn.textContent = active ? '✕ বন্ধ করো' : (this.getAttribute('label') || '⛶ ফুলস্ক্রিন');
        document.body.style.overflow = active ? 'hidden' : '';
        if (active && !document.fullscreenElement) {
          const target = host.firstElementChild;
          if (target && target.requestFullscreen) {
            target.requestFullscreen().catch(() => {});
          }
        }
        window.dispatchEvent(new Event('resize'));
        this.dispatchEvent(new CustomEvent('b1b-fullscreen-change', {
          detail: { active }, bubbles: true
        }));
      };

      btn.addEventListener('click', (e) => { e.stopPropagation(); toggle(); });
      this._toggleFullscreen = toggle;

      this._onKey = (e) => {
        if (e.key === 'Escape' && host.classList.contains('b1b-fs-active')) toggle();
      };
      window.addEventListener('keydown', this._onKey);
    }

    disconnectedCallback() {
      if (this._onKey) window.removeEventListener('keydown', this._onKey);
      document.body.style.overflow = '';
    }
  }

  /* ------------------------------------------------------------------ */
  /* Registration                                                        */
  /* ------------------------------------------------------------------ */
  const registry = [
    ['b1b-article', B1bArticle],
    ['b1b-narration-banner', B1bNarrationBanner],
    ['b1b-bookmark', B1bBookmark],
    ['b1b-bookmarks', B1bBookmarks],
    ['b1b-vector-decomposer', B1bVectorDecomposer],
    ['b1b-vector-plane', B1bVectorPlane],
    ['b1b-fullscreen', B1bFullscreen]
  ];
  registry.forEach(([name, cls]) => {
    if (!customElements.get(name)) customElements.define(name, cls);
  });

  window.B1bExtendedComponents = {
    B1bArticle,
    B1bNarrationBanner,
    B1bBookmark,
    B1bBookmarks,
    B1bVectorDecomposer,
    B1bVectorPlane,
    B1bFullscreen
  };
})();
