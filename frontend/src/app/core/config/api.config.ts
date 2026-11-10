import { InjectionToken } from '@angular/core';

/** Base URL of the Django REST API (version 1). Must match the backend CORS allow-list. */
export const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1';

/** Override in `app.config.ts` (or in tests) to point the app at a different backend. */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  providedIn: 'root',
  factory: () => DEFAULT_API_BASE_URL,
});
