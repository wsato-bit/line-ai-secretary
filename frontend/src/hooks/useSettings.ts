import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import type { NotificationSetting, EventColorRule } from '@/types';

export function useNotificationSettings() {
  return useQuery<NotificationSetting>({
    queryKey: ['settings', 'notifications'],
    queryFn: () => apiClient.get<NotificationSetting>('/api/settings/notifications'),
  });
}

export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<NotificationSetting>) =>
      apiClient.patch<NotificationSetting>('/api/settings/notifications', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'notifications'] });
    },
  });
}

export function useEventColorRules() {
  return useQuery<EventColorRule[]>({
    queryKey: ['settings', 'colorRules'],
    queryFn: () => apiClient.get<EventColorRule[]>('/api/settings/color-rules'),
  });
}

export function useUpdateEventColorRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<EventColorRule> & { id: string }) =>
      apiClient.patch<EventColorRule>(`/api/settings/color-rules/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'colorRules'] });
    },
  });
}

export function useCreateEventColorRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<EventColorRule, 'id'>) =>
      apiClient.post<EventColorRule>('/api/settings/color-rules', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'colorRules'] });
    },
  });
}

export function useDeleteEventColorRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.delete<void>(`/api/settings/color-rules/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'colorRules'] });
    },
  });
}

interface OAuthStatus {
  connected: boolean;
  email?: string;
}

export function useGmailOAuthStatus() {
  return useQuery<OAuthStatus>({
    queryKey: ['settings', 'oauth', 'gmail'],
    queryFn: () => apiClient.get<OAuthStatus>('/api/settings/oauth/gmail/status'),
  });
}

export function useCalendarOAuthStatus() {
  return useQuery<OAuthStatus>({
    queryKey: ['settings', 'oauth', 'calendar'],
    queryFn: () => apiClient.get<OAuthStatus>('/api/settings/oauth/calendar/status'),
  });
}

export function useDisconnectOAuth() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (provider: 'gmail' | 'calendar') =>
      apiClient.post<void>(`/api/settings/oauth/${provider}/disconnect`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'oauth'] });
    },
  });
}
