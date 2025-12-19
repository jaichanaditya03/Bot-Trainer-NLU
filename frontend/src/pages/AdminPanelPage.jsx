import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import {
  Users, Trash2, Key, Database, Download, FolderOpen,
  RefreshCw, Activity, BarChart3, Eye, EyeOff, AlertCircle, X, Check
} from 'lucide-react';
import api from '../services/api';

export const AdminPanelPage = () => {
  const [activeSection, setActiveSection] = useState('users');
  const [loading, setLoading] = useState(false);
  
  // Users Management
  const [users, setUsers] = useState([]);
  const [userToDelete, setUserToDelete] = useState(null);
  const [resetPasswordUser, setResetPasswordUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  // Workspaces Management
  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState(null);
  
  // Datasets Management
  const [datasets, setDatasets] = useState([]);
  
  // Models Management
  const [models, setModels] = useState([]);
  
  // Logs/Activity
  const [uploadLogs, setUploadLogs] = useState([]);
  const [correctionLogs, setCorrectionLogs] = useState([]);
  const [activeLearningLogs, setActiveLearningLogs] = useState([]);
  const [trainingLogs, setTrainingLogs] = useState([]);
  
  // Annotations
  const [annotations, setAnnotations] = useState([]);
  
  // Statistics
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    switch (activeSection) {
      case 'users':
        fetchUsers();
        break;
      case 'workspaces':
        fetchWorkspaces();
        break;
      case 'datasets':
        fetchDatasets();
        break;
      case 'models':
        fetchModels();
        break;
      case 'logs':
        fetchLogs();
        break;
      case 'annotations':
        fetchAnnotations();
        break;
    }
  }, [activeSection]);

  const fetchStats = async () => {
    try {
      const response = await api.get('/admin/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  // ===== USER MANAGEMENT =====
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/users');
      setUsers(response.data.users || []);
    } catch (error) {
      toast.error('Failed to fetch users');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (email) => {
    if (!window.confirm(`Are you sure you want to delete user ${email}? This will delete all their data.`)) {
      return;
    }
    
    try {
      await api.delete(`/admin/users/${email}`);
      toast.success(`User ${email} deleted successfully`);
      fetchUsers();
      fetchStats();
      setUserToDelete(null);
    } catch (error) {
      toast.error('Failed to delete user');
      console.error(error);
    }
  };

  const handleResetPassword = async () => {
    if (!resetPasswordUser || !newPassword) {
      toast.error('Please enter a new password');
      return;
    }

    try {
      await api.post('/admin/users/reset-password', {
        email: resetPasswordUser,
        new_password: newPassword
      });
      toast.success('Password reset successfully');
      setResetPasswordUser(null);
      setNewPassword('');
    } catch (error) {
      toast.error('Failed to reset password');
      console.error(error);
    }
  };

  // ===== WORKSPACE MANAGEMENT =====
  const fetchWorkspaces = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/workspaces');
      setWorkspaces(response.data.workspaces || []);
    } catch (error) {
      toast.error('Failed to fetch workspaces');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWorkspace = async (workspaceId) => {
    if (!window.confirm('Are you sure you want to delete this workspace? All associated data will be deleted.')) {
      return;
    }

    try {
      await api.delete(`/admin/workspaces/${workspaceId}`);
      toast.success('Workspace deleted successfully');
      fetchWorkspaces();
      fetchStats();
    } catch (error) {
      toast.error('Failed to delete workspace');
      console.error(error);
    }
  };

  const handleDownloadWorkspace = async (workspaceId, workspaceName) => {
    try {
      const response = await api.get(`/admin/workspaces/${workspaceId}/download`);
      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${workspaceName}_export_${Date.now()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      toast.success('Workspace data downloaded');
    } catch (error) {
      toast.error('Failed to download workspace data');
      console.error(error);
    }
  };

  // ===== DATASET MANAGEMENT =====
  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/datasets');
      setDatasets(response.data.datasets || []);
    } catch (error) {
      toast.error('Failed to fetch datasets');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadDataset = async (workspaceId, workspaceName, format = 'csv') => {
    try {
      const response = await api.get(`/admin/datasets/${workspaceId}/download`);
      const data = response.data;
      
      if (!data.data || data.data.length === 0) {
        toast.error('No data found in dataset');
        return;
      }

      let blob, filename;
      
      if (format === 'csv') {
        // Convert to CSV
        const headers = ['sentence', 'intent', 'entities'];
        const csvRows = [headers.join(',')];
        
        data.data.forEach(item => {
          const sentence = `"${(item.sentence || '').replace(/"/g, '""')}"`;
          const intent = `"${(item.intent || '').replace(/"/g, '""')}"`;
          const entities = `"${JSON.stringify(item.entities || []).replace(/"/g, '""')}"`;
          csvRows.push([sentence, intent, entities].join(','));
        });
        
        const csvContent = csvRows.join('\n');
        blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        filename = `${workspaceName}_dataset_${Date.now()}.csv`;
      } else {
        // JSON format
        const dataStr = JSON.stringify(data, null, 2);
        blob = new Blob([dataStr], { type: 'application/json' });
        filename = `${workspaceName}_dataset_${Date.now()}.json`;
      }
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      toast.success(`Dataset downloaded as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Failed to download dataset');
      console.error(error);
    }
  };

  const handleDeleteDataset = async (workspaceId, checksum, filename) => {
    if (!window.confirm(`Are you sure you want to delete dataset "${filename}"?`)) {
      return;
    }

    try {
      await api.delete(`/admin/datasets/${workspaceId}/${checksum}`);
      toast.success('Dataset deleted successfully');
      fetchDatasets();
      fetchStats();
    } catch (error) {
      toast.error('Failed to delete dataset');
      console.error(error);
    }
  };

  // ===== MODEL MANAGEMENT =====
  const fetchModels = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/models');
      setModels(response.data.models || []);
    } catch (error) {
      toast.error('Failed to fetch models');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteModel = async (comparisonId, modelIndex, modelName) => {
    if (!window.confirm(`Are you sure you want to delete model "${modelName}"?`)) {
      return;
    }

    try {
      await api.delete(`/admin/models/${comparisonId}/${modelIndex}`);
      toast.success('Model deleted successfully');
      fetchModels();
      fetchStats();
    } catch (error) {
      toast.error('Failed to delete model');
      console.error(error);
    }
  };

  // ===== LOGS =====
  const fetchLogs = async () => {
    setLoading(true);
    try {
      const [uploadsRes, correctionsRes, activeLearningRes, trainingRes] = await Promise.all([
        api.get('/admin/logs/uploads'),
        api.get('/admin/logs/corrections'),
        api.get('/admin/logs/active-learning'),
        api.get('/admin/logs/training')
      ]);
      setUploadLogs(uploadsRes.data.uploads || []);
      setCorrectionLogs(correctionsRes.data.corrections || []);
      setActiveLearningLogs(activeLearningRes.data.corrections || []);
      setTrainingLogs(trainingRes.data.trainings || []);
    } catch (error) {
      toast.error('Failed to fetch logs');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // ===== ANNOTATIONS =====
  const fetchAnnotations = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/annotations');
      setAnnotations(response.data.annotations || []);
    } catch (error) {
      toast.error('Failed to fetch annotations');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen" style={{ paddingTop: '80px' }}>
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2" style={{ color: '#f3f8ff' }}>
            Admin Panel
          </h1>
          <p style={{ color: 'rgba(228, 247, 238, 0.75)' }}>
            Manage users, workspaces, datasets, and view system activity
          </p>
        </div>

        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <div className="card p-4" style={{ background: 'rgba(50, 186, 255, 0.08)', borderColor: 'rgba(50, 186, 255, 0.35)' }}>
              <div className="flex items-center gap-3">
                <Users size={24} style={{ color: '#32beff' }} />
                <div>
                  <p className="text-2xl font-bold" style={{ color: '#32beff' }}>{stats.total_users}</p>
                  <p className="text-xs" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>Users</p>
                </div>
              </div>
            </div>

            <div className="card p-4" style={{ background: 'rgba(50, 244, 122, 0.08)', borderColor: 'rgba(50, 244, 122, 0.35)' }}>
              <div className="flex items-center gap-3">
                <FolderOpen size={24} style={{ color: '#2bf06f' }} />
                <div>
                  <p className="text-2xl font-bold" style={{ color: '#2bf06f' }}>{stats.total_workspaces}</p>
                  <p className="text-xs" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>Workspaces</p>
                </div>
              </div>
            </div>

            <div className="card p-4" style={{ background: 'rgba(255, 186, 50, 0.08)', borderColor: 'rgba(255, 186, 50, 0.35)' }}>
              <div className="flex items-center gap-3">
                <Database size={24} style={{ color: '#ffba32' }} />
                <div>
                  <p className="text-2xl font-bold" style={{ color: '#ffba32' }}>{stats.total_datasets}</p>
                  <p className="text-xs" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>Datasets</p>
                </div>
              </div>
            </div>

            <div className="card p-4" style={{ background: 'rgba(255, 107, 107, 0.08)', borderColor: 'rgba(255, 107, 107, 0.35)' }}>
              <div className="flex items-center gap-3">
                <RefreshCw size={24} style={{ color: '#ff6b6b' }} />
                <div>
                  <p className="text-2xl font-bold" style={{ color: '#ff6b6b' }}>{stats.total_corrections}</p>
                  <p className="text-xs" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>Corrections</p>
                </div>
              </div>
            </div>

            <div className="card p-4" style={{ background: 'rgba(186, 107, 255, 0.08)', borderColor: 'rgba(186, 107, 255, 0.35)' }}>
              <div className="flex items-center gap-3">
                <Activity size={24} style={{ color: '#ba6bff' }} />
                <div>
                  <p className="text-2xl font-bold" style={{ color: '#ba6bff' }}>{stats.total_annotations}</p>
                  <p className="text-xs" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>Annotations</p>
                </div>
              </div>
            </div>

            <div className="card p-4" style={{ background: 'rgba(50, 244, 122, 0.08)', borderColor: 'rgba(50, 244, 122, 0.35)' }}>
              <div className="flex items-center gap-3">
                <BarChart3 size={24} style={{ color: '#2bf06f' }} />
                <div>
                  <p className="text-2xl font-bold" style={{ color: '#2bf06f' }}>{stats.avg_datasets_per_workspace}</p>
                  <p className="text-xs" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>Avg DS/WS</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="card mb-6 p-0 overflow-hidden">
          <div className="flex overflow-x-auto">
            {[
              { id: 'users', label: 'Users Management', icon: Users },
              { id: 'workspaces', label: 'Workspaces', icon: FolderOpen },
              { id: 'datasets', label: 'Datasets', icon: Database },
              { id: 'models', label: 'Models', icon: BarChart3 },
              { id: 'logs', label: 'Activity Logs', icon: Activity },
              { id: 'annotations', label: 'Annotated Data', icon: Check }
            ].map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className="flex items-center gap-2 px-6 py-4 font-medium whitespace-nowrap transition-all"
                style={{
                  color: activeSection === section.id ? '#2bf06f' : 'rgba(228, 247, 238, 0.65)',
                  background: activeSection === section.id ? 'rgba(50, 244, 122, 0.08)' : 'transparent',
                  borderBottom: activeSection === section.id ? '2px solid #2bf06f' : '2px solid transparent'
                }}
              >
                <section.icon size={18} />
                {section.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="card">
          {loading ? (
            <div className="text-center py-12">
              <RefreshCw className="animate-spin mx-auto mb-4" size={40} style={{ color: '#2bf06f' }} />
              <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>Loading...</p>
            </div>
          ) : (
            <>
              {/* USERS MANAGEMENT */}
              {activeSection === 'users' && (
                <div>
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold mb-2" style={{ color: '#f3f8ff' }}>Users Management</h2>
                    <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                      View registered users, remove users, and reset passwords
                    </p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(142, 228, 175, 0.25)' }}>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Email</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Full Name</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Role</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Created At</th>
                          <th className="text-right p-3" style={{ color: '#2bf06f' }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((user, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid rgba(142, 228, 175, 0.15)' }}>
                            <td className="p-3" style={{ color: '#f3f8ff' }}>{user.email}</td>
                            <td className="p-3" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>{user.username || user.full_name || 'N/A'}</td>
                            <td className="p-3">
                              <span className="px-2 py-1 rounded text-xs" style={{
                                background: user.is_admin ? 'rgba(255, 186, 50, 0.15)' : 'rgba(50, 186, 255, 0.15)',
                                color: user.is_admin ? '#ffba32' : '#32beff'
                              }}>
                                {user.is_admin ? 'Admin' : 'User'}
                              </span>
                            </td>
                            <td className="p-3" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                              {new Date(user.created_at).toLocaleDateString('en-GB')}
                            </td>
                            <td className="p-3 text-right">
                              <div className="flex justify-end gap-2">
                                <button
                                  onClick={() => setResetPasswordUser(user.email)}
                                  className="p-2 rounded transition-all"
                                  style={{ background: 'rgba(50, 186, 255, 0.15)', color: '#32beff' }}
                                  title="Reset Password"
                                >
                                  <Key size={16} />
                                </button>
                                <button
                                  onClick={() => handleDeleteUser(user.email)}
                                  className="p-2 rounded transition-all"
                                  style={{ background: 'rgba(255, 107, 107, 0.15)', color: '#ff6b6b' }}
                                  title="Delete User"
                                  disabled={user.is_admin}
                                >
                                  <Trash2 size={16} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {users.length === 0 && (
                    <div className="text-center py-8">
                      <AlertCircle className="mx-auto mb-2" size={32} style={{ color: 'rgba(228, 247, 238, 0.45)' }} />
                      <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>No users found</p>
                    </div>
                  )}
                </div>
              )}

              {/* WORKSPACES MANAGEMENT */}
              {activeSection === 'workspaces' && (
                <div>
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold mb-2" style={{ color: '#f3f8ff' }}>Workspaces Management</h2>
                    <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                      View all workspaces, their owners, and delete workspaces
                    </p>
                  </div>

                  <div className="grid gap-4">
                    {workspaces.map((workspace, idx) => (
                      <div key={idx} className="p-4 rounded-lg border" style={{
                        background: 'rgba(255, 255, 255, 0.04)',
                        borderColor: 'rgba(142, 228, 175, 0.25)'
                      }}>
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h3 className="font-semibold text-lg mb-1" style={{ color: '#f3f8ff' }}>
                              {workspace.name}
                            </h3>
                            <p className="text-sm mb-2" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                              {workspace.description || 'No description'}
                            </p>
                            <div className="flex gap-4 text-sm">
                              <span style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                                Owner: <span style={{ color: '#32beff' }}>{workspace.owner_email}</span>
                              </span>
                              <span style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                                Created: {new Date(workspace.created_at).toLocaleDateString('en-GB')}
                              </span>
                            </div>
                          </div>
                          <div>
                            <button
                              onClick={() => handleDeleteWorkspace(workspace.workspace_id)}
                              className="p-2 rounded transition-all"
                              style={{ background: 'rgba(255, 107, 107, 0.15)', color: '#ff6b6b' }}
                              title="Delete Workspace"
                            >
                              <Trash2 size={18} />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {workspaces.length === 0 && (
                    <div className="text-center py-8">
                      <FolderOpen className="mx-auto mb-2" size={32} style={{ color: 'rgba(228, 247, 238, 0.45)' }} />
                      <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>No workspaces found</p>
                    </div>
                  )}
                </div>
              )}

              {/* DATASETS MANAGEMENT */}
              {activeSection === 'datasets' && (
                <div>
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold mb-2" style={{ color: '#f3f8ff' }}>Datasets Management</h2>
                    <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                      View datasets for each workspace, download, and manage data
                    </p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(142, 228, 175, 0.25)' }}>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Workspace</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Filename</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Samples</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Owner</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Uploaded</th>
                          <th className="text-right p-3" style={{ color: '#2bf06f' }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {datasets.map((dataset, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid rgba(142, 228, 175, 0.15)' }}>
                            <td className="p-3" style={{ color: '#f3f8ff' }}>{dataset.workspace_name}</td>
                            <td className="p-3" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>{dataset.filename}</td>
                            <td className="p-3" style={{ color: '#2bf06f' }}>{dataset.sample_count}</td>
                            <td className="p-3" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>{dataset.owner_email}</td>
                            <td className="p-3" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                              {new Date(dataset.uploaded_at).toLocaleDateString('en-GB')}
                            </td>
                            <td className="p-3 text-right">
                              <div className="flex justify-end gap-2">
                                <button
                                  onClick={() => handleDownloadDataset(dataset.workspace_id, dataset.workspace_name, 'csv')}
                                  className="p-2 rounded transition-all"
                                  style={{ background: 'rgba(50, 244, 122, 0.15)', color: '#2bf06f' }}
                                  title="Download as CSV"
                                >
                                  <Download size={16} />
                                </button>
                                <button
                                  onClick={() => handleDeleteDataset(dataset.workspace_id, dataset.checksum, dataset.filename)}
                                  className="p-2 rounded transition-all"
                                  style={{ background: 'rgba(255, 107, 107, 0.15)', color: '#ff6b6b' }}
                                  title="Delete Dataset"
                                >
                                  <Trash2 size={16} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {datasets.length === 0 && (
                    <div className="text-center py-8">
                      <Database className="mx-auto mb-2" size={32} style={{ color: 'rgba(228, 247, 238, 0.45)' }} />
                      <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>No datasets found</p>
                    </div>
                  )}
                </div>
              )}

              {/* MODELS MANAGEMENT */}
              {activeSection === 'models' && (
                <div>
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold mb-2" style={{ color: '#f3f8ff' }}>Model Management</h2>
                    <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                      View all model versions, accuracy/F1 scores, and delete models
                    </p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(142, 228, 175, 0.25)' }}>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Workspace</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Model Name</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Version</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Accuracy</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>F1 Score</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Saved At</th>
                          <th className="text-right p-3" style={{ color: '#2bf06f' }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {models.map((model, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid rgba(142, 228, 175, 0.15)' }}>
                            <td className="p-3" style={{ color: '#f3f8ff' }}>{model.workspace_name}</td>
                            <td className="p-3" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>{model.model_name}</td>
                            <td className="p-3 font-mono text-xs" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                              {model.version || 'N/A'}
                            </td>
                            <td className="p-3" style={{ color: '#2bf06f' }}>
                              {typeof model.accuracy === 'number' ? `${(model.accuracy * 100).toFixed(2)}%` : model.accuracy}
                            </td>
                            <td className="p-3" style={{ color: '#2bf06f' }}>
                              {typeof model.f1_score === 'number' ? `${(model.f1_score * 100).toFixed(2)}%` : model.f1_score}
                            </td>
                            <td className="p-3" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                              {model.saved_at ? new Date(model.saved_at).toLocaleString('en-GB', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit'
                              }) : 'N/A'}
                            </td>
                            <td className="p-3 text-right">
                              <button
                                onClick={() => handleDeleteModel(model._id, model.model_index, model.model_name)}
                                className="p-2 rounded transition-all"
                                style={{ background: 'rgba(255, 107, 107, 0.15)', color: '#ff6b6b' }}
                                title="Delete Model"
                              >
                                <Trash2 size={16} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {models.length === 0 && (
                    <div className="text-center py-8">
                      <BarChart3 className="mx-auto mb-2" size={32} style={{ color: 'rgba(228, 247, 238, 0.45)' }} />
                      <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>No model data found</p>
                    </div>
                  )}
                </div>
              )}

              {/* ACTIVITY LOGS */}
              {activeSection === 'logs' && (
                <div>
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold mb-2" style={{ color: '#f3f8ff' }}>Activity Logs</h2>
                    <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                      Track who uploaded datasets, retrained models, and corrected feedback
                    </p>
                  </div>

                  {/* Upload Logs */}
                  <div className="mb-8">
                    <h3 className="text-xl font-semibold mb-4" style={{ color: '#32beff' }}>
                      📁 Who Uploaded Dataset?
                    </h3>
                    <div className="space-y-2">
                      {uploadLogs.slice(0, 10).map((log, idx) => (
                        <div key={idx} className="p-3 rounded border" style={{
                          background: 'rgba(50, 186, 255, 0.05)',
                          borderColor: 'rgba(50, 186, 255, 0.25)'
                        }}>
                          <div className="flex justify-between items-start">
                            <div>
                              <p style={{ color: '#f3f8ff' }}>
                                <span style={{ color: '#32beff' }}>{log.owner_email}</span> uploaded to{' '}
                                <span style={{ color: '#ffba32' }}>{log.workspace_name}</span>
                              </p>
                              <p className="text-sm mt-1" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                                {log.sample_count} samples
                              </p>
                            </div>
                            <span className="text-xs" style={{ color: 'rgba(228, 247, 238, 0.55)' }}>
                              {log.uploaded_at !== 'Invalid Date' ? new Date(log.uploaded_at).toLocaleString('en-GB') : 'Invalid Date'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Training Logs */}
                  <div className="mb-8">
                    <h3 className="text-xl font-semibold mb-4" style={{ color: '#ffba32' }}>
                      🤖 Who Retrained Model?
                    </h3>
                    <div className="space-y-2">
                      {trainingLogs.slice(0, 10).map((log, idx) => (
                        <div key={idx} className="p-3 rounded border" style={{
                          background: 'rgba(255, 186, 50, 0.05)',
                          borderColor: 'rgba(255, 186, 50, 0.25)'
                        }}>
                          <div className="flex justify-between items-start">
                            <div>
                              <p style={{ color: '#f3f8ff' }}>
                                Trained <span style={{ color: '#2bf06f' }}>{log.model_name}</span>{' '}
                                <span className="text-sm" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>({log.version})</span> in{' '}
                                <span style={{ color: '#ffba32' }}>{log.workspace_name}</span>
                              </p>
                              <p className="text-sm mt-1" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                                Accuracy: <span style={{ color: '#2bf06f' }}>{(log.accuracy * 100).toFixed(2)}%</span>
                                {' | '}
                                F1: <span style={{ color: '#2bf06f' }}>{(log.f1_score * 100).toFixed(2)}%</span>
                              </p>
                            </div>
                            <span className="text-xs" style={{ color: 'rgba(228, 247, 238, 0.55)' }}>
                              {log.saved_at ? new Date(log.saved_at).toLocaleString('en-GB') : 'N/A'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Feedback Correction Logs */}
                  <div className="mb-8">
                    <h3 className="text-xl font-semibold mb-4" style={{ color: '#2bf06f' }}>
                      🔄 Who Corrected Feedback?
                    </h3>
                    <div className="space-y-2">
                      {correctionLogs.slice(0, 10).map((log, idx) => (
                        <div key={idx} className="p-3 rounded border" style={{
                          background: 'rgba(50, 244, 122, 0.05)',
                          borderColor: 'rgba(50, 244, 122, 0.25)'
                        }}>
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <p style={{ color: '#f3f8ff' }}>
                                <span style={{ color: '#32beff' }}>{log.owner_email}</span> corrected prediction in{' '}
                                <span style={{ color: '#ffba32' }}>{log.workspace_name}</span>
                              </p>
                              <p className="text-sm mt-1" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>
                                "{log.text}"
                              </p>
                              <p className="text-xs mt-1" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                                <span style={{ color: '#ff6b6b' }}>{log.predicted}</span> → <span style={{ color: '#2bf06f' }}>{log.corrected}</span>
                              </p>
                            </div>
                            <span className="text-xs" style={{ color: 'rgba(228, 247, 238, 0.55)' }}>
                              {log.created_at ? new Date(log.created_at).toLocaleString('en-GB') : 'N/A'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Active Learning Correction Logs */}
                  <div>
                    <h3 className="text-xl font-semibold mb-4" style={{ color: '#a78bfa' }}>
                      🎯 Active Learning Corrections
                    </h3>
                    <div className="space-y-2">
                      {activeLearningLogs.slice(0, 10).map((log, idx) => (
                        <div key={idx} className="p-3 rounded border" style={{
                          background: 'rgba(167, 139, 250, 0.05)',
                          borderColor: 'rgba(167, 139, 250, 0.25)'
                        }}>
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <p style={{ color: '#f3f8ff' }}>
                                <span style={{ color: '#32beff' }}>{log.owner_email}</span> corrected in{' '}
                                <span style={{ color: '#ffba32' }}>{log.workspace_name}</span>
                              </p>
                              <p className="text-sm mt-1" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>
                                "{log.text}"
                              </p>
                              <p className="text-xs mt-1" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                                <span style={{ color: '#ff6b6b' }}>{log.predicted}</span> → <span style={{ color: '#2bf06f' }}>{log.corrected}</span>
                              </p>
                            </div>
                            <span className="text-xs" style={{ color: 'rgba(228, 247, 238, 0.55)' }}>
                              {log.created_at ? new Date(log.created_at).toLocaleString('en-GB') : 'N/A'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {uploadLogs.length === 0 && correctionLogs.length === 0 && activeLearningLogs.length === 0 && trainingLogs.length === 0 && (
                    <div className="text-center py-8">
                      <Activity className="mx-auto mb-2" size={32} style={{ color: 'rgba(228, 247, 238, 0.45)' }} />
                      <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>No activity logs found</p>
                    </div>
                  )}
                </div>
              )}

              {/* ANNOTATED DATA */}
              {activeSection === 'annotations' && (
                <div>
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold mb-2" style={{ color: '#f3f8ff' }}>Annotated Data</h2>
                    <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                      View all annotations created by users across workspaces
                    </p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(142, 228, 175, 0.25)' }}>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Dataset Name</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Owner</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Sentence</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Intent</th>
                          <th className="text-left p-3" style={{ color: '#2bf06f' }}>Entities</th>
                        </tr>
                      </thead>
                      <tbody>
                        {annotations.map((ann, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid rgba(142, 228, 175, 0.15)' }}>
                            <td className="p-3" style={{ color: '#f3f8ff' }}>{ann.dataset_filename || 'Unknown'}</td>
                            <td className="p-3" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>{ann.owner_email || 'Unknown'}</td>
                            <td className="p-3" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>
                              {ann.sentence || 'N/A'}
                            </td>
                            <td className="p-3" style={{ color: '#2bf06f' }}>{ann.intent || 'N/A'}</td>
                            <td className="p-3" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>
                              {ann.entities && ann.entities.length > 0 ? (
                                <div className="flex flex-col gap-2">
                                  {ann.entities.map((entity, i) => (
                                    <div key={i} className="flex items-center gap-2 p-2 rounded text-xs" style={{
                                      background: 'rgba(50, 190, 255, 0.15)',
                                      borderLeft: '3px solid #32beff'
                                    }}>
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2">
                                          <span className="font-semibold" style={{ color: '#32beff' }}>
                                            {entity.text || entity.value || 'N/A'}
                                          </span>
                                          <span style={{ color: 'rgba(228, 247, 238, 0.5)' }}>→</span>
                                          <span className="px-2 py-0.5 rounded" style={{
                                            background: 'rgba(43, 240, 111, 0.2)',
                                            color: '#2bf06f'
                                          }}>
                                            {entity.label || entity.entity || 'unknown'}
                                          </span>
                                        </div>
                                        {entity.confidence && (
                                          <div className="mt-1" style={{ color: 'rgba(228, 247, 238, 0.6)' }}>
                                            Confidence: {typeof entity.confidence === 'number' 
                                              ? (entity.confidence * 100).toFixed(1) + '%' 
                                              : entity.confidence}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <span style={{ color: 'rgba(228, 247, 238, 0.5)' }}>No entities</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {annotations.length === 0 && (
                    <div className="text-center py-8">
                      <Check className="mx-auto mb-2" size={32} style={{ color: 'rgba(228, 247, 238, 0.45)' }} />
                      <p style={{ color: 'rgba(228, 247, 238, 0.65)' }}>No annotations found</p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Reset Password Modal */}
      {resetPasswordUser && (
        <div className="fixed inset-0 flex items-center justify-center z-50" style={{ background: 'rgba(0, 0, 0, 0.75)' }}>
          <div className="card max-w-md w-full mx-4 p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold" style={{ color: '#f3f8ff' }}>Reset Password</h3>
              <button onClick={() => { setResetPasswordUser(null); setNewPassword(''); setShowPassword(false); }}>
                <X size={20} style={{ color: 'rgba(228, 247, 238, 0.65)' }} />
              </button>
            </div>
            <p className="mb-4" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>
              Reset password for <span style={{ color: '#32beff' }}>{resetPasswordUser}</span>
            </p>
            <div className="relative mb-4">
              <input
                type={showPassword ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
                className="input-field pr-12"
                style={{ color: '#f7fbff' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 p-2 rounded transition-all"
                style={{ color: 'rgba(228, 247, 238, 0.65)' }}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleResetPassword}
                className="btn-primary flex-1"
              >
                Reset Password
              </button>
              <button
                onClick={() => { setResetPasswordUser(null); setNewPassword(''); setShowPassword(false); }}
                className="px-4 py-2 rounded"
                style={{ background: 'rgba(255, 107, 107, 0.15)', color: '#ff6b6b' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
