import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import { useAuthStore } from '@/stores/authStore';
import type { EmailSummary, EmailFilter } from '@/types';

function useUserId() {
  return useAuthStore((s) => s.user?.lineUserId ?? s.user?.id ?? '');
}

export function useImportantEmails() {
  const userId = useUserId();
  return useQuery<EmailSummary[]>({
    queryKey: ['emails', 'important', userId],
    queryFn: () => apiClient.get<EmailSummary[]>(`/api/emails?user_id=${userId}&category=important`),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useEmailFilters() {
  const userId = useUserId();
  return useQuery<EmailFilter[]>({
    queryKey: ['emails', 'filters', userId],
    queryFn: () => apiClient.get<EmailFilter[]>(`/api/emails/filters?user_id=${userId}`),
    enabled: !!userId,
  });
}

export function useCreateEmailFilter() {
  const queryClient = useQueryClient();
  const userId = useUserId();
  return useMutation({
    mutationFn: (filter: Omit<EmailFilter, 'id'>) =>
      apiClient.post<EmailFilter>(`/api/emails/filters?user_id=${userId}`, filter),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails', 'filters'] });
    },
  });
}

export function useDeleteEmailFilter() {
  const queryClient = useQueryClient();
  const userId = useUserId();
  return useMutation({
    mutationFn: (filterId: string) =>
      apiClient.delete<void>(`/api/emails/filters/${filterId}?user_id=${userId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails', 'filters'] });
    },
  });
}
