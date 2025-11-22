/* app.js — Voice in/out, typing, dark-mode, contact queue, guest replies (safety-aware) */

// Safe selector
const $ = id => document.getElementById(id);

// Elements
const loader = $('app-loader');
const startChatBtn = $('startChatBtn');
const floatingAssistant = $('floatingAssistant');
const chatSection = $('chatbot-section');
const chatWindow = $('chat-window');
const chatForm = $('chat-form');
const userInput = $('user-input');
const typingIndicator = $('typingIndicator');
const voiceToggle = $('voiceToggle');
const darkModeBtn = $('darkModeBtn');
const voiceBtn = $('voiceBtn');
const quickHelpBtn = $('quickHelpBtn');
const moodCheckBtn = $('moodCheckBtn');
const clearChatBtn = $('clearChatBtn');
const languageSelect = $('language-select');
const contactForm = $('contact-form');
const contactStatus = $('contactStatus');
const palettePreview = $('palettePreview');

// Helpers
const now = () => new Date().toLocaleTimeString();
const safeScroll = () => { if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight; };

// Hide loader & register SW
window.addEventListener('load', () => {
  try {
    if (loader) {
      setTimeout(()=>{ loader.style.transition='opacity 300ms ease'; loader.style.opacity='0'; setTimeout(()=> loader.remove(),360); }, 500);
    }
  } catch(e){ console.warn(e); }

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(err => console.warn('SW register failed', err));
  }

  setTimeout(()=> showTypingThen("Hi — I'm MentalWell. I can listen, guide breathing exercises, and share resources. How can I help?"), 800);
});

// open chat
const openChat = () => {
  if (chatSection && chatSection.scrollIntoView) {
    chatSection.scrollIntoView({behavior:'smooth', block:'center'});
    setTimeout(()=> userInput && userInput.focus(), 500);
  } else userInput && userInput.focus();
};
startChatBtn && startChatBtn.addEventListener('click', openChat);
floatingAssistant && floatingAssistant.addEventListener('click', openChat);

// dark mode
function updateDark() {
  const on = localStorage.getItem('darkMode') === 'enabled';
  document.body.classList.toggle('dark', on);
  if (darkModeBtn) darkModeBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
  if (darkModeBtn) darkModeBtn.textContent = on ? '☀' : '🌙';
  // Change voice button color in dark mode
  if (voiceBtn) {
    voiceBtn.style.color = on ? '#111' : '#fff';
  }
  if (voiceToggle) {
    voiceToggle.style.color = on ? '#111' : '#fff';
  }
}
updateDark();
darkModeBtn && darkModeBtn.addEventListener('click', () => {
  const toggled = !document.body.classList.contains('dark');
  localStorage.setItem('darkMode', toggled ? 'enabled' : 'disabled');
  updateDark();
});

// append messages
function appendUser(text){
  if (!chatWindow) return;
  const d = document.createElement('div'); d.className='msg user'; d.textContent=text;
  const t = document.createElement('span'); t.className='time'; t.textContent = now();
  d.appendChild(t); chatWindow.appendChild(d); safeScroll();
}
function appendBot(text){
  if (!chatWindow) return;
  const d = document.createElement('div'); d.className='msg bot'; d.textContent=text;
  const t = document.createElement('span'); t.className='time'; t.textContent = now();
  d.appendChild(t); chatWindow.appendChild(d); safeScroll();
  speak(text);
}

// typing indicator + typewriter
function showTypingThen(reply){
  if (!typingIndicator || !chatWindow) { appendBot(reply); return; }
  typingIndicator.innerHTML = '';
  for (let i=0;i<3;i++){ const s = document.createElement('span'); typingIndicator.appendChild(s); }
  typingIndicator.style.visibility='visible'; typingIndicator.setAttribute('aria-hidden','false');

  setTimeout(()=> {
    typingIndicator.style.visibility='hidden'; typingIndicator.setAttribute('aria-hidden','true');
    const el = document.createElement('div'); el.className='msg bot'; el.textContent='';
    chatWindow.appendChild(el); safeScroll();
    let i=0; const speed = 16 + Math.random()*18;
    const t = setInterval(()=> {
      if (i<reply.length) { el.textContent += reply.charAt(i++); safeScroll(); } else clearInterval(t);
    }, speed);
  }, 700 + Math.random()*700);
}

