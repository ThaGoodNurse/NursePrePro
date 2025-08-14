const CACHE_NAME = 'nurseprep-pro-v1.0.0';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icon-192x192.png',
  '/icon-512x512.png'
];

// Install Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      }
    )
  );
});

// Activate Service Worker
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background Sync for offline quiz submissions
self.addEventListener('sync', (event) => {
  if (event.tag === 'quiz-submission') {
    event.waitUntil(syncQuizSubmissions());
  }
});

// Push notifications for study reminders
self.addEventListener('push', (event) => {
  const options = {
    body: 'Time for your daily NCLEX-RN practice session!',
    icon: '/icon-192x192.png',
    badge: '/icon-96x96.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '2'
    },
    actions: [
      {
        action: 'explore',
        title: 'Start Studying',
        icon: '/icon-study-24x24.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/icon-close-24x24.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('NursePrep Pro Study Reminder', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Sync quiz submissions when back online
async function syncQuizSubmissions() {
  try {
    // Get pending quiz submissions from IndexedDB
    const pendingSubmissions = await getPendingSubmissions();
    
    for (const submission of pendingSubmissions) {
      try {
        const response = await fetch('/api/quiz/submit', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submission.data)
        });
        
        if (response.ok) {
          // Remove from pending submissions
          await removePendingSubmission(submission.id);
        }
      } catch (error) {
        console.error('Failed to sync quiz submission:', error);
      }
    }
  } catch (error) {
    console.error('Error during background sync:', error);
  }
}

// Placeholder functions for IndexedDB operations
async function getPendingSubmissions() {
  // Implementation would use IndexedDB to retrieve pending submissions
  return [];
}

async function removePendingSubmission(id) {
  // Implementation would remove the submission from IndexedDB
  console.log('Removing pending submission:', id);
}