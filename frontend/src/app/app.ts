import { toSignal } from '@angular/core/rxjs-interop';
import { Component, computed, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { catchError, map, of } from 'rxjs';

import { HealthApiService } from './core/services/health-api.service';

type BackendStatus = 'checking' | 'online' | 'offline';

const STATUS_LABELS: Record<BackendStatus, string> = {
  checking: 'Checking backend…',
  online: 'Backend connected',
  offline: 'Backend unreachable. Start the Django server on port 8000.',
};

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly healthApi = inject(HealthApiService);

  protected readonly backendStatus = toSignal(
    this.healthApi.check().pipe(
      map((): BackendStatus => 'online'),
      catchError(() => of<BackendStatus>('offline')),
    ),
    { initialValue: 'checking' as BackendStatus },
  );

  protected readonly statusLabel = computed(() => STATUS_LABELS[this.backendStatus()]);
}
