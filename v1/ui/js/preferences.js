/** UI tercihlerinin tek bellek nesnesi ve sıfırdan varsayılanları.
 * Kaydetme/doğrulama settings.js, cihaz I/O devices.js sorumluluğundadır. */
export function defaultInterfaceSettings() {
  // Her çağrıda yeni nesne: colors gibi değişebilir alanlar varsayılanı kirletmesin.
  return { theme: '#a78bfa', colors: {}, sfx: true, vol: 0.8, wake: 50, sleepDelay: 10,
    noise: 420, onTop: false, cmp: 'auto', tab: 'theme', layout: null };
}

export const store = { ...defaultInterfaceSettings(), devs: {}, prof: {}, conn: {} };

