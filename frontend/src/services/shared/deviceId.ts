import { generateRequestId } from './requestId';

const DEVICE_ID_KEY = 'giq_device_id';

/**
 * Reads the device ID from localStorage, creating and storing one if absent.
 */
export function getDeviceId(): string {
  let id = localStorage.getItem(DEVICE_ID_KEY);
  if (!id) {
    id = generateRequestId();
    localStorage.setItem(DEVICE_ID_KEY, id);
  }
  return id;
}

/**
 * Clears and regenerates the device ID (e.g., for logout flows).
 */
export function resetDeviceId(): void {
  localStorage.removeItem(DEVICE_ID_KEY);
  getDeviceId();
}
