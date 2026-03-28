import { Box, Typography, Grid2 as Grid, Paper } from '@mui/material';

function WorkspacePage() {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        ワークスペース
      </Typography>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, minHeight: 200 }}>
            <Typography variant="h6">今日の予定</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, minHeight: 200 }}>
            <Typography variant="h6">未読重要メール</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, minHeight: 200 }}>
            <Typography variant="h6">LINE未返信</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, minHeight: 200 }}>
            <Typography variant="h6">最近のメモ</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default WorkspacePage;
