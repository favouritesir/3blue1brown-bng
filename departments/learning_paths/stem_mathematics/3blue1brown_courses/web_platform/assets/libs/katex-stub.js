/**
 * KaTeX Offline Stub — Lightweight Local Math Renderer
 * =====================================================
 * This stub provides a graceful fallback when the full KaTeX library
 * is not available (e.g. offline mode). It renders math expressions
 * as styled Unicode-approximate text so the page remains readable.
 *
 * To use the real KaTeX, replace this file with the full distribution
 * from https://katex.org/docs/browser.html or include via CDN.
 */

(function (global) {
  'use strict';

  /* ---------- Unicode symbol map for common LaTeX commands ---------- */
  const SYMBOL_MAP = {
    /* Greek lowercase */
    '\\alpha': 'α', '\\beta': 'β', '\\gamma': 'γ', '\\delta': 'δ',
    '\\epsilon': 'ε', '\\zeta': 'ζ', '\\eta': 'η', '\\theta': 'θ',
    '\\iota': 'ι', '\\kappa': 'κ', '\\lambda': 'λ', '\\mu': 'μ',
    '\\nu': 'ν', '\\xi': 'ξ', '\\pi': 'π', '\\rho': 'ρ',
    '\\sigma': 'σ', '\\tau': 'τ', '\\upsilon': 'υ', '\\phi': 'φ',
    '\\chi': 'χ', '\\psi': 'ψ', '\\omega': 'ω',

    /* Greek uppercase */
    '\\Gamma': 'Γ', '\\Delta': 'Δ', '\\Theta': 'Θ', '\\Lambda': 'Λ',
    '\\Xi': 'Ξ', '\\Pi': 'Π', '\\Sigma': 'Σ', '\\Phi': 'Φ',
    '\\Psi': 'Ψ', '\\Omega': 'Ω',

    /* Operators & relations */
    '\\times': '×', '\\div': '÷', '\\pm': '±', '\\mp': '∓',
    '\\cdot': '·', '\\circ': '∘', '\\bullet': '•',
    '\\leq': '≤', '\\geq': '≥', '\\neq': '≠', '\\approx': '≈',
    '\\equiv': '≡', '\\cong': '≅', '\\sim': '∼', '\\simeq': '≃',
    '\\subset': '⊂', '\\supset': '⊃', '\\subseteq': '⊆', '\\supseteq': '⊇',
    '\\in': '∈', '\\notin': '∉', '\\cup': '∪', '\\cap': '∩',
    '\\vee': '∨', '\\wedge': '∧', '\\neg': '¬',
    '\\forall': '∀', '\\exists': '∃', '\\nexists': '∄',
    '\\infty': '∞', '\\partial': '∂', '\\nabla': '∇',
    '\\int': '∫', '\\oint': '∮', '\\sum': '∑', '\\prod': '∏',
    '\\sqrt': '√', '\\angle': '∠', '\\perp': '⊥', '\\parallel': '∥',

    /* Arrows */
    '\\to': '→', '\\rightarrow': '→', '\\leftarrow': '←',
    '\\Rightarrow': '⇒', '\\Leftarrow': '⇐', '\\Leftrightarrow': '⇔',
    '\\leftrightarrow': '↔', '\\mapsto': '↦',
    '\\uparrow': '↑', '\\downarrow': '↓',

    /* Misc */
    '\\cdots': '⋯', '\\ldots': '…', '\\vdots': '⋮', '\\ddots': '⋱',
    '\\langle': '⟨', '\\rangle': '⟩', '\\lfloor': '⌊', '\\rfloor': '⌋',
    '\\lceil': '⌈', '\\rceil': '⌉',
    '\\hat': '^', '\\vec': '⃗', '\\bar': '‾', '\\tilde': '~',
    '\\mathbb{R}': 'ℝ', '\\mathbb{N}': 'ℕ', '\\mathbb{Z}': 'ℤ',
    '\\mathbb{Q}': 'ℚ', '\\mathbb{C}': 'ℂ',
    '\\emptyset': '∅', '\\varnothing': '∅',
    '\\therefore': '∴', '\\because': '∵',
  };

  /* ---------- Superscript / Subscript digit map ---------- */
  const SUPERSCRIPT = { '0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','+':'⁺','-':'⁻','=':'⁼','(':'⁽',')':'⁾','n':'ⁿ','i':'ⁱ' };
  const SUBSCRIPT   = { '0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉','+':'₊','-':'₋','=':'₌','(':'₍',')':'₎','a':'ₐ','e':'ₑ','i':'ᵢ','o':'ₒ','u':'ᵤ','n':'ₙ' };

  function toSuper(str) { return str.split('').map(c => SUPERSCRIPT[c] || c).join(''); }
  function toSub(str)   { return str.split('').map(c => SUBSCRIPT[c]   || c).join(''); }

  /* ---------- Core renderer ---------- */
  function transform(tex) {
    let s = tex;

    // Replace known symbols
    for (const [cmd, sym] of Object.entries(SYMBOL_MAP)) {
      s = s.split(cmd).join(sym);
    }

    // \frac{a}{b}  →  (a)/(b)
    s = s.replace(/\\frac\{([^}]*)\}\{([^}]*)\}/g, '($1)/($2)');

    // ^{...} superscript
    s = s.replace(/\^\{([^}]{1,6})\}/g, (_, g) => toSuper(g));
    s = s.replace(/\^([0-9a-zA-Z])/g,   (_, c) => toSuper(c));

    // _{...} subscript
    s = s.replace(/_\{([^}]{1,6})\}/g, (_, g) => toSub(g));
    s = s.replace(/_([0-9a-zA-Z])/g,   (_, c) => toSub(c));

    // \text{...}
    s = s.replace(/\\text\{([^}]*)\}/g, '$1');

    // \mathbf{...} → bold placeholder
    s = s.replace(/\\mathbf\{([^}]*)\}/g, '$1');

    // \left \right wrappers (strip)
    s = s.replace(/\\left\s*/g, '').replace(/\\right\s*/g, '');

    // Remaining backslash commands (just strip backslash)
    s = s.replace(/\\([a-zA-Z]+)\s*/g, '$1 ');

    // Curly brace cleanup
    s = s.replace(/[{}]/g, '');

    return s.trim();
  }

  /**
   * katex.render(tex, element, options)
   * Renders math into `element`.
   */
  function render(tex, element, opts = {}) {
    const displayMode = opts.displayMode || false;
    const rendered    = transform(tex);

    element.innerHTML = '';
    element.textContent = rendered;
    element.classList.add(displayMode ? 'math-display' : 'math-inline');
    element.setAttribute('title', tex); // Show original LaTeX on hover
    element.setAttribute('data-tex', tex);
  }

  /**
   * katex.renderToString(tex, options)
   * Returns an HTML string.
   */
  function renderToString(tex, opts = {}) {
    const displayMode = opts.displayMode || false;
    const rendered    = transform(tex);
    const cls         = displayMode ? 'math-display' : 'math-inline';
    return `<span class="${cls}" title="${tex.replace(/"/g, '&quot;')}" data-tex="${tex.replace(/"/g, '&quot;')}">${rendered}</span>`;
  }

  /* ---------- Auto-render utility ---------- */
  function renderMathInElement(element, opts = {}) {
    const delimiters = opts.delimiters || [
      { left: '$$', right: '$$', display: true  },
      { left: '\\[', right: '\\]', display: true  },
      { left: '$',  right: '$',  display: false },
      { left: '\\(', right: '\\)', display: false },
    ];

    function processNode(node) {
      if (node.nodeType === Node.TEXT_NODE) {
        let text = node.textContent;
        let changed = false;
        let result  = '';

        // Try each delimiter pair
        for (const { left, right, display } of delimiters) {
          const lIdx = text.indexOf(left);
          if (lIdx === -1) continue;
          const rIdx = text.indexOf(right, lIdx + left.length);
          if (rIdx === -1) continue;

          result  += text.slice(0, lIdx);
          const tex = text.slice(lIdx + left.length, rIdx);
          result  += renderToString(tex, { displayMode: display });
          text     = text.slice(rIdx + right.length);
          changed  = true;
        }

        if (changed) {
          const span = document.createElement('span');
          span.innerHTML = result + escapeHtml(text);
          node.parentNode.replaceChild(span, node);
        }
      } else if (node.nodeType === Node.ELEMENT_NODE &&
                 node.tagName !== 'SCRIPT' && node.tagName !== 'STYLE') {
        Array.from(node.childNodes).forEach(processNode);
      }
    }

    processNode(element);
  }

  function escapeHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  /* ---------- Export as window.katex ---------- */
  const katex = {
    render,
    renderToString,
    renderMathInElement,
    VERSION: '0.1.0-stub',
    _isStub: true,
  };

  // Support both module and global environments
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = katex;
  } else {
    if (!global.katex || global.katex._isStub) {
      global.katex = katex;
      global.renderMathInElement = renderMathInElement;
    }
  }

}(typeof globalThis !== 'undefined' ? globalThis : typeof window !== 'undefined' ? window : this));
