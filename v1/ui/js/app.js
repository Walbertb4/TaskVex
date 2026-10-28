import {initTaskPermissions, startTaskPermissions, refreshTaskPermissions} from './task_permissions.js';
import {initWorkflowView, startWorkflowView, refreshWorkflows} from './workflow_view.js';
/** Module startup, snapshot coordination and general UI bindings.
 * The sole owner of the talk/wake/Stop lifecycle is the assistant_session.js file. */
import { initApi, emit, addLog, isBackendAvailable, sanitizeError } from './api.js';
import { startupStatus, getStartupTasks, streamReset, streamMsg, msg, say, user, task, taskDone, start, tick } from './shell.js';
import { initCredentials } from './credentials.js';
import { liveMic } from './live_mic.js';
import { refreshSystem, startSystemView } from './system_view.js';
import { refreshMedia, startMediaView } from './media_view.js';
import { refreshWeather, startWeatherView } from './weather_view.js';
import { liveTranscript } from './live_transcript.js';
import { initReactor, setState, setLevel, setMicLevel, attachAudio, detachAudio, wakeAnimation } from './reactor.js';
import { initSettings, store, saveAll, saveSettingsConfirmed, setDevices, queryDevices, loadStore, validateAndNormalizeSnapshot, registerCollectionGetters, setBackupImportHandler } from './settings.js';
import { initPanels, openM, closeM, toggleD, setScreen, addTL, setTimeline } from './panels.js';
import { initTimers, connectTimers, startTimer, pauseTimer, resumeTimer, resetTimer, startStopwatch, pauseStopwatch, resumeStopwatch, resetStopwatch } from './timers.js';
import { initNotes, addNote, setNotes, getNotes, connectNativeNotes } from './notes.js';
import { initSkills, setSkills, addSkill, skillResult, getSkills, runSkill } from './skills.js';
import { initRoutines, setRoutines, routineResult, getRoutines, runRoutine, renderRoutines } from './routines.js';
import { initConnections, setCatalog, loadLiveModels, setGoogleStatus, setWeather, setCalendar, setReminders, setTelemetry, setTokens, setMedia, setNetwork } from './connections.js';
import {sendText, shutdownApplication, flushClockAnnouncement, assistantReady, receiveAudioChunk, setAssistantState, enqueueClockAnnouncement, initAssistantControls} from './assistant_session.js';

export function applySnapshot(snapshot, options = {}) {
  // Native note authority cannot be exceeded by snapshot/import. Restore separate core
  // requires command; We cannot apply the existing backup locally and call it a success.
  if (isBackendAvailable() && snapshot && Object.hasOwn(snapshot, 'notes') && !options.skipPersist) return false;
  // 1. Pre-validation and normalization: reject invalid snapshots before mutating any state or localStorage
  const validation = validateAndNormalizeSnapshot(snapshot);
  if (!validation.ok) {
    console.error('[Snapshot] Validation rejected:', validation.error);
    return false;
  }

  // Work on the validated, normalized candidate ONLY
  const candidate = validation.candidate;
  const { emitSave = false, skipPersist = false } = options;

  // 2. Settings, layout and theme (silent, skip intermediate localStorage writes and save events)
  loadStore(candidate, { emitSave: false, skipPersist: true });

  // 3. Notes contract:
  // - Array provided: replace collection with validated normalized candidate.notes
  // - Explicit null: clear collection
  // - Omitted (undefined): preserve existing in both full and partial snapshots
  if (Array.isArray(candidate.notes)) {
    setNotes(candidate.notes, { silent: true });
  } else if (candidate.notes === null) {
    setNotes([], { silent: true });
  }

  // 4. Skills contract:
  if (Array.isArray(candidate.skills)) {
    setSkills(candidate.skills, { silent: true });
  } else if (candidate.skills === null) {
    setSkills([], { silent: true });
  }

  // 5. Routines contract:
  if (Array.isArray(candidate.routines)) {
    setRoutines(candidate.routines, { silent: true });
  } else if (candidate.routines === null) {
    setRoutines([], { silent: true });
  }

  // 6. Optional modules
  if (candidate.calendar !== undefined) {
    setCalendar(candidate.calendar);
  }
  if (candidate.reminders !== undefined) {
    setReminders(candidate.reminders);
  }
  if (candidate.weather !== undefined) {
    setWeather(candidate.weather);
  }
  if (candidate.telemetry !== undefined) {
    setTelemetry(candidate.telemetry);
  }
  if (candidate.tokens !== undefined) {
    if (Array.isArray(candidate.tokens)) {
      setTokens(...candidate.tokens);
    } else if (candidate.tokens && typeof candidate.tokens === 'object') {
      setTokens(candidate.tokens.used, candidate.tokens.max, candidate.tokens.isEst);
    }
  }
  if (candidate.network !== undefined) {
    setNetwork(candidate.network);
  }
  if (candidate.media !== undefined) {
    setMedia(candidate.media);
  }
  if (candidate.googleStatus !== undefined) {
    setGoogleStatus(candidate.googleStatus);
  }
  if (candidate.timeline !== undefined) {
    setTimeline(candidate.timeline);
  }
  if (candidate.devices !== undefined) {
    setDevices(candidate.devices);
  }
  if (candidate.catalog !== undefined) {
    setCatalog(candidate.catalog);
  }

  // 7. Single atomic persistence step:
  return skipPersist ? true : saveAll({ emitSave });
}

