/** Single memory object and defaults from scratch of UI preferences.
 * Saving/verifying settings.js is the responsibility of device I/O devices.js. */
export function defaultInterfaceSettings() {
  // New object on every call: mutable fields such as colors should not pollute the default.
  return { theme: '#a78bfa', colors: {}, sfx: true, vol: 0.8, replyVolume: 1, wake: 50, sleepDelay: 10,
    noise: 420, onTop: false, cmp: 'auto', tab: 'theme', layout: null };
}

export const store = { ...defaultInterfaceSettings(), devs: {}, prof: {}, conn: {} };

