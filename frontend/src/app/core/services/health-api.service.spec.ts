import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { API_BASE_URL, DEFAULT_API_BASE_URL } from '../config/api.config';
import { HealthApiService } from './health-api.service';

describe('HealthApiService', () => {
  let service: HealthApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(HealthApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('defaults to the local Django development server', () => {
    expect(TestBed.inject(API_BASE_URL)).toBe(DEFAULT_API_BASE_URL);
    expect(DEFAULT_API_BASE_URL).toBe('http://localhost:8000/api/v1');
  });

  it('requests GET /health/ under the versioned base URL', () => {
    let result: unknown;
    service.check().subscribe((response) => (result = response));

    const request = httpMock.expectOne(`${DEFAULT_API_BASE_URL}/health/`);
    expect(request.request.method).toBe('GET');
    request.flush({ status: 'ok', service: 'chessboard-robot-navigation-api', api_version: 'v1' });

    expect(result).toEqual({
      status: 'ok',
      service: 'chessboard-robot-navigation-api',
      api_version: 'v1',
    });
  });
});
