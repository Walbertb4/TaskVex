/** Browser persistence. Failures are visible; caller decides whether to continue. */
import { logBridgeError } from './api.js';

export function writeStoredJSON(key, value) {
  try {
    const serialized = JSON.stringify(value);
    localStorage.setItem(key, serialized);
    return true;
  } catch (error) {
    logBridgeError('local storage write', error);
    return false;
  }
}

export function removeStoredKeys(...keys) {
  try {
    keys.forEach(key => localStorage.removeItem(key));
    return true;
  } catch (error) {
    logBridgeError('local storage reset', error);
    return false;
  }
}
