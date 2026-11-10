import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, throwError } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ApiErrorResponse, PathfindingRequest, PathfindingResponse } from '../models';

/** Every failure of a search request, in one shape with a message fit to show the user. */
export class PathfindingApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    /** Dotted request path to messages, e.g. `grid.rows`. Empty when the error is not about a field. */
    readonly fieldErrors: Record<string, string[]> = {},
  ) {
    super(message);
    this.name = 'PathfindingApiError';
  }
}

function isApiErrorResponse(body: unknown): body is ApiErrorResponse {
  return typeof body === 'object' && body !== null && (body as ApiErrorResponse).status === 'error';
}

function toApiError(failure: HttpErrorResponse): PathfindingApiError {
  if (failure.status === 0) {
    return new PathfindingApiError('Cannot reach the backend. Start the Django server on port 8000 and try again.', 0);
  }
  if (isApiErrorResponse(failure.error)) {
    const { message, errors } = failure.error;
    const details = Object.entries(errors ?? {}).map(([field, messages]) => `${field}: ${messages.join(' ')}`);
    return new PathfindingApiError([message, ...details].join(' '), failure.status, errors ?? {});
  }
  return new PathfindingApiError(`The server returned an unexpected error (${failure.status}).`, failure.status);
}

/** Talks to `POST /api/v1/pathfinding/run/`. */
@Injectable({ providedIn: 'root' })
export class PathfindingApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  run(request: PathfindingRequest): Observable<PathfindingResponse> {
    return this.http
      .post<PathfindingResponse>(`${this.baseUrl}/pathfinding/run/`, request)
      .pipe(catchError((failure: HttpErrorResponse) => throwError(() => toApiError(failure))));
  }
}
