const ARMED_CLASS = 'armed';
const BULLET_SLICE = 2;
const DEFAULT_EXPAND_MS = 1000;
const DEFAULT_NAME = 'John Doe';
const DEFAULT_SPACER_HEIGHT = 60;
const ENTERING_CLASS = 'entering';
const ENTERING_CLEANUP_MS = 700;
const ERASE_MS = 18;
const EXPAND_EARLY_RATIO = 0.45;
const EXPAND_LATE_RATIO = 0.55;
const FOCUS_DELAY_MS = 100;
const GAP_MS = 350;
const HOLD_MS = 1400;
const INPUT_MAX_HEIGHT = 200;
const MODE_ERASE = 'erase';
const MODE_GAP = 'gap';
const MODE_HOLD = 'hold';
const MODE_TYPE = 'type';
const MS_PER_SEC = 1000;
const NAME = document.querySelector('.cr-root').dataset.name || DEFAULT_NAME;
const PLACEHOLDER_START_MS = 400;
const SCROLL_PIN_THRESHOLD = 0.5;
const SCROLL_SUPPRESS_MS = 250;
const STAGE_CHAT = 'chat';
const STAGE_EMPTY = 'empty';
const STAGE_LEAVING = 'leaving';
const STREAM_CHARS_PER_SEC = 360;
const STREAM_JUMP_DIVISOR = 12;
const STREAM_JUMP_MAX = 3;
const STREAM_START_MS = 380;
const STREAM_SUPPRESS_MS = 80;
const TURN_SELECTOR = '.cr-turn';
const TYPE_MS = 38;
const TYPEWRITER_PROMPTS = [
  'How does ' + NAME + ' show up in a team?',
  'Walk me through a project ' + NAME + ' is proud of',
  'What do peers say about working with ' + NAME + '?',
  'What kind of work does ' + NAME + ' do best?',
];

const bottomSpacer = document.getElementById('cr-bottom-spacer');
const chatElement = document.getElementById('cr-chat');
const columnElement = document.getElementById('cr-column');
const composerElement = document.querySelector('.cr-composer');
const composerForm = document.getElementById('cr-composer');
const composerWrap = document.getElementById('cr-composer-wrap');
const emptyElement = document.getElementById('cr-empty');
const inputElement = document.getElementById('cr-input');
const resetButton = document.getElementById('cr-new');
const scrollerElement = document.getElementById('cr-scroll');
const sendButton = document.getElementById('cr-send');
const stageElement = document.getElementById('cr-stage');

let busy = false;
let following = true;
let stageState = STAGE_EMPTY;
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
  if (state !== STAGE_EMPTY) inputElement.setAttribute('placeholder', '');
  chatElement.setAttribute(
    'aria-hidden',
    state === STAGE_EMPTY ? 'true' : 'false',
  );
  emptyElement.setAttribute(
    'aria-hidden',
    state !== STAGE_EMPTY ? 'true' : 'false',
  );
}

