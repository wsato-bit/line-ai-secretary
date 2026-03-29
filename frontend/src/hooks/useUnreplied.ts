import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import { useAuthStore } from '@/stores/authStore';
import type { UnrepliedItem } from '@/types';

function useUserId() {
  return useAuthStore((s) => s.user?.lineUserId ?? s.user?.id ?? '');
}

export function useUnrepliedItems() {
  const userId = useUserId();
  return useQuery<UnrepliedItem[]>({
    queryKey: ['unreplied', userId],
    queryFn: () => apiClient.get<UnrepliedItem[]>(`/api/unreplied?user_id=${userId}`),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCompleteUnreplied() {
  const queryClient = useQueryClient();
  const userId = useUserId();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.put<UnrepliedItem>(`/api/unreplied/${id}/complete?user_id=${userId}`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unreplied'] });
    },
  });
}
