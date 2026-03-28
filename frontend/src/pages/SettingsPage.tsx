import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  List,
  ListItem,
  ListItemSecondaryAction,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Skeleton,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LinkOffIcon from '@mui/icons-material/LinkOff';
import GoogleIcon from '@mui/icons-material/Google';
import EmailIcon from '@mui/icons-material/Email';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import {
  useNotificationSettings,
  useUpdateNotificationSettings,
  useEventColorRules,
  useCreateEventColorRule,
  useUpdateEventColorRule,
  useDeleteEventColorRule,
  useGmailOAuthStatus,
  useCalendarOAuthStatus,
  useDisconnectOAuth,
} from '@/hooks/useSettings';
import {
  useEmailFilters,
  useCreateEmailFilter,
  useDeleteEmailFilter,
} from '@/hooks/useEmails';
import { useUIStore } from '@/stores/uiStore';
import { config } from '@/config';
import type { EventColorRule, EmailFilter, EmailFilterType, EmailFilterAction, EventType, EventStatus } from '@/types';

const PRESET_INTERVALS = [5, 10, 15, 30, 60];

const EVENT_TYPE_LABELS: Record<EventType, string> = {
  business: 'ビジネス',
  private: 'プライベート',
};

const EVENT_STATUS_LABELS: Record<EventStatus, string> = {
  confirmed: '確定',
  tentative: '仮',
};

const FILTER_TYPE_LABELS: Record<EmailFilterType, string> = {
  sender: '送信者',
  domain: 'ドメイン',
  subject_pattern: '件名パターン',
};

const FILTER_ACTION_LABELS: Record<EmailFilterAction, string> = {
  important: '重要',
  exclude: '除外',
};

const COLOR_OPTIONS = [
  { id: '1', label: 'ブルー', hex: '#1976d2' },
  { id: '2', label: 'グリーン', hex: '#2e7d32' },
  { id: '3', label: 'パープル', hex: '#7b1fa2' },
  { id: '4', label: 'レッド', hex: '#d32f2f' },
  { id: '5', label: 'オレンジ', hex: '#ed6c02' },
  { id: '6', label: 'ティール', hex: '#0097a7' },
  { id: '7', label: 'ピンク', hex: '#c2185b' },
  { id: '8', label: 'グレー', hex: '#616161' },
];

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
      {children}
    </Typography>
  );
}

