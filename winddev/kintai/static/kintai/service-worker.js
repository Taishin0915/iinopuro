// キャッシュ名（バージョン管理しやすいようにする）
const CACHE_NAME = 'kintai-cache-v1';

// キャッシュするリソース一覧
const urlsToCache = [
  '/',
  '/kintai/login/',
  '/static/kintai/style.css',
  '/static/kintai/icons/icon-192x192.png',
  '/static/kintai/icons/icon-512x512.png',
];

// インストールイベント
self.addEventListener('install', (event) => {
  console.log('Service Worker: インストール中...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('キャッシュ登録:', urlsToCache);
      return cache.addAll(urlsToCache);
    })
  );
});

// 有効化イベント
self.addEventListener('activate', (event) => {
  console.log('Service Worker: 有効化');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
});

// fetch イベント（オフライン対応）
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      // キャッシュがあれば返す、なければネットワークから取得
      return response || fetch(event.request);
    })
  );
});