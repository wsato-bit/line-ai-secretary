import { useState, useCallback } from 'react';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Drawer,
  IconButton,
  InputAdornment,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import {
  Search as SearchIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Block as BlockIcon,
  CheckCircle as EnableIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import type { UserStatus } from '@/types';
import { useAuthStore } from '@/stores/authStore';
import {
  useUsers,
  useUserDetail,
  useApproveUser,
  useRejectUser,
  useDisableUser,
  useEnableUser,
} from '@/hooks/useAdmin';

const LINE_GREEN = '#06C755';

const STATUS_CONFIG: Record<UserStatus, { label: string; color: 'warning' | 'success' | 'error' | 'default' }> = {
  pending: { label: '承認待ち', color: 'warning' },
  approved: { label: '有効', color: 'success' },
  rejected: { label: '却下', color: 'error' },
  disabled: { label: '無効', color: 'default' },
};

function StatusChip({ status }: { status: UserStatus }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, color: 'default' as const };
  return <Chip label={cfg.label} color={cfg.color} size="small" />;
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ─── Pending Applications Tab ─────────────────────────────────

function PendingApplications() {
  const { data: users = [], isLoading } = useUsers('pending');
  const approveMutation = useApproveUser();
  const rejectMutation = useRejectUser();
  const [rejectTarget, setRejectTarget] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const handleApprove = useCallback((userId: string) => {
    approveMutation.mutate(userId);
  }, [approveMutation]);

  const handleRejectOpen = useCallback((userId: string) => {
    setRejectTarget(userId);
    setRejectReason('');
  }, []);

  const handleRejectConfirm = useCallback(() => {
    if (!rejectTarget) return;
    rejectMutation.mutate({ userId: rejectTarget, reason: rejectReason || undefined });
    setRejectTarget(null);
    setRejectReason('');
  }, [rejectTarget, rejectReason, rejectMutation]);

  if (isLoading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="text.secondary">読み込み中...</Typography>
      </Box>
    );
  }

  if (users.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography color="text.secondary">承認待ちの申請はありません</Typography>
      </Box>
    );
  }

  return (
    <>
      <Stack spacing={2} sx={{ p: 2 }}>
        {users.map((user) => (
          <Card key={user.id} variant="outlined">
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar
                src={user.linePictureUrl}
                sx={{ width: 56, height: 56, bgcolor: LINE_GREEN }}
              >
                {user.lineDisplayName?.charAt(0) ?? '?'}
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {user.lineDisplayName || '名前未設定'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  LINE ID: {user.lineUserId}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  申請日: {formatDate(user.appliedAt ?? user.createdAt)}
                </Typography>
              </Box>
              <StatusChip status={user.status} />
            </CardContent>
            <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2 }}>
              <Button
                variant="contained"
                startIcon={<CheckIcon />}
                onClick={() => handleApprove(user.id)}
                disabled={approveMutation.isPending}
                sx={{ bgcolor: LINE_GREEN, '&:hover': { bgcolor: '#05a847' } }}
              >
                承認
              </Button>
              <Button
                variant="outlined"
                color="error"
                startIcon={<CloseIcon />}
                onClick={() => handleRejectOpen(user.id)}
                disabled={rejectMutation.isPending}
              >
                却下
              </Button>
            </CardActions>
          </Card>
        ))}
      </Stack>

      <Dialog open={!!rejectTarget} onClose={() => setRejectTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>申請を却下</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            却下理由を入力してください（任意）。ユーザーにLINE通知が送信されます。
          </Typography>
          <TextField
            autoFocus
            fullWidth
            multiline
            rows={3}
            label="却下理由"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="例: 現在新規登録を制限しています"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectTarget(null)}>キャンセル</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleRejectConfirm}
            disabled={rejectMutation.isPending}
          >
            却下する
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

// ─── Registered Users Tab ─────────────────────────────────────