function NotificationSection() {
  const { data: settings, isLoading } = useNotificationSettings();
  const updateSettings = useUpdateNotificationSettings();
  const { showSnackbar } = useUIStore();

  const [summaryTime, setSummaryTime] = useState('07:00');
  const [summaryEnabled, setSummaryEnabled] = useState(true);
  const [intervals, setIntervals] = useState<number[]>([30, 10]);
  const [unrepliedDays, setUnrepliedDays] = useState(3);
  const [unrepliedEnabled, setUnrepliedEnabled] = useState(true);

  useEffect(() => {
    if (settings) {
      setSummaryTime(settings.morningSummaryTime);
      setSummaryEnabled(settings.morningSummaryEnabled);
      setIntervals(settings.reminderIntervals);
      setUnrepliedDays(settings.unrepliedThresholdDays);
      setUnrepliedEnabled(settings.unrepliedReminderEnabled);
    }
  }, [settings]);

  const handleSave = () => {
    updateSettings.mutate(
      {
        morningSummaryTime: summaryTime,
        morningSummaryEnabled: summaryEnabled,
        reminderIntervals: intervals,
        unrepliedThresholdDays: unrepliedDays,
        unrepliedReminderEnabled: unrepliedEnabled,
      },
      {
        onSuccess: () => showSnackbar('通知設定を保存しました', 'success'),
        onError: () => showSnackbar('保存に失敗しました', 'error'),
      },
    );
  };

  const toggleInterval = (minutes: number) => {
    setIntervals((prev) =>
      prev.includes(minutes) ? prev.filter((m) => m !== minutes) : [...prev, minutes].sort((a, b) => b - a),
    );
  };

  if (isLoading) {
    return <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 1 }} />;
  }

  return (
    <Paper sx={{ p: 3 }}>
      <SectionTitle>通知設定</SectionTitle>

      <Box sx={{ mb: 3 }}>
        <FormControlLabel
          control={<Switch checked={summaryEnabled} onChange={(e) => setSummaryEnabled(e.target.checked)} />}
          label="朝のサマリー配信"
        />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1, ml: 4 }}>
          <TextField
            type="time"
            size="small"
            value={summaryTime}
            onChange={(e) => setSummaryTime(e.target.value)}
            disabled={!summaryEnabled}
            sx={{ width: 150 }}
          />
          <Typography variant="body2" color="text.secondary">
            に配信
          </Typography>
        </Box>
      </Box>

      <Box sx={{ mb: 3 }}>
        <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>
          予定リマインダー間隔
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {PRESET_INTERVALS.map((min) => (
            <Chip
              key={min}
              label={min >= 60 ? `${min / 60}時間前` : `${min}分前`}
              color={intervals.includes(min) ? 'primary' : 'default'}
              variant={intervals.includes(min) ? 'filled' : 'outlined'}
              onClick={() => toggleInterval(min)}
            />
          ))}
        </Box>
      </Box>

      <Box sx={{ mb: 3 }}>
        <FormControlLabel
          control={
            <Switch checked={unrepliedEnabled} onChange={(e) => setUnrepliedEnabled(e.target.checked)} />
          }
          label="LINE未返信リマインダー"
        />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1, ml: 4 }}>
          <TextField
            type="number"
            size="small"
            value={unrepliedDays}
            onChange={(e) => setUnrepliedDays(Math.max(1, parseInt(e.target.value) || 1))}
            disabled={!unrepliedEnabled}
            sx={{ width: 80 }}
            inputProps={{ min: 1, max: 30 }}
          />
          <Typography variant="body2" color="text.secondary">
            日以上未返信でリマインド
          </Typography>
        </Box>
      </Box>

      <Button
        variant="contained"
        onClick={handleSave}
        disabled={updateSettings.isPending}
        sx={{ mt: 1 }}
      >
        {updateSettings.isPending ? <CircularProgress size={20} color="inherit" /> : '保存'}
      </Button>
    </Paper>
  );
}

function OAuthSection() {
  const { data: gmailStatus, isLoading: gmailLoading } = useGmailOAuthStatus();
  const { data: calendarStatus, isLoading: calendarLoading } = useCalendarOAuthStatus();
  const disconnectOAuth = useDisconnectOAuth();
  const { showSnackbar } = useUIStore();

  const handleConnect = (provider: 'gmail' | 'calendar') => {
    window.location.href = `${config.API_URL}/api/settings/oauth/${provider}/connect`;
  };

  const handleDisconnect = (provider: 'gmail' | 'calendar') => {
    disconnectOAuth.mutate(provider, {
      onSuccess: () => showSnackbar('連携を解除しました', 'success'),
      onError: () => showSnackbar('連携解除に失敗しました', 'error'),
    });
  };

  return (
    <Paper sx={{ p: 3 }}>
      <SectionTitle>外部サービス連携</SectionTitle>

      <Stack spacing={2}>
        {/* Gmail */}
        <Card variant="outlined">
          <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <EmailIcon color="error" />
              <Box>
                <Typography variant="body1" fontWeight="bold">
                  Gmail
                </Typography>
                {gmailLoading ? (
                  <Skeleton width={120} />
                ) : gmailStatus?.connected ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <CheckCircleIcon fontSize="small" color="success" />
                    <Typography variant="caption" color="success.main">
                      接続済み ({gmailStatus.email})
                    </Typography>
                  </Box>
                ) : (
                  <Typography variant="caption" color="text.secondary">
                    未接続
                  </Typography>
                )}
              </Box>
            </Box>
            {gmailStatus?.connected ? (
              <Button
                variant="outlined"
                color="error"
                size="small"
                startIcon={<LinkOffIcon />}
                onClick={() => handleDisconnect('gmail')}
                disabled={disconnectOAuth.isPending}
              >
                解除
              </Button>
            ) : (
              <Button
                variant="contained"
                size="small"
                startIcon={<GoogleIcon />}
                onClick={() => handleConnect('gmail')}
              >
                接続
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Google Calendar */}
        <Card variant="outlined">
          <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CalendarMonthIcon color="primary" />
              <Box>
                <Typography variant="body1" fontWeight="bold">
                  Google カレンダー
                </Typography>
                {calendarLoading ? (
                  <Skeleton width={120} />
                ) : calendarStatus?.connected ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <CheckCircleIcon fontSize="small" color="success" />
                    <Typography variant="caption" color="success.main">
                      接続済み ({calendarStatus.email})
                    </Typography>
                  </Box>
                ) : (
                  <Typography variant="caption" color="text.secondary">
                    未接続
                  </Typography>
                )}
              </Box>
            </Box>
            {calendarStatus?.connected ? (
              <Button
                variant="outlined"
                color="error"
                size="small"
                startIcon={<LinkOffIcon />}
                onClick={() => handleDisconnect('calendar')}
                disabled={disconnectOAuth.isPending}
              >
                解除
              </Button>
            ) : (
              <Button
                variant="contained"
                size="small"
                startIcon={<GoogleIcon />}
                onClick={() => handleConnect('calendar')}
              >
                接続
              </Button>
            )}
          </CardContent>
        </Card>
      </Stack>
    </Paper>
  );
}

