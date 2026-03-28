import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import type { User, UserStatus } from '@/types';

interface UserDetail extends User {
  memoCount: number;
  rejectionReason?: string;
}

interface AdminUserResponse {
  id: string;
  line_user_id: string;
  line_display_name: string | null;
  line_picture_url: string | null;
  role: string;
  status: string;
  applied_at: string | null;
  approved_at: string | null;
  rejection_reason: string | null;
  last_active_at: string | null;
  created_at: string;
  memo_count?: number;
}

function mapUser(raw: AdminUserResponse): User {
  return {
    id: raw.id,
    lineUserId: raw.line_user_id,
    lineDisplayName: raw.line_display_name ?? '',
    linePictureUrl: raw.line_picture_url ?? undefined,
    role: raw.role as User['role'],
    status: raw.status as UserStatus,
    appliedAt: raw.applied_at ?? undefined,
    approvedAt: raw.approved_at ?? undefined,
    lastActiveAt: raw.last_active_at ?? undefined,
    createdAt: raw.created_at,
  };
}

function mapUserDetail(raw: AdminUserResponse): UserDetail {
  return {
    ...mapUser(raw),
    memoCount: raw.memo_count ?? 0,
    rejectionReason: raw.rejection_reason ?? undefined,
  };
}

export function useUsers(status?: string, search?: string) {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (search) params.set('search', search);
  const qs = params.toString();
  const endpoint = `/api/admin/users${qs ? `?${qs}` : ''}`;

  return useQuery<User[]>({
    queryKey: ['admin', 'users', status, search],
    queryFn: async () => {
      const data = await apiClient.get<AdminUserResponse[]>(endpoint);
      return data.map(mapUser);
    },
    staleTime: 30 * 1000,
  });
}

export function useUserDetail(userId: string | null) {
  return useQuery<UserDetail | null>({
    queryKey: ['admin', 'users', userId],
    queryFn: async () => {
      if (!userId) return null;
      const data = await apiClient.get<AdminUserResponse>(`/api/admin/users/${userId}`);
      return mapUserDetail(data);
    },
    enabled: !!userId,
  });
}

export function useApproveUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) =>
      apiClient.post<AdminUserResponse>(`/api/admin/users/${userId}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useRejectUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, reason }: { userId: string; reason?: string }) =>
      apiClient.post<AdminUserResponse>(`/api/admin/users/${userId}/reject`, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useDisableUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) =>
      apiClient.post<AdminUserResponse>(`/api/admin/users/${userId}/disable`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useEnableUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) =>
      apiClient.post<AdminUserResponse>(`/api/admin/users/${userId}/enable`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}
