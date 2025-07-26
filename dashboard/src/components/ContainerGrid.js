import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  Typography,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Terminal as TerminalIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import api from '../services/api';

const ContainerGrid = ({ containers, onCreateContainer, onCreateSession, onRefresh }) => {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('');

  const containerTemplates = [
    { name: 'python-dev', label: 'Python Development' },
    { name: 'node-dev', label: 'Node.js Development' },
    { name: 'ascii-games', label: 'ASCII Games' },
    { name: 'system-monitor', label: 'System Monitor' },
  ];

  const handleContainerAction = async (containerId, action) => {
    try {
      await api.containerAction(containerId, action);
      onRefresh();
    } catch (error) {
      console.error(`Failed to ${action} container:`, error);
    }
  };

  const handleCreateContainer = () => {
    if (selectedTemplate) {
      onCreateContainer(selectedTemplate);
      setCreateDialogOpen(false);
      setSelectedTemplate('');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'exited':
        return 'error';
      case 'paused':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Containers
        </Typography>
        <IconButton onClick={onRefresh} size="small" sx={{ mr: 1 }}>
          <RefreshIcon />
        </IconButton>
        <Button
          variant="contained"
          size="small"
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Container
        </Button>
      </Box>

      <Grid container spacing={2}>
        {containers.map((container) => (
          <Grid item xs={12} sm={6} md={4} key={container.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" noWrap>
                  {container.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" noWrap>
                  {container.image}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Chip
                    label={container.status}
                    color={getStatusColor(container.status)}
                    size="small"
                  />
                </Box>
              </CardContent>
              <CardActions>
                {container.status === 'running' ? (
                  <>
                    <IconButton
                      size="small"
                      onClick={() => onCreateSession(container.id)}
                      title="Open Terminal"
                    >
                      <TerminalIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleContainerAction(container.id, 'stop')}
                      title="Stop"
                    >
                      <StopIcon />
                    </IconButton>
                  </>
                ) : (
                  <IconButton
                    size="small"
                    onClick={() => handleContainerAction(container.id, 'start')}
                    title="Start"
                  >
                    <PlayIcon />
                  </IconButton>
                )}
                <IconButton
                  size="small"
                  onClick={() => handleContainerAction(container.id, 'remove')}
                  title="Remove"
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)}>
        <DialogTitle>Create Container</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Container Template</InputLabel>
            <Select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              label="Container Template"
            >
              {containerTemplates.map((template) => (
                <MenuItem key={template.name} value={template.name}>
                  {template.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateContainer} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ContainerGrid;