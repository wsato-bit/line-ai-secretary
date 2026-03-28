import {
  Alert,
  Box,
  Button,
  Chip,
  Grid2 as Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Skeleton,
  Typography,
} from '@mui/material';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import EmailIcon from '@mui/icons-material/Email';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import TextSnippetIcon from '@mui/icons-material/TextSnippet';
import ImageIcon from '@mui/icons-material/Image';
import LinkIcon from '@mui/icons-material/Link';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { useNavigate } from 'react-router-dom';
import { useTodaySchedule } from '@/hooks/useSchedule';
import { useImportantEmails } from '@/hooks/useEmails';
import { useUnrepliedItems, useCompleteUnreplied } from '@/hooks/useUnreplied';
import { useRecentMemos } from '@/hooks/useMemos';
import type { CalendarEvent, EmailSummary, UnrepliedItem, Memo, ContentType } from '@/types';

function formatTime(datetime: string): string {
  return new Date(datetime).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
}

function formatTimeRange(start: string, end: string): string {
  return `${formatTime(start)} - ${formatTime(end)}`;
}

const CONTENT_TYPE_ICON: Record<ContentType, React.ReactElement> = {
  text: <TextSnippetIcon fontSize="small" />,
  image: <ImageIcon fontSize="small" />,
  url: <LinkIcon fontSize="small" />,
};

// Section wrapper with loading/empty/error states
function SectionCard({
  title,
  isLoading,
  isError,
  isEmpty,
  emptyText,
  children,
  action,
}: {
  title: string;
  isLoading: boolean;
  isError: boolean;
  isEmpty: boolean;
  emptyText: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <Paper sx={{ p: 3, minHeight: 200, display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" fontWeight="bold">
          {title}
        </Typography>
        {action}
      </Box>

      {isLoading && (
        <Box sx={{ flex: 1 }}>
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} variant="rectangular" height={40} sx={{ mb: 1, borderRadius: 1 }} />
          ))}
        </Box>
      )}

      {isError && (
        <Alert severity="error" sx={{ mt: 1 }}>
          データの取得に失敗しました
        </Alert>
      )}

      {!isLoading && !isError && isEmpty && (
        <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {emptyText}
          </Typography>
        </Box>
      )}

      {!isLoading && !isError && !isEmpty && children}
    </Paper>
  );
}

function ScheduleSection() {
  const { data: events, isLoading, isError } = useTodaySchedule();

  return (
    <SectionCard
      title="今日の予定"
      isLoading={isLoading}
      isError={isError}
      isEmpty={!events || events.length === 0}
      emptyText="今日の予定はありません"
    >
      <List dense disablePadding>
        {events?.map((event: CalendarEvent) => (
          <ListItem
            key={event.id}
            sx={{
              borderLeft: '3px solid',
              borderColor: event.status === 'tentative' ? 'warning.main' : 'primary.main',
              mb: 1,
              borderRadius: 1,
              bgcolor: 'grey.50',
            }}
          >
            <ListItemIcon sx={{ minWidth: 36 }}>
              <AccessTimeIcon fontSize="small" color="action" />
            </ListItemIcon>
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" fontWeight="bold">
                    {event.title}
                  </Typography>
                  {event.status === 'tentative' && (
                    <Chip label="仮" size="small" color="warning" variant="outlined" />
                  )}
                </Box>
              }
              secondary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    {formatTimeRange(event.startDatetime, event.endDatetime)}
                  </Typography>
                  {event.location && (
                    <>
                      <LocationOnIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
                      <Typography variant="caption" color="text.secondary">
                        {event.location}
                      </Typography>
                    </>
                  )}
                </Box>
              }
            />
          </ListItem>
        ))}
      </List>
    </SectionCard>
  );
}

