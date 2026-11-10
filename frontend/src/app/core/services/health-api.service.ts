import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { HealthResponse } from '../models';

/** Talks to `GET /api/v1/health/`. */
@Injectable({ providedIn: 'root' })
export class HealthApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  check(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/health/`);
  }
}
