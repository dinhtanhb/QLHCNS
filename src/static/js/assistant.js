/* Trợ lý tài liệu: khung chat tìm kiếm văn bản, dùng cho trang /assistant/
   và nút nổi trên portal. Không gửi dữ liệu ra ngoài IHRMS/SharePoint. */
(function () {
  'use strict';

  const MIN_QUESTION_LENGTH = 2;
  const MOBILE_PAGE_SWITCH_PX = 640;
  const ICON_TEMPLATES = { ihrms: 'assistantIconIHRMS', sharepoint: 'assistantIconSharePoint' };
  const MESSAGES = {
    loading: 'Đang tìm tài liệu…',
    empty: 'Không tìm thấy tài liệu phù hợp trong phạm vi quyền của anh/chị.',
    search_fallback: 'Đang hiển thị kết quả theo tên tệp trong các thư mục SharePoint được phép.',
    partial: 'SharePoint tạm không phản hồi — kết quả dưới đây chỉ gồm tài liệu trong IHRMS.',
    network: 'Không kết nối được máy chủ. Anh/chị kiểm tra mạng rồi thử lại.',
    rate_limited: 'Anh/chị đã gửi quá nhiều câu hỏi trong một phút. Hãy đợi chút rồi thử lại.',
    question_too_short: 'Câu hỏi cần ít nhất hai ký tự.',
    invalid_json: 'Câu hỏi không được chấp nhận. Anh/chị thử lại nhé.',
    session_expired: 'Phiên làm việc đã hết hạn. Anh/chị đăng nhập lại rồi thử lại nhé.',
    unknown: 'Không thực hiện được truy vấn. Anh/chị thử lại sau.'
  };

  function csrfToken() {
    const parts = (document.cookie || '').split(';');
    for (let i = 0; i < parts.length; i += 1) {
      const pair = parts[i].trim();
      if (pair.indexOf('csrftoken=') === 0) {
        return decodeURIComponent(pair.slice('csrftoken='.length));
      }
    }
    return '';
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function sourceIcon(source) {
    const holder = document.getElementById(ICON_TEMPLATES[source] || ICON_TEMPLATES.ihrms);
    if (!holder || !holder.content) return null;
    const svg = holder.content.querySelector('svg');
    return svg ? document.importNode(svg, true) : null;
  }

  /* Liên kết chỉ chấp nhận đường dẫn nội bộ hoặc SharePoint qua HTTPS:
     tiêu đề và URL đến từ dữ liệu nên không được phép thành javascript:. */
  function safeUrl(url) {
    if (typeof url !== 'string') return '';
    const value = url.trim();
    if (value.indexOf('/') === 0 && value.indexOf('//') !== 0) return value;
    if (value.indexOf('https://') === 0) return value;
    return '';
  }

  function dayLabel(isoDate) {
    if (typeof isoDate !== 'string' || isoDate.length < 10) return '';
    const parts = isoDate.slice(0, 10).split('-');
    return parts[2] + '/' + parts[1] + '/' + parts[0];
  }

  function renderResult(row) {
    const href = safeUrl(row.url);
    const card = el(href ? 'a' : 'div', 'assistant-result');
    if (href) {
      card.href = href;
      if (href.indexOf('https://') === 0) {
        card.target = '_blank';
        card.rel = 'noopener noreferrer';
      }
    }
    const icon = sourceIcon(row.source);
    if (icon) {
      icon.setAttribute('class', 'ui-icon assistant-result-icon');
      card.appendChild(icon);
    }
    const body = el('div', 'assistant-result-body');
    body.appendChild(el('div', 'assistant-result-title', row.title || '(không tên)'));
    const meta = [row.meta, dayLabel(row.date)].filter(Boolean).join(' · ');
    if (meta) body.appendChild(el('div', 'assistant-result-meta', meta));
    card.appendChild(body);
    return card;
  }

  function renderResults(panel, payload) {
    if (payload && payload.partial) {
      panel.appendChild(el('div', 'assistant-warning', payload.sharepoint_status === 'search_fallback' ? MESSAGES.search_fallback : MESSAGES.partial));
    }
    const results = (payload && Array.isArray(payload.results)) ? payload.results : [];
    if (!results.length) {
      panel.appendChild(el('div', 'assistant-msg assistant-msg-bot', MESSAGES.empty));
      return;
    }
    const list = el('div', 'assistant-results');
    results.forEach(function (row) { list.appendChild(renderResult(row)); });
    panel.appendChild(list);
  }

  function failureMessage(code, status) {
    if (MESSAGES[code]) return MESSAGES[code];
    return MESSAGES.unknown + ' (HTTP ' + status + ')';
  }

  function setBusy(state, busy) {
    state.busy = busy;
    const controls = state.root.querySelectorAll('input, button');
    Array.prototype.forEach.call(controls, function (control) {
      control.disabled = busy;
    });
  }

  function scrollPanel(panel) {
    panel.scrollTop = panel.scrollHeight;
  }

  function ask(state, question) {
    if (state.busy || question.length < MIN_QUESTION_LENGTH) return;
    const panel = state.panel;
    setBusy(state, true);
    panel.appendChild(el('div', 'assistant-msg assistant-msg-user', question));
    const pending = el('div', 'assistant-status', MESSAGES.loading);
    panel.appendChild(pending);
    scrollPanel(panel);

    fetch(state.root.getAttribute('data-api'), {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify({ question: question })
    }).then(function (response) {
      const type = response.headers.get('Content-Type') || '';
      if (response.ok && type.indexOf('application/json') === -1) {
        // `login_required` trả 302 về trang đăng nhập khi phiên hết hạn và fetch
        // tự đi theo redirect: `ok` vẫn true nhưng body là HTML, không phải JSON.
        // Nếu nuốt thành {} thì `renderResults` in ra "không có tài liệu trong
        // phạm vi quyền" - hết phiên bị báo nhầm thành hết quyền.
        return { ok: false, status: response.status, data: { error: 'session_expired' } };
      }
      return response.json()
        .catch(function () { return {}; })
        .then(function (data) { return { ok: response.ok, status: response.status, data: data }; });
    }).then(function (result) {
      if (pending.parentNode) pending.parentNode.removeChild(pending);
      if (!result.ok) {
        panel.appendChild(el('div', 'assistant-error', failureMessage(result.data.error, result.status)));
        return;
      }
      renderResults(panel, result.data);
    }).catch(function () {
      if (pending.parentNode) pending.parentNode.removeChild(pending);
      panel.appendChild(el('div', 'assistant-error', MESSAGES.network));
    }).then(function () {
      setBusy(state, false);
      scrollPanel(panel);
    });
  }

  function bindRoot(root) {
    const panel = root.querySelector('[data-role="panel"]');
    const form = root.querySelector('[data-role="form"]');
    const input = form ? form.querySelector('input[name="question"]') : null;
    if (!panel || !form || !input) return null;

    const state = { root: root, panel: panel, input: input, busy: false };

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      const question = input.value.trim();
      if (question.length < MIN_QUESTION_LENGTH) return;
      input.value = '';
      ask(state, question);
    });

    Array.prototype.forEach.call(root.querySelectorAll('.assistant-chip'), function (chip) {
      chip.addEventListener('click', function () {
        ask(state, (chip.getAttribute('data-question') || '').trim());
      });
    });

    const historyUrl = root.getAttribute('data-history');
    if (historyUrl) {
      setBusy(state, true);
      fetch(historyUrl, { credentials: 'same-origin', cache: 'no-store' })
        .then(function (response) { return response.ok ? response.json() : { turns: [] }; })
        .then(function (data) {
          (data.turns || []).forEach(function (turn) {
            panel.appendChild(el('div', 'assistant-msg assistant-msg-user', turn.question));
            renderResults(panel, turn.answer);
          });
        }).catch(function () {
          panel.appendChild(el('div', 'assistant-error', 'Không tải được hội thoại trước. Anh/chị vẫn có thể gửi câu hỏi mới.'));
        }).then(function () { setBusy(state, false); scrollPanel(panel); });
    }
    return state;
  }

  function initRoot(root) {
    if (!root || root.dataset.assistantReady === '1') return;
    const state = bindRoot(root);
    if (!state) return;
    root.dataset.assistantReady = '1';
  }

  function buildDockRoot(fab) {
    const root = el('div', 'ui-card assistant-root');
    root.setAttribute('data-api', fab.getAttribute('data-api'));
    root.setAttribute('data-history', fab.getAttribute('data-history'));

    const panel = el('div', 'assistant-panel');
    panel.setAttribute('data-role', 'panel');
    panel.setAttribute('role', 'status');
    panel.setAttribute('aria-live', 'polite');

    const form = el('form', 'assistant-form');
    form.setAttribute('data-role', 'form');
    form.setAttribute('autocomplete', 'off');
    const field = el('div', 'ui-field assistant-question');
    const label = el('label', 'ui-sr-only', 'Câu hỏi tìm tài liệu');
    label.setAttribute('for', 'assistantDockInput');
    const input = el('input');
    input.type = 'text';
    input.id = 'assistantDockInput';
    input.name = 'question';
    input.maxLength = 500;
    input.placeholder = 'Nhập câu hỏi…';
    field.appendChild(label);
    field.appendChild(input);
    const button = el('button', 'ui-button ui-button--primary', 'Gửi');
    button.type = 'submit';
    form.appendChild(field);
    form.appendChild(button);

    root.appendChild(panel);
    root.appendChild(form);
    return root;
  }

  function initFab(fab) {
    const dock = document.getElementById('assistantDock');
    if (!fab || !dock) return;
    // `initRoot` đã tự chốt bằng dataset; nút nổi cũng phải vậy vì listener
    // Escape gắn trên document — gọi initFab hai lần là nhân đôi người nghe.
    if (fab.dataset.assistantFabReady) return;
    fab.dataset.assistantFabReady = '1';

    function setOpen(open) {
      if (open && !dock.firstElementChild) {
        const root = buildDockRoot(fab);
        dock.appendChild(root);
        initRoot(root);
      }
      dock.hidden = !open;
      fab.setAttribute('aria-expanded', String(open));
      if (open) {
        const input = dock.querySelector('input[name="question"]');
        if (input) input.focus();
      }
    }

    fab.addEventListener('click', function () {
      if (window.innerWidth < MOBILE_PAGE_SWITCH_PX) {
        window.location.href = fab.getAttribute('data-page-url');
        return;
      }
      setOpen(dock.hidden);
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && !dock.hidden) {
        setOpen(false);
        fab.focus();
      }
    });
  }

  function start() {
    const fab = document.getElementById('assistantFab');
    if (fab) initFab(fab);
    Array.prototype.forEach.call(document.querySelectorAll('.assistant-root'), initRoot);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }

  window.IHRMSAssistant = { initRoot: initRoot, initFab: initFab };
})();