// ------ FIXED CHAT SUBMIT: Now talks to Flask backend (/api/chat) -------
chatForm && chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  if (!userInput) return;
  const txt = (userInput.value||'').trim(); if (!txt) return;
  appendUser(txt); userInput.value=''; userInput.style.height='';

  // TALK TO BACKEND INSTEAD OF BASIC REPLY!
  fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({message: txt})
  })
  .then(async resp => {
      const data = await resp.json();
      if (data.success && data.reply) {
          showTypingThen(data.reply);
      } else if (data.error) {
          showTypingThen("Error: " + data.error);
      } else {
          showTypingThen("Sorry, something went wrong!");
      }
  })
  .catch(() => {
      showTypingThen("Network error!");
  });
});

// chips
quickHelpBtn && quickHelpBtn.addEventListener('click', ()=>{ if (userInput) { userInput.value="I'm feeling anxious and overwhelmed."; userInput.focus(); } });
moodCheckBtn && moodCheckBtn.addEventListener('click', ()=>{ if (userInput) { userInput.value="I've been feeling low lately."; userInput.focus(); } });

// clear chat
clearChatBtn && clearChatBtn.addEventListener('click', ()=>{ if (chatWindow) chatWindow.innerHTML=''; if (userInput) userInput.focus(); });

// auto-resize textarea
if (userInput) {
  const resize = () => { userInput.style.height='auto'; userInput.style.height = (userInput.scrollHeight) + 'px'; };
  userInput.addEventListener('input', resize);
  setTimeout(resize, 200);
  userInput.addEventListener('keydown', (e)=>{ if (e.key==='Enter' && !e.shiftKey){ e.preventDefault(); chatForm && chatForm.dispatchEvent(new Event('submit',{cancelable:true})); }});
}

