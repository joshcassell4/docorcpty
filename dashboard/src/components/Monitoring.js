import React from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Grid,
  Paper,
} from '@mui/material';

const Monitoring = ({ stats }) => {
  if (!stats || !stats.system) {
    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 2 }}>
          System Monitoring
        </Typography>
        <Typography color="text.secondary">
          Loading system statistics...
        </Typography>
      </Box>
    );
  }

  const { cpu, memory, disk, process } = stats.system;

  const formatBytes = (bytes) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const MetricCard = ({ title, value, percent, unit = '%' }) => (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" color="text.secondary">
        {title}
      </Typography>
      <Typography variant="h6">
        {value}{unit}
      </Typography>
      {percent !== undefined && (
        <Box sx={{ mt: 1 }}>
          <LinearProgress
            variant="determinate"
            value={percent}
            color={percent > 80 ? 'error' : percent > 60 ? 'warning' : 'primary'}
          />
        </Box>
      )}
    </Paper>
  );

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        System Monitoring
      </Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <MetricCard
            title="CPU Usage"
            value={cpu?.percent?.toFixed(1) || 0}
            percent={cpu?.percent || 0}
          />
        </Grid>
        
        <Grid item xs={6}>
          <MetricCard
            title="Memory Usage"
            value={memory?.percent?.toFixed(1) || 0}
            percent={memory?.percent || 0}
          />
        </Grid>
        
        <Grid item xs={6}>
          <MetricCard
            title="Disk Usage"
            value={disk?.percent?.toFixed(1) || 0}
            percent={disk?.percent || 0}
          />
        </Grid>
        
        <Grid item xs={6}>
          <MetricCard
            title="Process Memory"
            value={formatBytes(process?.memory || 0)}
            unit=""
          />
        </Grid>
      </Grid>
      
      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Sessions: {stats.orchestrator?.sessions || 0} / {stats.orchestrator?.max_sessions || 50}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Containers: {stats.containers || 0}
        </Typography>
      </Box>
    </Box>
  );
};

export default Monitoring;