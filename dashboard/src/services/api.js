import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = {
  // Health and status
  async getHealth() {
    const response = await axios.get(`${API_URL}/health`);
    return response.data;
  },

  // Container operations
  async getContainers(all = false) {
    const response = await axios.get(`${API_URL}/api/containers`, {
      params: { all },
    });
    return response.data;
  },

  async createContainer(name) {
    const response = await axios.post(`${API_URL}/api/containers`, { name });
    return response.data;
  },

  async getContainer(containerId) {
    const response = await axios.get(`${API_URL}/api/containers/${containerId}`);
    return response.data;
  },

  async containerAction(containerId, action) {
    const response = await axios.post(
      `${API_URL}/api/containers/${containerId}/action`,
      { action }
    );
    return response.data;
  },

  async getContainerStats(containerId) {
    const response = await axios.get(`${API_URL}/api/containers/${containerId}/stats`);
    return response.data;
  },

  async getContainerLogs(containerId, tail = 100) {
    const response = await axios.get(`${API_URL}/api/containers/${containerId}/logs`, {
      params: { tail },
    });
    return response.data;
  },

  // Session operations
  async getSessions() {
    const response = await axios.get(`${API_URL}/api/sessions`);
    return response.data;
  },

  async createSession(containerId, command = null, useAutomation = false) {
    const response = await axios.post(`${API_URL}/api/sessions`, {
      container_id: containerId,
      command,
      use_automation: useAutomation,
    });
    return response.data;
  },

  async getSession(sessionId) {
    const response = await axios.get(`${API_URL}/api/sessions/${sessionId}`);
    return response.data;
  },

  async closeSession(sessionId) {
    const response = await axios.delete(`${API_URL}/api/sessions/${sessionId}`);
    return response.data;
  },

  // Automation operations
  async executeScript(sessionId, commands, expectPrompts = null, timeout = 30.0) {
    const response = await axios.post(`${API_URL}/api/automation/execute`, {
      session_id: sessionId,
      commands,
      expect_prompts: expectPrompts,
      timeout,
    });
    return response.data;
  },

  async getAutomationTemplates() {
    const response = await axios.get(`${API_URL}/api/automation/templates`);
    return response.data;
  },

  async executeTemplate(templateName, sessionId, variables = null) {
    const response = await axios.post(
      `${API_URL}/api/automation/templates/${templateName}/execute`,
      null,
      {
        params: {
          session_id: sessionId,
          ...variables,
        },
      }
    );
    return response.data;
  },
};

export default api;