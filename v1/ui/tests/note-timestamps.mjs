/** Try preserving note date in snapshot/backup normalization without DOM.
 * Application dependency is not added. Broken date, partially applying import candidate
 * is instead rejected entirely; Older undated records remain valid.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
const source = fs.readFileSync(new URL('../js/schema.js', import.meta.url), 'utf8');
const { validNoteCreatedAt, validateAndNormalizeSnapshot } = await import(
  'data:text/javascript;base64,' + Buffer.from(source).toString('base64'));

const dated = { id: 'stable-id', t: 'Same note', d: 0, created_at: '2024-02-29T12:34:56.789Z' };
for (const record of [dated, { t: 'Legacy', d: 0 }, { ...dated, created_at: null }]) {
  const checked = validateAndNormalizeSnapshot({ notes: [record] });
  assert.equal(checked.ok, true);
  assert.deepEqual(checked.candidate.notes, [record]);
}
for (const value of ['yesterday', '2026-02-30T12:00:00.000Z', '0000-01-01T00:00:00.000Z',
  '2026-10-22T12:00:00.000+03:00', '2026-10-22T12:00:00', 1, {}, []]) {
  assert.equal(validNoteCreatedAt(value), false);
  const result = validateAndNormalizeSnapshot({ theme: '#000000', notes: [{ ...dated, created_at: value }] });
  assert.equal(result.ok, false);
  assert.equal(result.candidate, undefined);
}
console.log('PASS note creation time: preservation, legacy compatibility and atomic invalid-import rejection');
