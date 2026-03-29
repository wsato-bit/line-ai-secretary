import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import { useAuthStore } from '@/stores/authStore';
import type { Memo, MemoCategory } from '@/types';

function useUserId() {
  return useAuthStore((s) => s.user?.lineUserId ?? s.user?.id ?? '');
}

interface MemosResponse {
  items: Memo[];
  total: number;
  nextCursor?: string;
}

interface MemosQueryParams {
  categoryId?: string;
  search?: string;
  limit?: number;
}

export function useMemos(params: MemosQueryParams = {}) {
  const userId = useUserId();
  const { categoryId, search, limit = 20 } = params;
  return useInfiniteQuery<MemosResponse>({
    queryKey: ['memos', { categoryId, search, userId }],
    queryFn: ({ pageParam }) => {
      const qs = new URLSearchParams();
      qs.set('user_id', userId);
      if (categoryId) qs.set('category_id', categoryId);
      if (search) qs.set('search', search);
      qs.set('limit', String(limit));
      if (pageParam) qs.set('cursor', pageParam as string);
      return apiClient.get<MemosResponse>(`/api/memos?${qs}`);
    },
    enabled: !!userId,
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    staleTime: 2 * 60 * 1000,
  });
}

export function useRecentMemos(limit = 5) {
  const userId = useUserId();
  return useQuery<Memo[]>({
    queryKey: ['memos', 'recent', limit, userId],
    queryFn: () => apiClient.get<Memo[]>(`/api/memos?user_id=${userId}&limit=${limit}`),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useMemoCategories() {
  const userId = useUserId();
  return useQuery<MemoCategory[]>({
    queryKey: ['memos', 'categories', userId],
    queryFn: () => apiClient.get<MemoCategory[]>(`/api/memos/categories?user_id=${userId}`),
    enabled: !!userId,
  });
}

export function useCreateMemoCategory() {
  const queryClient = useQueryClient();
  const userId = useUserId();
  return useMutation({
    mutationFn: (data: { name: string }) =>
      apiClient.post<MemoCategory>(`/api/memos/categories?user_id=${userId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos', 'categories'] });
    },
  });
}

export function useUpdateMemoCategory() {
  const queryClient = useQueryClient();
  const userId = useUserId();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; name?: string; sortOrder?: number }) =>
      apiClient.patch<MemoCategory>(`/api/memos/categories/${id}?user_id=${userId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos', 'categories'] });
    },
  });
}

export function useDeleteMemoCategory() {
  const queryClient = useQueryClient();
  const userId = useUserId();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.delete<void>(`/api/memos/categories/${id}?user_id=${userId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos', 'categories'] });
    },
  });
}

export function useUpdateMemoTags() {
  const queryClient = useQueryClient();
  const userId = useUserId();
  return useMutation({
    mutationFn: ({ id, tags }: { id: string; tags: string[] }) =>
      apiClient.patch<Memo>(`/api/memos/${id}?user_id=${userId}`, { tags }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos'] });
    },
  });
}

export function useDeleteMemo() {
  const queryClient = useQueryClient();
  const userId = useUserId();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.delete<void>(`/api/memos/${id}?user_id=${userId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos'] });
    },
  });
}