function ColorRulesSection() {
  const { data: rules = [], isLoading } = useEventColorRules();
  const createRule = useCreateEventColorRule();
  const updateRule = useUpdateEventColorRule();
  const deleteRule = useDeleteEventColorRule();
  const { showSnackbar } = useUIStore();

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newRule, setNewRule] = useState({ eventType: 'business' as EventType, confirmationStatus: 'confirmed' as EventStatus, colorId: '1' });

  const handleCreate = () => {
    const colorOption = COLOR_OPTIONS.find((c) => c.id === newRule.colorId);
    createRule.mutate(
      { ...newRule, colorLabel: colorOption?.label },
      {
        onSuccess: () => {
          setAddDialogOpen(false);
          showSnackbar('カラールールを追加しました', 'success');
        },
      },
    );
  };

  const handleColorChange = (ruleId: string, colorId: string) => {
    const colorOption = COLOR_OPTIONS.find((c) => c.id === colorId);
    updateRule.mutate({ id: ruleId, colorId, colorLabel: colorOption?.label });
  };

  if (isLoading) {
    return <Skeleton variant="rectangular" height={150} sx={{ borderRadius: 1 }} />;
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <SectionTitle>カレンダー色ルール</SectionTitle>
        <Button size="small" startIcon={<AddIcon />} onClick={() => setAddDialogOpen(true)}>
          追加
        </Button>
      </Box>

      {rules.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          カラールールが設定されていません
        </Typography>
      ) : (
        <List dense>
          {rules.map((rule: EventColorRule) => {
            const colorOption = COLOR_OPTIONS.find((c) => c.id === rule.colorId);
            return (
              <ListItem key={rule.id} sx={{ bgcolor: 'grey.50', borderRadius: 1, mb: 0.5 }}>
                <Box
                  sx={{
                    width: 16,
                    height: 16,
                    borderRadius: '50%',
                    bgcolor: colorOption?.hex ?? '#ccc',
                    mr: 2,
                    flexShrink: 0,
                  }}
                />
                <ListItemText
                  primary={`${EVENT_TYPE_LABELS[rule.eventType]} / ${EVENT_STATUS_LABELS[rule.confirmationStatus]}`}
                />
                <Select
                  size="small"
                  value={rule.colorId}
                  onChange={(e) => handleColorChange(rule.id, e.target.value as string)}
                  sx={{ minWidth: 120, mr: 1 }}
                >
                  {COLOR_OPTIONS.map((opt) => (
                    <MenuItem key={opt.id} value={opt.id}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: opt.hex }} />
                        {opt.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
                <ListItemSecondaryAction>
                  <IconButton size="small" color="error" onClick={() => deleteRule.mutate(rule.id)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            );
          })}
        </List>
      )}

      {/* Add dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>カラールール追加</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Select
              size="small"
              value={newRule.eventType}
              onChange={(e) => setNewRule((prev) => ({ ...prev, eventType: e.target.value as EventType }))}
              fullWidth
            >
              <MenuItem value="business">ビジネス</MenuItem>
              <MenuItem value="private">プライベート</MenuItem>
            </Select>
            <Select
              size="small"
              value={newRule.confirmationStatus}
              onChange={(e) => setNewRule((prev) => ({ ...prev, confirmationStatus: e.target.value as EventStatus }))}
              fullWidth
            >
              <MenuItem value="confirmed">確定</MenuItem>
              <MenuItem value="tentative">仮</MenuItem>
            </Select>
            <Select
              size="small"
              value={newRule.colorId}
              onChange={(e) => setNewRule((prev) => ({ ...prev, colorId: e.target.value as string }))}
              fullWidth
            >
              {COLOR_OPTIONS.map((opt) => (
                <MenuItem key={opt.id} value={opt.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: opt.hex }} />
                    {opt.label}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>キャンセル</Button>
          <Button variant="contained" onClick={handleCreate} disabled={createRule.isPending}>
            追加
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}

function EmailFilterSection() {
  const { data: filters = [], isLoading } = useEmailFilters();
  const createFilter = useCreateEmailFilter();
  const deleteFilter = useDeleteEmailFilter();
  const { showSnackbar } = useUIStore();

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newFilter, setNewFilter] = useState({
    filterType: 'sender' as EmailFilterType,
    filterValue: '',
    action: 'important' as EmailFilterAction,
  });

  const handleCreate = () => {
    if (!newFilter.filterValue.trim()) return;
    createFilter.mutate(
      { ...newFilter, filterValue: newFilter.filterValue.trim() },
      {
        onSuccess: () => {
          setAddDialogOpen(false);
          setNewFilter({ filterType: 'sender', filterValue: '', action: 'important' });
          showSnackbar('フィルターを追加しました', 'success');
        },
      },
    );
  };

  if (isLoading) {
    return <Skeleton variant="rectangular" height={150} sx={{ borderRadius: 1 }} />;
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <SectionTitle>メールフィルター</SectionTitle>
        <Button size="small" startIcon={<AddIcon />} onClick={() => setAddDialogOpen(true)}>
          追加
        </Button>
      </Box>

      {filters.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          フィルターが設定されていません
        </Typography>
      ) : (
        <List dense>
          {filters.map((filter: EmailFilter) => (
            <ListItem key={filter.id} sx={{ bgcolor: 'grey.50', borderRadius: 1, mb: 0.5 }}>
              <ListItemText
                primary={filter.filterValue}
                secondary={`${FILTER_TYPE_LABELS[filter.filterType]} / ${FILTER_ACTION_LABELS[filter.action]}`}
              />
              <ListItemSecondaryAction>
                <Chip
                  label={FILTER_ACTION_LABELS[filter.action]}
                  size="small"
                  color={filter.action === 'important' ? 'primary' : 'default'}
                  sx={{ mr: 1 }}
                />
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => deleteFilter.mutate(filter.id, {
                    onSuccess: () => showSnackbar('フィルターを削除しました', 'success'),
                  })}
                  disabled={deleteFilter.isPending}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}

      {/* Add dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>メールフィルター追加</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Select
              size="small"
              value={newFilter.filterType}
              onChange={(e) => setNewFilter((prev) => ({ ...prev, filterType: e.target.value as EmailFilterType }))}
              fullWidth
            >
              <MenuItem value="sender">送信者</MenuItem>
              <MenuItem value="domain">ドメイン</MenuItem>
              <MenuItem value="subject_pattern">件名パターン</MenuItem>
            </Select>
            <TextField
              size="small"
              placeholder="フィルター値"
              value={newFilter.filterValue}
              onChange={(e) => setNewFilter((prev) => ({ ...prev, filterValue: e.target.value }))}
              fullWidth
            />
            <Select
              size="small"
              value={newFilter.action}
              onChange={(e) => setNewFilter((prev) => ({ ...prev, action: e.target.value as EmailFilterAction }))}
              fullWidth
            >
              <MenuItem value="important">重要としてマーク</MenuItem>
              <MenuItem value="exclude">除外</MenuItem>
            </Select>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>キャンセル</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!newFilter.filterValue.trim() || createFilter.isPending}
          >
            追加
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}

function SettingsPage() {
  return (
    <Box sx={{ p: 3, maxWidth: 900, mx: 'auto' }}>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        設定
      </Typography>

      <Stack spacing={3}>
        <NotificationSection />
        <OAuthSection />
        <ColorRulesSection />
        <EmailFilterSection />
      </Stack>
    </Box>
  );
}

export default SettingsPage;