function makeTurnNode(userText) {
  const turn = document.createElement('div');
  turn.className = 'cr-turn ' + ENTERING_CLASS;
  turn.innerHTML =
    '<div class="cr-message user"><div class="cr-body"></div></div>' +
    '<div class="cr-message assistant"><div class="cr-body"></div></div>';
  turn.querySelector('.cr-message.user .cr-body').textContent = userText;
  setTimeout(function cleanupEntering() {
    turn.classList.remove(ENTERING_CLASS);
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
  const turns = columnElement.querySelectorAll(TURN_SELECTOR);
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

function renderBulletList(lines) {
  return (
    '<ul class="cr-list">' +
    lines
      .map(function renderItem(line) {
        return (
          '<li class="cr-list-item">' +
          escapeHtml(line.slice(BULLET_SLICE)) +
          '</li>'
        );
      })
      .join('') +
    '</ul>'
  );
}

function renderBlock(block) {
  const lines = block.split('\n');
  if (
    lines.every(function isBullet(line) {
      return line.startsWith('\u2022 ');
    })
  ) {
    return renderBulletList(lines);
  }
  return (
    '<p class="cr-paragraph">' +
    escapeHtml(block).replace(/\n/g, '<br>') +
    '</p>'
  );
}

function renderBody(text) {
  return text.split(/\n\n+/).map(renderBlock).join('');
}

function generateMockResponse() {
  return (
    'This is a placeholder response. Connect the backend to see real ' +
    'answers streamed here.'
  );
}

function pinToLastTurn() {
  const turns = columnElement.querySelectorAll(TURN_SELECTOR);
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
  const target = turnNode.querySelector('.cr-message.assistant .cr-body');
  let position = 0;
  const total = fullText.length;
  const msPerChar = MS_PER_SEC / STREAM_CHARS_PER_SEC;
  target.innerHTML = '<span class="cr-cursor"></span>';

  function advanceStream() {
    const jump = Math.max(
      1,
      Math.min(STREAM_JUMP_MAX, Math.round(STREAM_JUMP_DIVISOR / msPerChar)),
    );
    position = Math.min(total, position + jump);
    const cursor = position < total ? '<span class="cr-cursor"></span>' : '';
    target.innerHTML = renderBody(fullText.slice(0, position)) + cursor;
    if (following) pinToLastTurn();
    if (position < total) {
      streamTimer = setTimeout(advanceStream, msPerChar * jump);
    } else {
      streamTimer = null;
      if (onDone) onDone();
    }
  }
  streamTimer = setTimeout(advanceStream, STREAM_START_MS);
}

function insertTurn(userText) {
  const turn = makeTurnNode(userText);
  columnElement.insertBefore(turn, bottomSpacer);
  following = true;
  recomputeSpacer();
  snapToActive();
  requestAnimationFrame(function resnapAfterPaint() {
    snapToActive();
    requestAnimationFrame(snapToActive);
  });
  return turn;
}

function commitTurn(userText) {
  busy = true;
  sendButton.disabled = true;
  sendButton.classList.remove(ARMED_CLASS);
  const turn = insertTurn(userText);
  streamReply(turn, generateMockResponse(), function handleStreamDone() {
    busy = false;
    sendButton.disabled = !inputElement.value.trim();
    if (inputElement.value.trim()) sendButton.classList.add(ARMED_CLASS);
    inputElement.focus();
  });
}

function send(text) {
  if (busy || !text || !text.trim()) return false;
  const trimmed = text.trim();
  if (stageState === STAGE_EMPTY) {
    setStage(STAGE_LEAVING);
    const expandMs =
      parseInt(
        getComputedStyle(document.documentElement).getPropertyValue(
          '--t-expand',
        ),
      ) || DEFAULT_EXPAND_MS;
    setTimeout(function beginCommit() {
      commitTurn(trimmed);
      setTimeout(function finishTransition() {
        setStage(STAGE_CHAT);
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
  const target = TYPEWRITER_PROMPTS[state.index];
  state.position++;
  inputElement.setAttribute('placeholder', target.slice(0, state.position));
  if (state.position >= target.length) {
    state.mode = MODE_HOLD;
    return HOLD_MS;
  }
  return TYPE_MS;
}

function erasePlaceholderChar(state) {
  const target = TYPEWRITER_PROMPTS[state.index];
  state.position--;
  inputElement.setAttribute(
    'placeholder',
    target.slice(0, Math.max(state.position, 0)),
  );
  if (state.position <= 0) {
    state.mode = MODE_GAP;
    return GAP_MS;
  }
  return ERASE_MS;
}

function advancePlaceholder(state) {
  if (state.mode === MODE_TYPE) return typePlaceholderChar(state);
  if (state.mode === MODE_HOLD) {
    state.mode = MODE_ERASE;
    return ERASE_MS;
  }
  if (state.mode === MODE_ERASE) return erasePlaceholderChar(state);
  state.index = (state.index + 1) % TYPEWRITER_PROMPTS.length;
  state.position = 0;
  state.mode = MODE_TYPE;
  return TYPE_MS;
}

function tickPlaceholder(state) {
  if (inputElement.value.length > 0 || stageState !== STAGE_EMPTY) return;
  const delay = advancePlaceholder(state);
  setTimeout(function runNextTick() {
    tickPlaceholder(state);
  }, delay);
}

function runPlaceholderLoop() {
  inputElement.setAttribute('placeholder', '');
  setTimeout(function startTick() {
    tickPlaceholder({ index: 0, mode: MODE_TYPE, position: 0 });
  }, PLACEHOLDER_START_MS);
}

function resetChat() {
  if (streamTimer) {
    clearTimeout(streamTimer);
    streamTimer = null;
  }
  columnElement
    .querySelectorAll(TURN_SELECTOR)
    .forEach(function removeTurn(node) {
      node.remove();
    });
  busy = false;
  following = true;
  sendButton.disabled = true;
  sendButton.classList.remove(ARMED_CLASS);
  setStage(STAGE_EMPTY);
  runPlaceholderLoop();
  inputElement.value = '';
  autosize();
  inputElement.focus();
}

composerForm.addEventListener('submit', function preventSubmit(event) {
  event.preventDefault();
});
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
