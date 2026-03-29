import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import { useAuthStore } from '@/stores/authStore';
import type { CalendarEvent } from '@/types';

function useUserId() {
  return useAuthStore((s) => s.user?.lineUserId ?? s.user?.id ?? '');
}

export function useTodaySchedule() {
  const userId = useUserId();
  const today = new Date().toISOString().slice(0, 10);
  return useQuery<CalendarEvent[]>({
    queryKey: ['schedule', 'today', userId],
    queryFn: () => apiClient.get<CalendarEvent[]>(`/api/schedule?user_id=${userId}&date_from=${today}&date_to=${today}`),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useScheduleByDate(date: string) {
  const userId = useUserId();
  return useQuery<CalendarEvent[]>({
    queryKey: ['schedule', date, userId],
    queryFn: () => apiClient.get<CalendarEvent[]>(`/api/schedule?user_id=${userId}&date_from=${date}&date_to=${date}`),
    enabled: !!date && !!userId,
  });
}
