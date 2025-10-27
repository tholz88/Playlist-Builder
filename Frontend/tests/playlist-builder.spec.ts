import { test, expect } from '@playwright/test';

const APP_URL = 'http://localhost:5173';  // Dein Frontend
const API_URL = 'http://127.0.0.1:5050';  // Dein Backend oder Mock

test.describe('🎵 Playlist-Builder Functional Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL);
  });

  // -------------------------------------------------
  // 1️⃣ Suchfeld-Interaktion
  // -------------------------------------------------
  test('zeigt Fehlermeldung bei leerer Suche', async ({ page }) => {
    await page.click('#btn-search');
    await expect(page.locator('body')).toContainText('Bitte Suchbegriff eingeben.');
  });

  test('führt erfolgreiche Suche aus und zeigt Ergebnisse', async ({ page }) => {
    await page.route(`${API_URL}/search`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            { id: 'song1', title: 'Numb', artist: 'Linkin Park' },
            { id: 'song2', title: 'Blinding Lights', artist: 'The Weeknd' },
          ],
        }),
      });
    });

    await page.fill('#q', 'test');
    await page.click('#btn-search');

    const results = page.locator('.song-item');
    await expect(results).toHaveCount(2);
    await expect(results.first()).toContainText('Numb');
  });

  // -------------------------------------------------
  // 2️⃣ Playlist hinzufügen / entfernen
  // -------------------------------------------------
  test('fügt Song zur Playlist hinzu', async ({ page }) => {
    // Mock /add und /playlist
    await page.route(`${API_URL}/add/song1`, route => route.fulfill({ status: 200, body: '{}' }));
    await page.route(`${API_URL}/playlist`, route =>
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          playlist: [{ id: 'song1', title: 'Numb', artist: 'Linkin Park' }],
        }),
      }),
    );

    // Simuliere Suchergebnis
    await page.evaluate(() => {
      document.querySelector('#results')!.innerHTML = `
        <article class="song-item" data-id="song1">
          <div class="meta"><div class="title">Numb</div><div class="artist">Linkin Park</div></div>
          <div class="row-actions"><button class="icon-btn action-add"><i class="fa-solid fa-plus"></i></button></div>
        </article>`;
    });

    await page.click('.action-add');
    await expect(page.locator('body')).toContainText('Titel hinzugefügt');
    await expect(page.locator('#playlist-body tr')).toHaveCount(1);
    await expect(page.locator('#playlist-body')).toContainText('Numb');
  });

  test('entfernt Song aus Playlist', async ({ page }) => {
    await page.route(`${API_URL}/remove/song1`, route => route.fulfill({ status: 200, body: '{}' }));
    await page.route(`${API_URL}/playlist`, route =>
      route.fulfill({
        status: 200,
        body: JSON.stringify({ playlist: [] }),
      }),
    );

    // Simuliere Playlist mit Song
    await page.evaluate(() => {
      document.querySelector('#playlist-body')!.innerHTML = `
        <tr data-id="song1">
          <td>1</td>
          <td><div class="title">Numb</div></td>
          <td class="col-artist"><div class="artist">Linkin Park</div></td>
          <td class="col-actions">
            <button class="icon-btn danger action-remove"><i class="fa-solid fa-trash"></i></button>
          </td>
        </tr>`;
    });

    await page.click('.action-remove');
    await expect(page.locator('body')).toContainText('Titel entfernt');
  });

  // -------------------------------------------------
  // 3️⃣ Export-Funktion (Spotify)
  // -------------------------------------------------
  test('exportiert Playlist zu Spotify', async ({ page }) => {
    await page.route(`${API_URL}/spotify/create-url?name=My%20Playlist`, route =>
      route.fulfill({
        status: 200,
        body: JSON.stringify({ url: 'https://spotify.com/authorize/test' }),
      }),
    );

    // Prompt simulieren
    page.on('dialog', dialog => dialog.accept('My Playlist'));

    const [popup] = await Promise.all([
      page.waitForEvent('popup'),
      page.click('#btn-export'),
    ]);

    await expect(popup.url()).toContain('spotify.com/authorize/test');
  });

  // -------------------------------------------------
  // 4️⃣ Tastenkürzel
  // -------------------------------------------------
  test('Shortcut "/" fokussiert das Suchfeld', async ({ page }) => {
    await page.keyboard.press('/');
    const active = await page.evaluate(() => document.activeElement?.id);
    expect(active).toBe('q');
  });

  // -------------------------------------------------
  // 5️⃣ Initialer Playlist-Load
  // -------------------------------------------------
  test('lädt leere Playlist beim Start', async ({ page }) => {
    await page.route(`${API_URL}/playlist`, route =>
      route.fulfill({
        status: 200,
        body: JSON.stringify({ playlist: [] }),
      }),
    );

    await page.reload();
    await expect(page.locator('#playlist-body')).toContainText('Noch keine Titel');
  });
});
