import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import type { UnrepliedItem } from '@/types';

export function useUnrepliedItems() {
  return useQuery<UnrepliedItem[]>({
    queryKey: ['unreplied'],
    queryFn: () => apiClient.get<UnrepliedItem[]>('/api/unreplied'),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCompleteUnreplied() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.patch<UnrepliedItem>(`/api/unreplied/${id}/complete`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unreplied'] });
    },
  });
}
