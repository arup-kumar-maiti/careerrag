const ARMED_CLASS = 'armed';
const BULLET_SLICE = 2;
const DEFAULT_EXPAND_MS = 1000;
const DEFAULT_SPACER_HEIGHT = 60;
const ENTERING_CLEANUP_MS = 700;
const ERASE_MS = 18;
const EXPAND_EARLY_RATIO = 0.45;
const EXPAND_LATE_RATIO = 0.55;
const FOCUS_DELAY_MS = 100;
const GAP_MS = 350;
const HOLD_MS = 1400;
const INPUT_MAX_HEIGHT = 200;
const MS_PER_SEC = 1000;
const NAME = document.querySelector('.cr-root').dataset.name || 'John Doe';
const PLACEHOLDER_START_MS = 400;
const SCROLL_PIN_THRESHOLD = 0.5;
const SCROLL_SUPPRESS_MS = 250;
const STREAM_CPS = 360;
const STREAM_JUMP_MAX = 3;
const STREAM_JUMP_DIVISOR = 12;
const STREAM_START_MS = 380;
const STREAM_SUPPRESS_MS = 80;
const TYPE_MS = 38;
const SUGGESTIONS = [
  'What kind of work does ' + NAME + ' do best?',
  'How does ' + NAME + ' show up in a team?',
  'Walk me through a project ' + NAME + ' is proud of',
  'What do peers say about working with ' + NAME + '?',
];

const bottomSpacer = document.getElementById('cr-bottom-spacer');
const chatElement = document.getElementById('cr-chat');
const columnElement = document.getElementById('cr-col');
const composerElement = document.querySelector('.cr-composer');
const composerWrap = document.getElementById('cr-composer-wrap');
const emptyElement = document.getElementById('cr-empty');
const inputElement = document.getElementById('cr-input');
const resetButton = document.getElementById('cr-new');
const scrollerElement = document.getElementById('cr-scroll');
const sendButton = document.getElementById('cr-send');
const stageElement = document.getElementById('cr-stage');

let busy = false;
let following = true;
let stageState = 'empty';
let streamTimer = null;
let suppressScrollUntil = 0;

function autosize() {
  inputElement.style.height = 'auto';
  inputElement.style.height =
    Math.min(inputElement.scrollHeight, INPUT_MAX_HEIGHT) + 'px';
}

function setStage(state) {
  stageState = state;
  stageElement.dataset.state = state;
  if (state !== 'empty') inputElement.setAttribute('placeholder', '');
  chatElement.setAttribute('aria-hidden', state === 'empty' ? 'true' : 'false');
  emptyElement.setAttribute(
    'aria-hidden',
    state !== 'empty' ? 'true' : 'false',
  );
}

function makeTurnNode(userText) {
  const turn = document.createElement('div');
  turn.className = 'cr-turn entering';
  turn.innerHTML =
    '<div class="cr-msg user"><div class="body"></div></div>' +
    '<div class="cr-msg assistant"><div class="body"></div></div>';
  turn.querySelector('.cr-msg.user .body').textContent = userText;
  setTimeout(function cleanup() {
    turn.classList.remove('entering');
  }, ENTERING_CLEANUP_MS);
  return turn;
}

function recomputeSpacer() {
  document.documentElement.style.setProperty(
    '--composer-pad',
    composerWrap.offsetHeight + 'px',
  );
  const innerHeight = composerElement
    ? composerElement.offsetHeight
    : DEFAULT_SPACER_HEIGHT;
  document.documentElement.style.setProperty(
    '--composer-empty-h',
    innerHeight + 'px',
  );
  bottomSpacer.style.height = scrollerElement.clientHeight + 'px';
}

function snapToActive() {
  const turns = columnElement.querySelectorAll('.cr-turn');
  if (!turns.length) return;
  suppressScrollUntil = performance.now() + SCROLL_SUPPRESS_MS;
  scrollerElement.scrollTop = turns[turns.length - 1].offsetTop;
}

function escapeHtml(source) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  };
  return source.replace(/[&<>"']/g, function replace(character) {
    return map[character];
  });
}

function renderBody(text) {
  return text
    .split(/\n\n+/)
    .map(function renderBlock(block) {
      const lines = block.split('\n');
      if (
        lines.every(function isBullet(line) {
          return line.startsWith('\u2022 ');
        })
      ) {
        return (
          '<ul>' +
          lines
            .map(function renderItem(line) {
              return '<li>' + escapeHtml(line.slice(BULLET_SLICE)) + '</li>';
            })
            .join('') +
          '</ul>'
        );
      }
      return '<p>' + escapeHtml(block).replace(/\n/g, '<br>') + '</p>';
    })
    .join('');
}

function pinToLastTurn() {
  const turns = columnElement.querySelectorAll('.cr-turn');
  const last = turns[turns.length - 1];
  if (
    last &&
    Math.abs(scrollerElement.scrollTop - last.offsetTop) > SCROLL_PIN_THRESHOLD
  ) {
    suppressScrollUntil = performance.now() + STREAM_SUPPRESS_MS;
    scrollerElement.scrollTop = last.offsetTop;
  }
}