// Bootstrap all submodules
document.addEventListener('DOMContentLoaded', () => {
  // 1. Settings & theme
  initSettings();
  initTaskPermissions();
  initWorkflowView();
  initCredentials();

  registerCollectionGetters({
    getNotes,
    getSkills,
    getRoutines
  });

  setBackupImportHandler((parsed, options = {}) => {
    return applySnapshot(parsed, { emitSave: false, ...options });
  });

  // 2. Reactor
  initReactor();
  liveMic.setNoiseThreshold(store.noise);
  window.addEventListener('taskvex-noise-changed', () => liveMic.setNoiseThreshold(store.noise));

  // 3. Timers & Stopwatch
  initTimers({
    onTimerFinished: enqueueClockAnnouncement,
    onClockPoll: flushClockAnnouncement
  });

  // 4. Notes
  initNotes({
    initialNotes: store.notes || [],
    saveStore: (opts) => saveAll(opts),
    addTimeline: (x, ok, k) => addTL(x, ok, k)
  });

  // 5. Skills
  initSkills({
    initialSkills: store.skills || [],
    saveStore: (opts) => saveAll(opts),
    openModal: id => openM(id),
    closeModal: () => closeM()
  });

  // 6. Routines
  initRoutines({
    initialRoutines: store.routines || [],
    saveStore: (opts) => saveAll(opts)
  });

  // 7. Connections & Telemetry
  initConnections({
    saveStore: opts => saveAll(opts)
  });

  // 8. Panels, Modals & Command Palette
  initPanels({
    queryDevices,
    renderRoutines: () => renderRoutines(),
    getSkills: () => getSkills(),
    getRoutines: () => getRoutines(),
    runSkill: s => runSkill(s),
    runRoutine: (r, src) => runRoutine(r, src),
    addNote: t => addNote(t),
    sendText: t => sendText(t),
  });

  const finishNativeStartup = async () => {
    startSystemView();startMediaView();startWeatherView();startTaskPermissions();startWorkflowView();queryDevices();
    await connectTimers();await connectNativeNotes();assistantReady();void loadLiveModels();
  };
  for (const [id, event] of [['retryStartup', 'retry_startup'], ['recoverSettings', 'recover_settings'], ['acknowledgeTasks','acknowledge_tasks']]) {
    document.getElementById(id)?.addEventListener('click', async () => {
      if (event === 'recover_settings' && !confirm(
        'Back up the original settings file and repair saved preferences? Valid fields will be kept. Local notes, skills, routines and profile data will not be deleted.'
      )) return;
      const reviewed = getStartupTasks();
      if(event==='acknowledge_tasks' && (!reviewed.length || !confirm(
        'These actions may already have happened. Check their effects before continuing:\n' +
        reviewed.map(task=>task.tool+' · '+task.task_id).join('\n') +
        '\nContinue without repeating them? Their results will remain unknown in history.')))return;
      const buttons = ['retryStartup','recoverSettings','acknowledgeTasks'].map(id=>document.getElementById(id));
      buttons.forEach(button => { button.disabled = true; });
      try {
        const result = await emit(event, event === 'recover_settings' ? {confirmed:true} : event==='acknowledge_tasks'
          ? {confirmed:true,task_ids:reviewed.map(task=>task.task_id)} : null);
        if (!result.ok) {
          const message = document.getElementById('nativeIssueText');
          if (message) message.textContent = sanitizeError(result.error);
        } else if (result.response?.completed === true) {await finishNativeStartup();}
      } finally { buttons.forEach(button => { button.disabled = false; }); }
    });
  }

  initAssistantControls();

  // 9. API & Bridge bindings
  initApi({
    nativeReady: finishNativeStartup,
    initApp: (s) => applySnapshot(s, { emitSave: false }),
    startupStatus,
    loadStore: (s) => applySnapshot(s, { emitSave: false }),
    msg,
    streamMsg,
    streamReset,
    say,
    audioChunk: receiveAudioChunk,
    liveTranscript: packet => liveTranscript.chunk(packet),
    user,
    log: addLog,
    setState: setAssistantState,
    level: setLevel,
    micLevel: v => setMicLevel(v, store.noise),
    attachAudio,
    detachAudio,
    wake: wakeAnimation,
    wakeWait: on => {
      const wkP = document.getElementById('wkP');
      if (wkP) wkP.style.display = on ? '' : 'none';
    },
    startTimer,
    pauseTimer,
    resumeTimer,
    resetTimer,
    startStopwatch,
    pauseStopwatch,
    resumeStopwatch,
    resetStopwatch,
    telemetry: setTelemetry,
    tokens: setTokens,
    network: setNetwork,
    weather: setWeather,
    media: setMedia,
    setCalendar,
    setReminders,
    setDevices,
    setCatalog,
    online: ok => { if (!ok) setNetwork({ api: null }); },
    googleStatus: setGoogleStatus,
    screen: setScreen,
    task,
    taskDone,
    addNote: (t) => addNote(t, { fromUser: false, silent: true }),
    setNotes: (a) => setNotes(a, { emitSave: false }),
    setSkills: (a) => setSkills(a, { emitSave: false }),
    addSkill: (o) => addSkill(o, { emitSave: false }),
    skillResult: (id, ok) => skillResult(id, ok, { emitSave: false }),
    setRoutines: (a) => setRoutines(a, { emitSave: false }),
    routineResult: (id, ok) => routineResult(id, ok, { emitSave: false }),
    action: (x, ok, k) => addTL(x, ok, k, true),
    setTimeline
  });

  // 10. Direct Header Button listeners
  const btnOpenSkill = document.getElementById('btnOpenSkill');
  if (btnOpenSkill) btnOpenSkill.addEventListener('click', () => openM('mSkill'));

  const btnOpenRut = document.getElementById('btnOpenRut');
  if (btnOpenRut) btnOpenRut.addEventListener('click', () => openM('mRut'));

  const btnOpenTl = document.getElementById('btnOpenTl');
  if (btnOpenTl) btnOpenTl.addEventListener('click', () => openM('mTl'));

  const btnOpenSet = document.getElementById('btnOpenSet');
  if (btnOpenSet) btnOpenSet.addEventListener('click', () => openM('mSet'));

  const btnOpenProf = document.getElementById('btnOpenProf');
  if (btnOpenProf) btnOpenProf.addEventListener('click', () => openM('mProf'));

  const btnOpenScreen = document.getElementById('btnOpenScreen');
  if (btnOpenScreen) btnOpenScreen.addEventListener('click', toggleD);

  const btnOpenLayFromSet = document.getElementById('btnOpenLayFromSet');
  if (btnOpenLayFromSet) btnOpenLayFromSet.addEventListener('click', () => openM('mLay'));

  const btnOpenProfFromSet = document.getElementById('btnOpenProfFromSet');
  if (btnOpenProfFromSet) btnOpenProfFromSet.addEventListener('click', () => openM('mProf'));

  const btnSaveSet = document.getElementById('btnSaveSet');
  if (btnSaveSet) {
    btnSaveSet.addEventListener('click', async () => {
      if (await saveSettingsConfirmed()) closeM();
    });
  }

  const btnSaveProf = document.getElementById('btnSaveProf');
  if (btnSaveProf) {
    btnSaveProf.addEventListener('click', async () => {
      if (await saveSettingsConfirmed()) closeM();
    });
  }

  // Restart & Shutdown
  ['restart', 'restartApp'].forEach(id => {
    const restart = document.getElementById(id);
    if (!restart) return;
    restart.addEventListener('click', async () => {
      if (isBackendAvailable()) {
        restart.disabled = true;
        await emit('restart');
        restart.disabled = false;
      } else { emit('restart'); start(); }
    });
  });

  const shut = document.getElementById('shut');
  if (shut) {
    shut.addEventListener('click', shutdownApplication);
  }

  // Global key bindings
  window.addEventListener('keydown', e => {
    if (e.key === 'F11') {
      // It also works when the text field is in focus; Holding down the key does not double-switch.
      e.preventDefault();
      if (e.repeat) return;
      if (isBackendAvailable()) emit('fullscreen');
      else {
        const operation = document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
        operation.catch(error => addLog('Fullscreen failed: ' + sanitizeError(error), true));
      }
      return;
    }
    if (e.key === 'Escape') { closeM(); return; }
    if (/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;

  });

  // Start clock and start app
  tick();
  setInterval(() => {tick(); void refreshSystem(); void refreshMedia(); void refreshWeather(); void refreshTaskPermissions(); void refreshWorkflows();}, 1000);
  start();
});
