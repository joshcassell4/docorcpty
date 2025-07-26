import React, { useState, useEffect } from 'react';
import { Container, Box, AppBar, Toolbar, Typography, Paper } from '@mui/material';
import ContainerGrid from './components/ContainerGrid';
import Terminal from './components/Terminal';
import Monitoring from './components/Monitoring';
import api from './services/api';

function App() {
  const [containers, setContainers] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [systemStats, setSystemStats] = useState(null);

  useEffect(() => {
    // Load initial data
    loadContainers();
    loadSessions();
    loadSystemStats();

    // Set up polling
    const interval = setInterval(() => {
      loadContainers();
      loadSystemStats();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const loadContainers = async () => {
    try {
      const data = await api.getContainers();
      setContainers(data);
    } catch (error) {
      console.error('Failed to load containers:', error);
    }
  };

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const loadSystemStats = async () => {
    try {
      const data = await api.getHealth();
      setSystemStats(data);
    } catch (error) {
      console.error('Failed to load system stats:', error);
    }
  };

  const handleCreateContainer = async (containerName) => {
    try {
      await api.createContainer(containerName);
      loadContainers();
    } catch (error) {
      console.error('Failed to create container:', error);
    }
  };

  const handleCreateSession = async (containerId) => {
    try {
      const session = await api.createSession(containerId);
      loadSessions();
      setSelectedSession(session.session_id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Container Terminal Orchestrator
          </Typography>
          <Typography variant="body2">
            Sessions: {sessions.length} / {systemStats?.orchestrator?.max_sessions || 50}
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ flex: 1, py: 2, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
          <Paper sx={{ p: 2 }}>
            <ContainerGrid
              containers={containers}
              onCreateContainer={handleCreateContainer}
              onCreateSession={handleCreateSession}
              onRefresh={loadContainers}
            />
          </Paper>
          
          <Paper sx={{ p: 2 }}>
            <Monitoring stats={systemStats} />
          </Paper>
        </Box>

        <Paper sx={{ flex: 1, p: 2 }}>
          {selectedSession ? (
            <Terminal
              sessionId={selectedSession}
              onClose={() => {
                setSelectedSession(null);
                loadSessions();
              }}
            />
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              <Typography variant="h6" color="text.secondary">
                Select a container to start a terminal session
              </Typography>
            </Box>
          )}
        </Paper>
      </Container>
    </Box>
  );
}

export default App;