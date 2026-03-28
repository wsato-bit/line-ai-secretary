/**
 * E2E tests for the workspace page.
 *
 * Tests that main dashboard sections render correctly.
 * These tests mock authentication state via localStorage injection.
 */

import { test, expect } from '@playwright/test';

// Helper to inject auth state into localStorage before page load
async function loginAsTestUser(page: import('@playwright/test').Page) {
  await page.addInitScript(() => {
    const authState = {
      state: {
        user: {
          id: 'test-user-id',
          lineUserId: 'U_test_user',
          lineDisplayName: 'Test User',
          role: 'user',
          status: 'approved',
          createdAt: '2026-01-01T00:00:00Z',
        },
        accessToken: 'mock_access_token',
        isAuthenticated: true,
      },
      version: 0,
    };
    localStorage.setItem('line-ai-secretary-auth', JSON.stringify(authState));
  });
}

test.describe('Workspace Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('workspace page renders section titles', async ({ page }) => {
    await page.goto('/');

    // Main title
    await expect(page.getByText('ワークスペース')).toBeVisible();
  });

  test('schedule section is present', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByText('今日の予定')).toBeVisible();
  });

  test('email section is present', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByText('未読重要メール')).toBeVisible();
  });

  test('unreplied section is present', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByText('LINE未返信')).toBeVisible();
  });

  test('recent memos section is present', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByText('最近のメモ')).toBeVisible();
  });
});
