import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import type { Memo, MemoCategory } from '@/types';

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
  const { categoryId, search, limit = 20 } = params;
  return useInfiniteQuery<MemosResponse>({
    queryKey: ['memos', { categoryId, search }],
    queryFn: ({ pageParam }) => {
      const qs = new URLSearchParams();
      if (categoryId) qs.set('category_id', categoryId);
      if (search) qs.set('search', search);
      qs.set('limit', String(limit));
      if (pageParam) qs.set('cursor', pageParam as string);
      return apiClient.get<MemosResponse>(`/api/memos?${qs}`);
    },
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    staleTime: 2 * 60 * 1000,
  });
}

export function useRecentMemos(limit = 5) {
  return useQuery<Memo[]>({
    queryKey: ['memos', 'recent', limit],
    queryFn: () => apiClient.get<Memo[]>(`/api/memos/recent?limit=${limit}`),
    staleTime: 2 * 60 * 1000,
  });
}

export function useMemoCategories() {
  return useQuery<MemoCategory[]>({
    queryKey: ['memos', 'categories'],
    queryFn: () => apiClient.get<MemoCategory[]>('/api/memos/categories'),
  });
}

export function useCreateMemoCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string }) =>
      apiClient.post<MemoCategory>('/api/memos/categories', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos', 'categories'] });
    },
  });
}

export function useUpdateMemoCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; name?: string; sortOrder?: number }) =>
      apiClient.patch<MemoCategory>(`/api/memos/categories/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos', 'categories'] });
    },
  });
}

export function useDeleteMemoCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.delete<void>(`/api/memos/categories/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos', 'categories'] });
    },
  });
}

export function useUpdateMemoTags() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, tags }: { id: string; tags: string[] }) =>
      apiClient.patch<Memo>(`/api/memos/${id}`, { tags }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos'] });
    },
  });
}

export function useDeleteMemo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.delete<void>(`/api/memos/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos'] });
    },
  });
}
