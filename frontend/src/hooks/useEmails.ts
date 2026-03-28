import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import type { EmailSummary, EmailFilter } from '@/types';

export function useImportantEmails() {
  return useQuery<EmailSummary[]>({
    queryKey: ['emails', 'important'],
    queryFn: () => apiClient.get<EmailSummary[]>('/api/emails/important'),
    staleTime: 5 * 60 * 1000,
  });
}

export function useEmailFilters() {
  return useQuery<EmailFilter[]>({
    queryKey: ['emails', 'filters'],
    queryFn: () => apiClient.get<EmailFilter[]>('/api/emails/filters'),
  });
}

export function useCreateEmailFilter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (filter: Omit<EmailFilter, 'id'>) =>
      apiClient.post<EmailFilter>('/api/emails/filters', filter),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails', 'filters'] });
    },
  });
}

export function useDeleteEmailFilter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (filterId: string) =>
      apiClient.delete<void>(`/api/emails/filters/${filterId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails', 'filters'] });
    },
  });
}
