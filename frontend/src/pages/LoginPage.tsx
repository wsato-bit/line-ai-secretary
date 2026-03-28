import { Box, Button, Typography, Container, Paper } from '@mui/material';
import { config } from '@/config';

function LoginPage() {
  const handleLineLogin = () => {
    const params = new URLSearchParams({
      response_type: 'code',
      client_id: config.LINE_LOGIN_CHANNEL_ID,
      redirect_uri: config.LINE_LOGIN_REDIRECT_URI,
      state: crypto.randomUUID(),
      scope: 'profile openid',
    });
    window.location.href = `https://access.line.me/oauth2/v2.1/authorize?${params}`;
  };

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