function RegisteredUsers() {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [detailUserId, setDetailUserId] = useState<string | null>(null);
  const { data: users = [], isLoading } = useUsers(undefined, debouncedSearch || undefined);
  const { data: userDetail } = useUserDetail(detailUserId);
  const disableMutation = useDisableUser();
  const enableMutation = useEnableUser();

  const handleSearchChange = useCallback((value: string) => {
    setSearch(value);
    const timeout = setTimeout(() => setDebouncedSearch(value), 400);
    return () => clearTimeout(timeout);
  }, []);

  const handleDisable = useCallback((userId: string) => {
    disableMutation.mutate(userId);
  }, [disableMutation]);

  const handleEnable = useCallback((userId: string) => {
    enableMutation.mutate(userId);
  }, [enableMutation]);

  return (
    <>
      <Box sx={{ p: 2 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="ユーザー名またはLINE IDで検索"
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            },
          }}
          sx={{ mb: 2 }}
        />
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>ユーザー</TableCell>
                <TableCell>ステータス</TableCell>
                <TableCell>ロール</TableCell>
                <TableCell>最終アクティブ</TableCell>
                <TableCell align="right">操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography color="text.secondary">読み込み中...</Typography>
                  </TableCell>
                </TableRow>
              ) : users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography color="text.secondary">該当するユーザーがいません</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                users.map((user) => (
                  <TableRow key={user.id} hover>
                    <TableCell>
                      <Stack direction="row" alignItems="center" spacing={1.5}>
                        <Avatar
                          src={user.linePictureUrl}
                          sx={{ width: 32, height: 32, bgcolor: LINE_GREEN, fontSize: 14 }}
                        >
                          {user.lineDisplayName?.charAt(0) ?? '?'}
                        </Avatar>
                        <Typography variant="body2">
                          {user.lineDisplayName || '名前未設定'}
                        </Typography>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <StatusChip status={user.status} />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{user.role}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {formatDate(user.lastActiveAt)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                        <IconButton
                          size="small"
                          title="詳細"
                          onClick={() => setDetailUserId(user.id)}
                        >
                          <InfoIcon fontSize="small" />
                        </IconButton>
                        {user.status === 'approved' && (
                          <IconButton
                            size="small"
                            title="無効化"
                            color="error"
                            onClick={() => handleDisable(user.id)}
                            disabled={disableMutation.isPending}
                          >
                            <BlockIcon fontSize="small" />
                          </IconButton>
                        )}
                        {user.status === 'disabled' && (
                          <IconButton
                            size="small"
                            title="有効化"
                            color="success"
                            onClick={() => handleEnable(user.id)}
                            disabled={enableMutation.isPending}
                          >
                            <EnableIcon fontSize="small" />
                          </IconButton>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      <Drawer
        anchor="right"
        open={!!detailUserId}
        onClose={() => setDetailUserId(null)}
        PaperProps={{ sx: { width: { xs: '100%', sm: 400 } } }}
      >
        {userDetail && (
          <Box sx={{ p: 3 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
              <Typography variant="h6" fontWeight="bold">ユーザー詳細</Typography>
              <IconButton onClick={() => setDetailUserId(null)}>
                <CloseIcon />
              </IconButton>
            </Stack>
            <Stack alignItems="center" spacing={1} sx={{ mb: 3 }}>
              <Avatar
                src={userDetail.linePictureUrl}
                sx={{ width: 80, height: 80, bgcolor: LINE_GREEN, fontSize: 32 }}
              >
                {userDetail.lineDisplayName?.charAt(0) ?? '?'}
              </Avatar>
              <Typography variant="h6">
                {userDetail.lineDisplayName || '名前未設定'}
              </Typography>
              <StatusChip status={userDetail.status} />
            </Stack>
            <Stack spacing={1.5}>
              <DetailRow label="ユーザーID" value={userDetail.id} />
              <DetailRow label="LINE User ID" value={userDetail.lineUserId} />
              <DetailRow label="ロール" value={userDetail.role} />
              <DetailRow label="申請日" value={formatDate(userDetail.appliedAt ?? userDetail.createdAt)} />
              <DetailRow label="承認日" value={formatDate(userDetail.approvedAt)} />
              <DetailRow label="最終アクティブ" value={formatDate(userDetail.lastActiveAt)} />
              <DetailRow label="メモ件数" value={String(userDetail.memoCount)} />
              {userDetail.rejectionReason && (
                <DetailRow label="却下理由" value={userDetail.rejectionReason} />
              )}
            </Stack>
          </Box>
        )}
      </Drawer>
    </>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>{value}</Typography>
    </Box>
  );
}

// ─── Main Page ────────────────────────────────────────────────

function AdminUsersPage() {
  const [tabIndex, setTabIndex] = useState(0);
  const currentUser = useAuthStore((s) => s.user);

  if (currentUser?.role !== 'admin') {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="error">
          アクセス権限がありません
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          この画面は管理者のみ利用可能です。
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 1000, mx: 'auto' }}>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        ユーザー管理
      </Typography>

      <Tabs
        value={tabIndex}
        onChange={(_, v) => setTabIndex(v)}
        sx={{
          mb: 2,
          '& .MuiTab-root': { fontWeight: 'bold' },
          '& .Mui-selected': { color: LINE_GREEN },
          '& .MuiTabs-indicator': { bgcolor: LINE_GREEN },
        }}
      >
        <Tab label="申請一覧" />
        <Tab label="登録ユーザー" />
      </Tabs>

      {tabIndex === 0 && <PendingApplications />}
      {tabIndex === 1 && <RegisteredUsers />}
    </Box>
  );
}

export default AdminUsersPage;