function streamReply(turnNode, fullText, onDone) {
  const target = turnNode.querySelector('.cr-msg.assistant .body');
  let position = 0;
  const total = fullText.length;
  const msPerChar = MS_PER_SEC / STREAM_CPS;
  target.innerHTML = '<span class="cr-cursor"></span>';

  function step() {
    const jump = Math.max(
      1,
      Math.min(STREAM_JUMP_MAX, Math.round(STREAM_JUMP_DIVISOR / msPerChar)),
    );
    position = Math.min(total, position + jump);
    const cursor = position < total ? '<span class="cr-cursor"></span>' : '';
    target.innerHTML = renderBody(fullText.slice(0, position)) + cursor;
    if (following) pinToLastTurn();
    if (position < total) {
      streamTimer = setTimeout(step, msPerChar * jump);
    } else {
      streamTimer = null;
      if (onDone) onDone();
    }
  }
  streamTimer = setTimeout(step, STREAM_START_MS);
}

function generateMockResponse() {
  return (
    'This is a placeholder response. Connect the backend to see real ' +
    'answers streamed here.'
  );
}

function commitTurn(userText) {
  busy = true;
  sendButton.disabled = true;
  sendButton.classList.remove(ARMED_CLASS);
  const turn = makeTurnNode(userText);
  columnElement.insertBefore(turn, bottomSpacer);
  following = true;
  recomputeSpacer();
  snapToActive();
  requestAnimationFrame(function resnap() {
    snapToActive();
    requestAnimationFrame(snapToActive);
  });
  streamReply(turn, generateMockResponse(), function onDone() {
    busy = false;
    sendButton.disabled = !inputElement.value.trim();
    if (inputElement.value.trim()) sendButton.classList.add(ARMED_CLASS);
    inputElement.focus();
  });
}

function send(text) {
  if (busy || !text || !text.trim()) return false;
  const trimmed = text.trim();
  if (stageState === 'empty') {
    setStage('leaving');
    const expandMs =
      parseInt(
        getComputedStyle(document.documentElement).getPropertyValue(
          '--t-expand',
        ),
      ) || DEFAULT_EXPAND_MS;
    setTimeout(function early() {
      commitTurn(trimmed);
      setTimeout(function late() {
        setStage('chat');
      }, expandMs * EXPAND_LATE_RATIO);
    }, expandMs * EXPAND_EARLY_RATIO);
  } else {
    commitTurn(trimmed);
  }
  return true;
}

function attemptSend() {
  if (!send(inputElement.value)) return;
  inputElement.value = '';
  autosize();
  sendButton.disabled = true;
  sendButton.classList.remove(ARMED_CLASS);
}

function typePlaceholderChar(state) {
  const target = SUGGESTIONS[state.index];
  state.position++;
  inputElement.setAttribute('placeholder', target.slice(0, state.position));
  if (state.position >= target.length) {
    state.mode = 'hold';
    return HOLD_MS;
  }
  return TYPE_MS;
}

function erasePlaceholderChar(state) {
  const target = SUGGESTIONS[state.index];
  state.position--;
  inputElement.setAttribute(
    'placeholder',
    target.slice(0, Math.max(state.position, 0)),
  );
  if (state.position <= 0) {
    state.mode = 'gap';
    return GAP_MS;
  }
  return ERASE_MS;
}

function advancePlaceholder(state) {
  if (state.mode === 'type') return typePlaceholderChar(state);
  if (state.mode === 'hold') {
    state.mode = 'erase';
    return ERASE_MS;
  }
  if (state.mode === 'erase') return erasePlaceholderChar(state);
  state.index = (state.index + 1) % SUGGESTIONS.length;
  state.position = 0;
  state.mode = 'type';
  return TYPE_MS;
}

function placeholderTick(state) {
  if (inputElement.value.length > 0 || stageState !== 'empty') return;
  const delay = advancePlaceholder(state);
  setTimeout(function nextTick() {
    placeholderTick(state);
  }, delay);
}

function runPlaceholderLoop() {
  inputElement.setAttribute('placeholder', '');
  setTimeout(function startTick() {
    placeholderTick({ index: 0, mode: 'type', position: 0 });
  }, PLACEHOLDER_START_MS);
}

function resetChat() {
  if (streamTimer) {
    clearTimeout(streamTimer);
    streamTimer = null;
  }
  columnElement.querySelectorAll('.cr-turn').forEach(function remove(node) {
    node.remove();
  });
  busy = false;
  following = true;
  sendButton.disabled = true;
  sendButton.classList.remove(ARMED_CLASS);
  setStage('empty');
  runPlaceholderLoop();
  inputElement.value = '';
  autosize();
  inputElement.focus();
}

inputElement.addEventListener('input', function handleInput() {
  autosize();
  const armed = inputElement.value.trim().length > 0 && !busy;
  sendButton.disabled = !armed;
  sendButton.classList.toggle(ARMED_CLASS, armed);
});
inputElement.addEventListener('keydown', function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    attemptSend();
  }
});
resetButton.addEventListener('click', resetChat);
scrollerElement.addEventListener(
  'scroll',
  function handleScroll() {
    if (performance.now() < suppressScrollUntil) return;
    following = false;
  },
  { passive: true },
);
sendButton.addEventListener('click', attemptSend);
window.addEventListener('resize', recomputeSpacer);
new ResizeObserver(recomputeSpacer).observe(composerWrap);
recomputeSpacer();
runPlaceholderLoop();
setTimeout(function focusInput() {
  inputElement.focus();
}, FOCUS_DELAY_MS);
