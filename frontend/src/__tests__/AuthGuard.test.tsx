/**
 * AuthGuard component tests.
 *
 * Tests redirect behavior when not authenticated and rendering when authenticated.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

// Mock the auth store before importing AuthGuard
const mockAuthState = {
  isAuthenticated: false,
  isLoading: false,
  user: null,
  accessToken: null,
  setUser: vi.fn(),
  setAccessToken: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  setLoading: vi.fn(),
};

vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(() => mockAuthState),
}));

import AuthGuard from '@/components/AuthGuard';

function renderWithRouter(
  initialPath: string,
  children: React.ReactNode,
) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
        <Route
          path="/"
          element={<AuthGuard>{children}</AuthGuard>}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe('AuthGuard', () => {
  beforeEach(() => {
    mockAuthState.isAuthenticated = false;
    mockAuthState.isLoading = false;
  });

  it('redirects to /login when not authenticated', () => {
    renderWithRouter('/', <div>Protected Content</div>);

    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('renders children when authenticated', () => {
    mockAuthState.isAuthenticated = true;

    renderWithRouter('/', <div>Protected Content</div>);

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('shows loading spinner while isLoading is true', () => {
    mockAuthState.isLoading = true;

    renderWithRouter('/', <div>Protected Content</div>);

    // CircularProgress renders a role="progressbar" element
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});
