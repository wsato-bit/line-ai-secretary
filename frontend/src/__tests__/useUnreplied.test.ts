/**
 * useUnreplied hook tests.
 *
 * Tests useUnrepliedItems query and useCompleteUnreplied mutation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import type { UnrepliedItem } from '@/types';

// Mock the API client
const mockGet = vi.fn();
const mockPatch = vi.fn();

vi.mock('@/services/apiClient', () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
  },
}));

import { useUnrepliedItems, useCompleteUnreplied } from '@/hooks/useUnreplied';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

const sampleItems: UnrepliedItem[] = [
  {
    id: 'item-1',
    contactName: 'Tanaka',
    contentMemo: 'Call back',
    registeredAt: '2026-03-25T09:00:00Z',
    completedAt: undefined,
    isCompleted: false,
    daysElapsed: 3,
  },
  {
    id: 'item-2',
    contactName: 'Suzuki',
    contentMemo: undefined,
    registeredAt: '2026-03-27T09:00:00Z',
    completedAt: undefined,
    isCompleted: false,
    daysElapsed: 1,
  },
];

describe('useUnrepliedItems', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches unreplied items successfully', async () => {
    mockGet.mockResolvedValueOnce(sampleItems);

    const { result } = renderHook(() => useUnrepliedItems(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(sampleItems);
    expect(mockGet).toHaveBeenCalledWith('/api/unreplied');
  });

  it('handles fetch error', async () => {
    mockGet.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useUnrepliedItems(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useCompleteUnreplied', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('sends PATCH request to complete item', async () => {
    const completedItem: UnrepliedItem = {
      ...sampleItems[0],
      isCompleted: true,
      completedAt: '2026-03-28T10:00:00Z',
    };
    mockPatch.mockResolvedValueOnce(completedItem);

    const { result } = renderHook(() => useCompleteUnreplied(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('item-1');

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPatch).toHaveBeenCalledWith('/api/unreplied/item-1/complete', {});
  });

  it('handles mutation error', async () => {
    mockPatch.mockRejectedValueOnce(new Error('Server error'));

    const { result } = renderHook(() => useCompleteUnreplied(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('item-1');

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});
