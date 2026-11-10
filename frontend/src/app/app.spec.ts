import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { App } from './app';
import { DEFAULT_API_BASE_URL } from './core/config/api.config';

describe('App', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  function render() {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const element = fixture.nativeElement as HTMLElement;
    return { fixture, element };
  }

  it('renders the application title', () => {
    const { element } = render();
    expect(element.querySelector('h1')?.textContent).toContain('Chessboard Robot Navigation Visualizer');
    httpMock.expectOne(`${DEFAULT_API_BASE_URL}/health/`);
  });

  it('shows a connected status when the health check succeeds', async () => {
    const { fixture, element } = render();
    httpMock
      .expectOne(`${DEFAULT_API_BASE_URL}/health/`)
      .flush({ status: 'ok', service: 'chessboard-robot-navigation-api', api_version: 'v1' });
    await fixture.whenStable();
    fixture.detectChanges();

    const status = element.querySelector('.api-status');
    expect(status?.textContent).toContain('Backend connected');
    expect(status?.getAttribute('data-status')).toBe('online');
  });

  it('tells the user how to recover when the backend is unreachable', async () => {
    const { fixture, element } = render();
    httpMock
      .expectOne(`${DEFAULT_API_BASE_URL}/health/`)
      .error(new ProgressEvent('error'), { status: 0 });
    await fixture.whenStable();
    fixture.detectChanges();

    const status = element.querySelector('.api-status');
    expect(status?.textContent).toContain('Backend unreachable');
    expect(status?.getAttribute('data-status')).toBe('offline');
  });
});
