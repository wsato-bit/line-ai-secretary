/**
 * E2E tests for the login page.
 *
 * Tests page rendering and LINE login button presence.
 */

import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('login page renders with title', async ({ page }) => {
    await page.goto('/login');

    // Should display the app name
    await expect(page.getByText('LINE AI Secretary')).toBeVisible();

    // Should display subtitle
    await expect(page.getByText('AI個人秘書サービス')).toBeVisible();
  });

  test('LINE login button exists and is clickable', async ({ page }) => {
    await page.goto('/login');

    const loginButton = page.getByRole('button', { name: /LINEでログイン/i });
    await expect(loginButton).toBeVisible();
    await expect(loginButton).toBeEnabled();
  });

  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/');

    // AuthGuard should redirect to /login
    await expect(page).toHaveURL(/\/login/);
  });

  test('login page has green LINE-branded button', async ({ page }) => {
    await page.goto('/login');

    const loginButton = page.getByRole('button', { name: /LINEでログイン/i });
    await expect(loginButton).toBeVisible();

    // Check the button has the LINE green color
    const bgColor = await loginButton.evaluate(
      (el) => getComputedStyle(el).backgroundColor,
    );
    // LINE green #06C755 => rgb(6, 199, 85)
    expect(bgColor).toContain('6, 199, 85');
  });
});
