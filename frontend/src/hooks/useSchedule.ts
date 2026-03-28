import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import type { CalendarEvent } from '@/types';

export function useTodaySchedule() {
  return useQuery<CalendarEvent[]>({
    queryKey: ['schedule', 'today'],
    queryFn: () => apiClient.get<CalendarEvent[]>('/api/schedule/today'),
    staleTime: 5 * 60 * 1000,
  });
}

export function useScheduleByDate(date: string) {
  return useQuery<CalendarEvent[]>({
    queryKey: ['schedule', date],
    queryFn: () => apiClient.get<CalendarEvent[]>(`/api/schedule?date=${date}`),
    enabled: !!date,
  });
}
