/* pta-documents HTML deck runtime (E10-S01): keys, touch, #n in the address, steps of builds,
   transitions, progress, chapters, notes panel with timer, screen reader announcement, print.
   Port of the vt-tools-libs deck runtime without scripted scenes. */
(function () {
  'use strict';

  function format(text) {
    var args = Array.prototype.slice.call(arguments, 1);
    return String(text).replace(/\{(\d)\}/g, function (m, i) { return args[+i]; });
  }

  function init() {
    var config = {};
    try { config = JSON.parse(document.body.getAttribute('data-config') || '{}'); } catch (e) { config = {}; }
    var stage = document.getElementById('deck');
    var slides = Array.prototype.slice.call(stage.querySelectorAll('section.slide'));
    var panel = document.getElementById('notes');
    var live = document.getElementById('live');
    var hint = document.getElementById('hint');
    var progress = document.querySelector('#progress span');
    var chapters = Array.prototype.slice.call(document.querySelectorAll('#chapters span'));
    var reduced = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    var cur = 0, step = 0, started = null, leaving = null;
    if (!slides.length) { return; }

    function fit() {
      var height = stage.offsetHeight || 900;
      var margin = 48;
      var s = Math.min((window.innerWidth - margin) / 1600, (window.innerHeight - margin) / height);
      stage.style.setProperty('--s', String(Math.max(s, 0.1)));
    }
    window.addEventListener('resize', fit);
    fit();

    slides.forEach(function (slide) {
      slide.builds = Array.prototype.slice.call(slide.querySelectorAll('[data-build]'));
      slide.steps = +(slide.getAttribute('data-steps') || 0);
    });

    function title(slide) {
      var label = slide.getAttribute('aria-label') || '';
      var colon = label.indexOf(': ');
      return colon >= 0 ? label.slice(colon + 2) : '';
    }

    function render(previous) {
      var slide = slides[cur];
      if (previous !== undefined && previous !== cur) {
        var left = slides[previous];
        var change = (cur > previous ? slide : left).getAttribute('data-transition');
        if (leaving) { leaving.classList.remove('leaving'); }
        if (change && change !== 'none' && !reduced) {
          stage.setAttribute('data-change', change);
          left.classList.add('leaving');
          leaving = left;
          slides.forEach(function (s) { s.style.animation = 'none'; void s.offsetWidth; s.style.animation = ''; });
        } else {
          stage.removeAttribute('data-change');
          leaving = null;
        }
        if (hint) { hint.style.opacity = '0'; }
      }
      slides.forEach(function (s, i) {
        s.classList.toggle('active', i === cur);
        s.setAttribute('aria-hidden', i === cur ? 'false' : 'true');
      });
      slide.builds.forEach(function (b) { b.classList.toggle('on', +b.getAttribute('data-build') <= step); });
      var chapter = slide.hasAttribute('data-chapter') ? +slide.getAttribute('data-chapter') : -1;
      chapters.forEach(function (c) { c.classList.toggle('on', +c.getAttribute('data-c') === chapter); });
      if (progress) {
        var share = slides.length > 1 ? (cur + step / (slide.steps + 1)) / (slides.length - 1) : 1;
        progress.style.width = (Math.min(share, 1) * 100) + '%';
      }
      var notes = slide.querySelector('.notes');
      panel.innerHTML = '<span class="timer" id="deck-timer"></span><h2></h2>' + (notes ? notes.innerHTML : '');
      panel.querySelector('h2').textContent = format(config.notesTitle || 'Notes · Slide {0}', cur + 1);
      timer();
      if (previous !== cur) {
        var name = title(slide);
        live.textContent = format(config.slideAnnouncement || 'Slide {0} of {1}', cur + 1, slides.length) + (name ? ': ' + name : '');
      }
      try { if (location.protocol !== 'file:') { history.replaceState(null, '', '#' + (cur + 1)); } } catch (e) { /* not allowed here */ }
    }

    function go(n, s) {
      var previous = cur;
      cur = Math.max(0, Math.min(slides.length - 1, n));
      step = s === undefined ? 0 : s;
      render(previous);
    }

    function next() {
      if (!started) { started = Date.now(); }
      if (step < slides[cur].steps) { step++; render(cur); } else if (cur < slides.length - 1) { go(cur + 1, 0); }
    }

    function prev() {
      if (step > 0) { step--; render(cur); } else if (cur > 0) { go(cur - 1, slides[cur - 1].steps); }
    }

    function timer() {
      var el = document.getElementById('deck-timer');
      if (!el) { return; }
      if (!started) { el.textContent = '00:00'; return; }
      var s = Math.floor((Date.now() - started) / 1000);
      el.textContent = String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
    }
    setInterval(timer, 1000);

    window.addEventListener('keydown', function (e) {
      if (e.ctrlKey || e.metaKey || e.altKey) { return; }
      var k = e.key;
      if (k === 'ArrowRight' || k === 'ArrowDown' || k === 'PageDown' || k === ' ' || k === 'Enter') { e.preventDefault(); next(); }
      else if (k === 'ArrowLeft' || k === 'ArrowUp' || k === 'PageUp' || k === 'Backspace') { e.preventDefault(); prev(); }
      else if (k === 'Home') { go(0); }
      else if (k === 'End') { go(slides.length - 1, slides[slides.length - 1].steps); }
      else if (k === 'f' || k === 'F') {
        if (document.fullscreenElement) { document.exitFullscreen(); }
        else if (document.documentElement.requestFullscreen) { document.documentElement.requestFullscreen(); }
      }
      else if (k === 'n' || k === 'N') {
        panel.classList.toggle('open');
        panel.setAttribute('aria-hidden', panel.classList.contains('open') ? 'false' : 'true');
      }
      else if (k === 'b' || k === 'B' || k === '.') { document.body.classList.toggle('blank'); }
    });

    stage.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('a')) { return; }
      next();
    });

    var touchX = null;
    window.addEventListener('touchstart', function (e) { touchX = e.changedTouches[0].clientX; }, { passive: true });
    window.addEventListener('touchend', function (e) {
      if (touchX === null) { return; }
      var dx = e.changedTouches[0].clientX - touchX;
      touchX = null;
      if (Math.abs(dx) > 50) { if (dx < 0) { next(); } else { prev(); } }
    }, { passive: true });

    window.addEventListener('hashchange', function () {
      var n = parseInt(location.hash.slice(1), 10);
      if (!isNaN(n) && n - 1 !== cur) { go(n - 1, 0); }
    });

    window.addEventListener('beforeprint', function () {
      slides.forEach(function (s) { s.builds.forEach(function (b) { b.classList.add('on'); }); });
    });
    window.addEventListener('afterprint', function () { render(cur); });

    var start = parseInt(location.hash.slice(1), 10);
    go(isNaN(start) ? 0 : start - 1, 0);
  }

  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); } else { init(); }
})();
