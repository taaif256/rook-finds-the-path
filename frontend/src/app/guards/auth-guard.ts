import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from '../core/services/auth';

/** Lets signed-in users through and sends everyone else to the login page. */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isLoggedIn()) {
    return true;
  }

  // Drop an expired or unreadable token so it is not attached to later requests.
  auth.logout();
  return router.createUrlTree(['/login']);
};