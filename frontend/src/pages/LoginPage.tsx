import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Button,
  CircularProgress,
  Container,
  Paper,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import { config } from '@/config';
import { apiClient } from '@/services/apiClient';
import { useAuthStore } from '@/stores/authStore';
import type { User } from '@/types';

type PageView = 'login' | 'callback' | 'apply' | 'pending' | 'rejected';

interface LoginResponse {
  user: User;
  accessToken: string;
  isNewUser: boolean;
}

interface ApplicationForm {
  displayName: string;
  reason: string;
}

function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, isAuthenticated } = useAuthStore();

  const [view, setView] = useState<PageView>('login');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rejectionMessage, setRejectionMessage] = useState('');
  const [form, setForm] = useState<ApplicationForm>({ displayName: '', reason: '' });

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
      return;
    }

    const code = searchParams.get('code');
    if (code) {
      handleCallback(code);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCallback = async (code: string) => {
    setView('callback');
    setIsProcessing(true);
    setError(null);

    try {
      const response = await apiClient.post<LoginResponse>('/api/auth/line/callback', {
        code,
        redirectUri: config.LINE_LOGIN_REDIRECT_URI,
      });

      if (response.isNewUser) {
        setForm((prev) => ({
          ...prev,
          displayName: response.user.lineDisplayName || '',
        }));
        setView('apply');
        return;
      }

      if (response.user.status === 'pending') {
        setView('pending');
        return;
      }

      if (response.user.status === 'rejected') {
        setRejectionMessage('管理者により申請が却下されました。');
        setView('rejected');
        return;
      }

      if (response.user.status === 'disabled') {
        setError('このアカウントは無効化されています。管理者にお問い合わせください。');
        setView('login');
        return;
      }

      login(response.user, response.accessToken);
      navigate('/', { replace: true });
    } catch {
      setError('ログイン処理に失敗しました。もう一度お試しください。');
      setView('login');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLineLogin = () => {
    const state = crypto.randomUUID();
    sessionStorage.setItem('line_oauth_state', state);
    const params = new URLSearchParams({
      response_type: 'code',
      client_id: config.LINE_LOGIN_CHANNEL_ID,
      redirect_uri: config.LINE_LOGIN_REDIRECT_URI,
      state,
      scope: 'profile openid',
    });
    window.location.href = `https://access.line.me/oauth2/v2.1/authorize?${params}`;
  };

  const handleApply = async () => {
    if (!form.displayName.trim()) {
      setError('表示名を入力してください。');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      await apiClient.post('/api/auth/apply', {
        displayName: form.displayName.trim(),
        reason: form.reason.trim(),
      });
      setView('pending');
    } catch {
      setError('申請の送信に失敗しました。もう一度お試しください。');
    } finally {
      setIsProcessing(false);
    }
  };

  if (view === 'callback' && isProcessing) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 12, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <CircularProgress color="primary" size={48} />
          <Typography variant="body1" sx={{ mt: 2 }}>
            ログイン処理中...
          </Typography>
        </Box>
      </Container>
    );
  }

  if (view === 'pending') {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 12, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Paper elevation={3} sx={{ p: 5, width: '100%', textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom fontWeight="bold" color="primary">
              申請を受け付けました
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
              管理者による承認をお待ちください。
            </Typography>
            <Typography variant="body2" color="text.secondary">
              承認されるとLINEで通知が届きます。
            </Typography>
          </Paper>
        </Box>
      </Container>
    );
  }

  if (view === 'rejected') {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 12, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Paper elevation={3} sx={{ p: 5, width: '100%', textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom fontWeight="bold" color="error">
              申請が却下されました
            </Typography>
            <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
              {rejectionMessage || '管理者により申請が却下されました。'}
            </Alert>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              再申請が必要な場合は管理者にお問い合わせください。
            </Typography>
            <Button variant="outlined" onClick={() => setView('login')}>
              ログイン画面に戻る
            </Button>
          </Paper>
        </Box>
      </Container>
    );
  }

  if (view === 'apply') {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 12, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Paper elevation={3} sx={{ p: 5, width: '100%' }}>
            <Typography variant="h5" gutterBottom fontWeight="bold" textAlign="center">
              利用申請
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }} textAlign="center">
              初めてのご利用には管理者の承認が必要です。
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <TextField
              label="表示名"
              value={form.displayName}
              onChange={(e) => setForm((prev) => ({ ...prev, displayName: e.target.value }))}
              fullWidth
              required
              sx={{ mb: 2 }}
            />
            <TextField
              label="申請理由（任意）"
              value={form.reason}
              onChange={(e) => setForm((prev) => ({ ...prev, reason: e.target.value }))}
              fullWidth
              multiline
              rows={3}
              sx={{ mb: 3 }}
            />
            <Button
              variant="contained"
              fullWidth
              onClick={handleApply}
              disabled={isProcessing}
              sx={{
                bgcolor: '#06C755',
                '&:hover': { bgcolor: '#05B34C' },
                py: 1.5,
              }}
            >
              {isProcessing ? <CircularProgress size={24} color="inherit" /> : '申請する'}
            </Button>
          </Paper>
        </Box>
      </Container>
    );
  }

  // Default: login view
  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 12, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={3} sx={{ p: 5, width: '100%', textAlign: 'center' }}>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            LINE AI Secretary
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            AI個人秘書サービス
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
              {error}
            </Alert>
          )}

          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={handleLineLogin}
            sx={{
              bgcolor: '#06C755',
              '&:hover': { bgcolor: '#05B34C' },
              py: 1.5,
              fontSize: '1.1rem',
            }}
          >
            LINEでログイン
          </Button>
        </Paper>
      </Box>
    </Container>
  );
}

export default LoginPage;