function EmailSection() {
  const { data: emails, isLoading, isError } = useImportantEmails();

  return (
    <SectionCard
      title="未読重要メール"
      isLoading={isLoading}
      isError={isError}
      isEmpty={!emails || emails.length === 0}
      emptyText="未読の重要メールはありません"
    >
      <List dense disablePadding>
        {emails?.slice(0, 5).map((email: EmailSummary) => (
          <ListItem
            key={email.id}
            sx={{ mb: 1, borderRadius: 1, bgcolor: 'grey.50', cursor: 'pointer' }}
          >
            <ListItemIcon sx={{ minWidth: 36 }}>
              <EmailIcon fontSize="small" color="primary" />
            </ListItemIcon>
            <ListItemText
              primary={
                <Typography variant="body2" fontWeight="bold" noWrap>
                  {email.subject}
                </Typography>
              }
              secondary={
                <>
                  <Typography variant="caption" color="text.secondary" component="span">
                    {email.from}
                  </Typography>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: 'block', mt: 0.5 }}
                    noWrap
                  >
                    {email.summary}
                  </Typography>
                </>
              }
            />
          </ListItem>
        ))}
      </List>
    </SectionCard>
  );
}

function UnrepliedSection() {
  const { data: items, isLoading, isError } = useUnrepliedItems();
  const completeMutation = useCompleteUnreplied();

  const activeItems = items?.filter((item: UnrepliedItem) => !item.isCompleted) ?? [];

  const handleComplete = (id: string) => {
    completeMutation.mutate(id);
  };

  return (
    <SectionCard
      title="LINE未返信"
      isLoading={isLoading}
      isError={isError}
      isEmpty={activeItems.length === 0}
      emptyText="未返信の連絡はありません"
    >
      <List dense disablePadding>
        {activeItems.map((item: UnrepliedItem) => (
          <ListItem
            key={item.id}
            sx={{ mb: 1, borderRadius: 1, bgcolor: 'grey.50' }}
            secondaryAction={
              <Button
                size="small"
                variant="outlined"
                color="primary"
                onClick={() => handleComplete(item.id)}
                disabled={completeMutation.isPending}
                startIcon={<CheckCircleOutlineIcon />}
              >
                完了
              </Button>
            }
          >
            <ListItemIcon sx={{ minWidth: 36 }}>
              {item.daysElapsed >= 3 ? (
                <WarningAmberIcon fontSize="small" color="error" />
              ) : (
                <AccessTimeIcon fontSize="small" color="action" />
              )}
            </ListItemIcon>
            <ListItemText
              primary={
                <Typography variant="body2" fontWeight="bold">
                  {item.contactName}
                </Typography>
              }
              secondary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  <Chip
                    label={`${item.daysElapsed}日経過`}
                    size="small"
                    color={item.daysElapsed >= 3 ? 'error' : 'default'}
                    variant="outlined"
                  />
                  {item.contentMemo && (
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {item.contentMemo}
                    </Typography>
                  )}
                </Box>
              }
            />
          </ListItem>
        ))}
      </List>
    </SectionCard>
  );
}

function RecentMemosSection() {
  const navigate = useNavigate();
  const { data: memos, isLoading, isError } = useRecentMemos(5);

  return (
    <SectionCard
      title="最近のメモ"
      isLoading={isLoading}
      isError={isError}
      isEmpty={!memos || memos.length === 0}
      emptyText="メモはまだありません"
      action={
        <Button size="small" color="primary" onClick={() => navigate('/memos')}>
          すべて表示
        </Button>
      }
    >
      <List dense disablePadding>
        {memos?.map((memo: Memo) => (
          <ListItem
            key={memo.id}
            sx={{ mb: 1, borderRadius: 1, bgcolor: 'grey.50', cursor: 'pointer' }}
            onClick={() => navigate('/memos')}
          >
            <ListItemIcon sx={{ minWidth: 36 }}>
              {CONTENT_TYPE_ICON[memo.contentType]}
            </ListItemIcon>
            <ListItemText
              primary={
                <Typography variant="body2" noWrap>
                  {memo.contentType === 'url' ? memo.urlTitle || memo.content : memo.content}
                </Typography>
              }
              secondary={
                <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
                  {memo.tags.slice(0, 3).map((tag) => (
                    <Chip key={tag} label={tag} size="small" variant="outlined" />
                  ))}
                </Box>
              }
            />
          </ListItem>
        ))}
      </List>
    </SectionCard>
  );
}

function WorkspacePage() {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        ワークスペース
      </Typography>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <ScheduleSection />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <EmailSection />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <UnrepliedSection />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <RecentMemosSection />
        </Grid>
      </Grid>
    </Box>
  );
}

export default WorkspacePage;