// ---- Voice (SpeechRecognition) + SpeechSynthesis ----
let recognition = null, listening = false;
const hasSR = ('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window);
if (hasSR) {
  try {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.interimResults = false; recognition.maxAlternatives = 1;
    recognition.onstart = () => { listening = true; voiceToggle && voiceToggle.classList.add('listening'); voiceToggle && voiceToggle.setAttribute('aria-pressed','true'); };
    recognition.onend = () => { listening = false; voiceToggle && voiceToggle.classList.remove('listening'); voiceToggle && voiceToggle.setAttribute('aria-pressed','false'); };
    recognition.onerror = (e)=>{ console.warn('sr error', e); };
    recognition.onresult = (ev) => {
      try {
        const t = ev.results[0][0].transcript;
        if (userInput) userInput.value = t;
        setTimeout(()=> { chatForm && chatForm.dispatchEvent(new Event('submit',{cancelable:true})); }, 250);
      } catch(e){ console.warn(e); }
    };
  } catch(e){ recognition = null; console.warn('sr init', e); }
} else {
  voiceToggle && (voiceToggle.style.display = 'none');
  voiceBtn && (voiceBtn.style.display = 'inline-block');
}

voiceToggle && voiceToggle.addEventListener('click', ()=> {
  if (!recognition) return;
  if (listening) { try { recognition.stop(); } catch(e){ console.warn(e); } }
  else {
    try {
      recognition.lang = (languageSelect && languageSelect.value === 'hi') ? 'hi-IN'
                      : (languageSelect && languageSelect.value === 'es') ? 'es-ES'
                      : (languageSelect && languageSelect.value === 'fr') ? 'fr-FR'
                      : 'en-US';
      recognition.start();
    } catch(e){ console.warn('sr start', e); }
  }
});

voiceBtn && voiceBtn.addEventListener('click', ()=> {
  if (recognition) { try { recognition.start(); } catch(e){ console.warn(e); } }
  else {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return alert('Voice not supported in this browser.');
    navigator.mediaDevices.getUserMedia({audio:true}).then(stream=>{
      alert('Captured audio locally (demo). In production, send this to a transcription endpoint.');
      stream.getTracks().forEach(t=>t.stop());
    }).catch(()=>alert('Microphone denied.'));
  }
});

// speech synthesis
function speak(text) {
  if (!window.speechSynthesis) return;
  try {
    const utter = new SpeechSynthesisUtterance(text);
    const lang = (languageSelect && languageSelect.value) || 'en';
    utter.lang = (lang==='hi') ? 'hi-IN' : (lang==='es') ? 'es-ES' : (lang==='fr') ? 'fr-FR' : 'en-US';
    utter.rate = 0.95; utter.pitch = 1.0; utter.volume = 1.0;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  } catch(e){ console.warn('speak err', e); }
}

// ---- Contact queue (localStorage) ----
const CONTACT_QUEUE_KEY = 'healthsync_contact_queue';
function queueContact(payload) {
  const q = JSON.parse(localStorage.getItem(CONTACT_QUEUE_KEY) || '[]');
  q.push(Object.assign({id: Date.now(), sent:false}, payload));
  localStorage.setItem(CONTACT_QUEUE_KEY, JSON.stringify(q));
  updateContactStatus();
}
async function flushContactQueue() {
  const q = JSON.parse(localStorage.getItem(CONTACT_QUEUE_KEY) || '[]');
  if (!q.length) return;
  for (let item of q) {
    try {
      const res = await fetch('/contact', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(item)
      });
      if (res && res.ok) item.sent = true;
    } catch(e){ /* keep queued */ }
  }
  const remaining = q.filter(i=>!i.sent);
  localStorage.setItem(CONTACT_QUEUE_KEY, JSON.stringify(remaining));
  updateContactStatus();
}
function updateContactStatus() {
  const q = JSON.parse(localStorage.getItem(CONTACT_QUEUE_KEY) || '[]');
  if (!contactStatus) return;
  contactStatus.textContent = q.length ? `You have ${q.length} queued message(s) (will send when online).` : '';
}

contactForm && contactForm.addEventListener('submit', (e)=>{
  e.preventDefault();
  const payload = {
    name: (document.getElementById('name')||{}).value || '',
    email: (document.getElementById('email')||{}).value || '',
    message: (document.getElementById('message')||{}).value || '',
    ts: new Date().toISOString()
  };
  if (!payload.message) { contactStatus.textContent = 'Please write a message.'; return; }

  if (navigator.onLine) {
    fetch('/contact', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)})
      .then(r => {
        if (r.ok) { contactStatus.textContent = 'Your message was sent. Thank you!'; contactForm.reset(); }
        else { queueContact(payload); contactForm.reset(); contactStatus.textContent = 'Saved locally — will retry when online.'; }
      }).catch(()=> { queueContact(payload); contactForm.reset(); contactStatus.textContent = 'Saved locally — will retry when online.'; });
  } else {
    queueContact(payload); contactForm.reset(); contactStatus.textContent = 'You are offline. Message queued and will be sent when online.';
  }
});

window.addEventListener('online', ()=>{ appendBot('You are back online — attempting to send queued messages.'); flushContactQueue().then(()=>updateContactStatus()); });
window.addEventListener('offline', ()=>{ appendBot('You are offline — some features may be limited.'); });

// flush queue on load
setTimeout(()=>{ flushContactQueue(); updateContactStatus(); }, 1200);

// palette preview (small playful pulse)
palettePreview && palettePreview.addEventListener('click', ()=> {
  document.body.animate([{filter:'saturate(1)'},{filter:'saturate(1.12)'}], {duration:420, easing:'ease-in-out', iterations:1});
});