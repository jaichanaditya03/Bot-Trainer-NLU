import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { 
  Upload, FileText, BarChart3, Plus, RefreshCw, 
  Database, Settings, Brain, Target, Grid, Loader2, MessageSquare 
} from 'lucide-react';
import { Card, CardHeader } from '../components/common/Card';
import { Loader } from '../components/common/Loader';
import { workspaceService } from '../services/workspaceService';
import { datasetService } from '../services/datasetService';
import { trainingService } from '../services/trainingService';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';
import { useWorkspaceStore } from '../store/workspaceStore';
import { useDatasetStore } from '../store/datasetStore';

// Shared model options constant
const MODEL_OPTIONS = [
  { id: 'spacy', name: 'spaCy' },
  { id: 'rasa', name: 'Rasa' },
  { id: 'nert', name: 'NERT (CRF)' },
];

export const DashboardPage = () => {
  const user = useAuthStore((state) => state.user);
  const [activeTab, setActiveTab] = useState('upload');
  const [loading, setLoading] = useState(false);
  const [evaluationResults, setEvaluationResults] = useState(null);
  const [modelHistory, setModelHistory] = useState([]);

  const tabs = [
    { id: 'upload', label: 'Upload Data', icon: Upload },
    { id: 'view', label: 'View Data', icon: FileText },
    { id: 'annotate', label: 'Annotate', icon: Target },
    { id: 'evaluate', label: 'Evaluate', icon: BarChart3 },
    { id: 'matrix', label: 'Matrix & Comparison', icon: Grid },
    { id: 'model-comparison', label: 'Model Comparison', icon: BarChart3 },
    { id: 'active-learning', label: 'Active Learning', icon: RefreshCw },
    { id: 'feedback', label: 'Feedback', icon: MessageSquare },
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="shadow-sm" style={{ background: 'var(--glass-bg)', borderBottom: '1px solid var(--glass-border)', backdropFilter: 'blur(10px)' }}>
        <div className="max-w-7xl mx-auto px-6 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard 📊</h1>
          <p className="text-gray-600 mt-1">Welcome back, {user?.username}! 👋</p>
        </div>
      </div>

      {/* Workspace Selector */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <WorkspaceSelector />
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-6">
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b overflow-x-auto">
            <div className="flex">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 font-medium whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <tab.icon size={20} />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6">
            {activeTab === 'upload' && <UploadTab />}
            {activeTab === 'view' && <ViewDataTab />}
            {activeTab === 'annotate' && <AnnotateTab />}
            {activeTab === 'evaluate' && <EvaluateTab onResultsReady={setEvaluationResults} onAddToHistory={(historyItem) => setModelHistory([...modelHistory, historyItem])} />}
            {activeTab === 'matrix' && <MatrixComparisonTab results={evaluationResults} />}
            {activeTab === 'model-comparison' && <ModelComparisonTab history={modelHistory} />}
            {activeTab === 'active-learning' && <ActiveLearningTab evaluationResults={evaluationResults} />}
            {activeTab === 'feedback' && <FeedbackTab />}
          </div>
        </div>
      </div>
    </div>
  );
};

// Workspace Selector Component
const WorkspaceSelector = () => {
  const { workspaces, selectedWorkspace, setWorkspaces, setSelectedWorkspace } = useWorkspaceStore();
  const { clearDatasets } = useDatasetStore();
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newWorkspace, setNewWorkspace] = useState({ name: '', description: '' });

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const fetchWorkspaces = async () => {
    setLoading(true);
    try {
      const data = await workspaceService.getWorkspaces();
      setWorkspaces(data.workspaces || []);
      if (data.selected_workspace_id) {
        const selected = data.workspaces.find(w => w.id === data.selected_workspace_id);
        setSelectedWorkspace(selected);
      }
    } catch (error) {
      toast.error('Failed to load workspaces');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectWorkspace = async (workspace) => {
    try {
      await workspaceService.selectWorkspace(workspace.id);
      setSelectedWorkspace(workspace);
      clearDatasets(); // Clear datasets when switching workspaces
      toast.success(`Switched to workspace: ${workspace.name}`);
      console.log(`✅ Workspace switched to: ${workspace.name} (ID: ${workspace.id})`);
    } catch (error) {
      console.error('Workspace selection error:', error);
      toast.error('Failed to switch workspace: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateWorkspace = async () => {
    if (!newWorkspace.name.trim()) {
      toast.error('Workspace name is required');
      return;
    }

    try {
      await workspaceService.createWorkspace(newWorkspace.name, newWorkspace.description);
      toast.success('Workspace created successfully');
      setShowCreateForm(false);
      setNewWorkspace({ name: '', description: '' });
      fetchWorkspaces();
    } catch (error) {
      toast.error('Failed to create workspace');
    }
  };

  return (
    <Card>
      <CardHeader 
        title="Workspaces" 
        action={
          <button 
            onClick={() => setShowCreateForm(!showCreateForm)} 
            className="btn-primary flex items-center gap-2"
          >
            {showCreateForm ? 'Cancel' : 'New Workspace'}
          </button>
        }
      />

      {/* Create Workspace Form - Inline Dropdown */}
      {showCreateForm && (
        <div className="mb-6 p-4 rounded-lg border" style={{ 
          background: 'rgba(50, 244, 122, 0.08)', 
          borderColor: 'rgba(50, 244, 122, 0.35)' 
        }}>
          <h3 className="text-lg font-semibold mb-4" style={{ color: '#f3f8ff' }}>Create New Workspace</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#f3f8ff' }}>
                Workspace Name
              </label>
              <input
                type="text"
                value={newWorkspace.name}
                onChange={(e) => setNewWorkspace({ ...newWorkspace, name: e.target.value })}
                className="input-field w-full"
                placeholder="Enter workspace name"
                style={{ color: '#f7fbff' }}
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#f3f8ff' }}>
                Description (Optional)
              </label>
              <textarea
                value={newWorkspace.description}
                onChange={(e) => setNewWorkspace({ ...newWorkspace, description: e.target.value })}
                className="input-field w-full"
                rows={3}
                placeholder="Enter description"
                style={{ color: '#f7fbff' }}
              />
            </div>
            <div className="flex gap-3">
              <button onClick={handleCreateWorkspace} className="btn-primary flex-1">
                Create Workspace
              </button>
              <button 
                onClick={() => {
                  setShowCreateForm(false);
                  setNewWorkspace({ name: '', description: '' });
                }} 
                className="flex-1 px-4 py-2 rounded"
                style={{ background: 'rgba(255, 107, 107, 0.15)', color: '#ff6b6b' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <Loader text="Loading workspaces..." />
      ) : (
        <div className="grid md:grid-cols-3 gap-4">
          {workspaces.map((workspace) => (
            <div
              key={workspace.id}
              onClick={() => handleSelectWorkspace(workspace)}
              className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                selectedWorkspace?.id === workspace.id
                  ? 'border-primary-600'
                  : 'hover:border-primary-300'
              }`}
              style={
                selectedWorkspace?.id === workspace.id
                  ? { 
                      background: 'rgba(50, 244, 122, 0.15)',
                      borderColor: 'var(--accent)',
                      boxShadow: '0 0 20px rgba(50, 244, 122, 0.2)'
                    }
                  : { 
                      background: 'rgba(255, 255, 255, 0.04)',
                      borderColor: 'rgba(255, 255, 255, 0.15)'
                    }
              }
            >
              <div className="flex items-start gap-3">
                <Database className="mt-1" style={{ color: 'var(--accent)' }} size={24} />
                <div className="flex-1">
                  <h4 className="font-semibold" style={{ 
                    color: selectedWorkspace?.id === workspace.id ? '#04130a' : '#f3f8ff'
                  }}>
                    {workspace.name}
                  </h4>
                  {workspace.description && (
                    <p className="text-sm mt-1" style={{ 
                      color: selectedWorkspace?.id === workspace.id 
                        ? 'rgba(4, 19, 10, 0.7)' 
                        : 'rgba(243, 248, 255, 0.7)'
                    }}>
                      {workspace.description}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};

// Upload Tab Component
const UploadTab = () => {
  const selectedWorkspace = useWorkspaceStore((state) => state.selectedWorkspace);
  const { addUploadedFile } = useDatasetStore();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const parseCSV = (text) => {
    const lines = text.split('\n').filter(line => line.trim());
    if (lines.length === 0) return [];
    
    const headers = lines[0].split(',').map(h => h.trim());
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      const row = {};
      headers.forEach((header, index) => {
        row[header] = values[index] || '';
      });
      data.push(row);
    }
    
    return data;
  };

  const analyzeData = (data, filename) => {
    // Find text/sentence columns
    const textFields = ['text', 'sentence', 'utterance', 'query', 'message', 'input'];
    const intentFields = ['intent', 'label', 'category', 'class'];
    const entityFields = ['entity', 'entities', 'ner', 'tags'];
    
    const columns = data.length > 0 ? Object.keys(data[0]) : [];
    
    const textCol = columns.find(col => 
      textFields.some(field => col.toLowerCase().includes(field))
    );
    
    const intentCols = columns.filter(col =>
      intentFields.some(field => col.toLowerCase().includes(field))
    );
    
    const entityCols = columns.filter(col =>
      entityFields.some(field => col.toLowerCase().includes(field))
    );
    
    // Extract sentences
    const sentences = textCol 
      ? data.map(row => row[textCol]).filter(s => s)
      : [];
    
    // Extract unique intents
    const intents = intentCols.length > 0
      ? [...new Set(data.flatMap(row => intentCols.map(col => row[col])).filter(v => v))]
      : [];
    
    // Extract unique entities
    const entities = entityCols.length > 0
      ? [...new Set(data.flatMap(row => entityCols.map(col => row[col])).filter(v => v))]
      : [];
    
    // Create analysis object
    return {
      stats: {
        rows: data.length,
        columns: columns.length,
      },
      sample: data.slice(0, 50),
      full_sentences: sentences,
      full_records: data,
      intent_columns: intentCols,
      entity_columns: entityCols,
      intents: intents,
      entities: entities,
      intent_distribution: [],
      entity_distribution: [],
    };
  };

  const handleUpload = async () => {
    if (!selectedWorkspace) {
      toast.error('Please select a workspace first');
      return;
    }

    if (!file) {
      toast.error('Please select a file');
      return;
    }

    setLoading(true);
    try {
      const reader = new FileReader();
      
      reader.onload = async (e) => {
        try {
          const content = e.target.result;
          let data = [];
          
          // Parse based on file type
          if (file.name.endsWith('.json')) {
            data = JSON.parse(content);
            if (!Array.isArray(data)) {
              data = [data];
            }
          } else if (file.name.endsWith('.csv')) {
            data = parseCSV(content);
          }
          
          // Analyze the data
          const analysis = analyzeData(data, file.name);
          
          // Prepare payload
          const payload = {
            filename: file.name,
            analysis: analysis,
            evaluation: {},
          };
          
          // Upload to backend
          await datasetService.uploadDataset(payload);
          toast.success('Dataset uploaded successfully!');
          
          // Notify store about new upload
          addUploadedFile({
            filename: file.name,
            uploadedAt: new Date().toISOString(),
          });
          
          setFile(null);
          
          // Refresh the file input
          const fileInput = document.getElementById('file-upload');
          if (fileInput) fileInput.value = '';
        } catch (error) {
          console.error('Error processing file:', error);
          toast.error('Failed to process file: ' + error.message);
        } finally {
          setLoading(false);
        }
      };
      
      reader.onerror = () => {
        toast.error('Failed to read file');
        setLoading(false);
      };
      
      reader.readAsText(file);
    } catch (error) {
      toast.error('Failed to upload dataset');
      setLoading(false);
    }
  };

  if (!selectedWorkspace) {
    return (
      <div className="text-center py-12">
        <Settings className="mx-auto text-gray-400 mb-4" size={48} />
        <p className="text-gray-600">Please select a workspace to upload datasets</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Upload Training Dataset</h3>
        <p className="text-gray-600 text-sm">Supported formats: CSV and JSON</p>
      </div>

      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-500 transition-colors">
        <Upload className="mx-auto text-gray-400 mb-4" size={48} />
        <input
          type="file"
          accept=".csv,.json"
          onChange={handleFileChange}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload" className="btn-primary cursor-pointer inline-block">
          Choose File
        </label>
        {file && (
          <p className="mt-4 text-sm text-gray-600">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}
      </div>

      {file && (
        <button
          onClick={handleUpload}
          disabled={loading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading ? <Loader size="sm" /> : 'Upload Dataset'}
        </button>
      )}
    </div>
  );
};

// View Data Tab Component
const ViewDataTab = () => {
  const selectedWorkspace = useWorkspaceStore((state) => state.selectedWorkspace);
  const { datasets, setDatasets, selectedDataset, setSelectedDataset, uploadedFiles } = useDatasetStore();
  const [loading, setLoading] = useState(false);
  const [datasetContent, setDatasetContent] = useState(null);
  const [loadingContent, setLoadingContent] = useState(false);

  useEffect(() => {
    if (selectedWorkspace) {
      fetchDatasets();
    }
  }, [selectedWorkspace, uploadedFiles]); // Re-fetch when new file is uploaded

  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const data = await datasetService.getDatasets();
      const entries = data.entries || [];
      
      // Additional frontend filtering by workspace_id as safety measure
      const filteredEntries = selectedWorkspace 
        ? entries.filter(e => e.workspace_id === selectedWorkspace.id)
        : entries;
      
      setDatasets(filteredEntries);
      
      // Auto-select the first dataset or the selected one
      if (data.selected && data.selected.workspace_id === selectedWorkspace?.id) {
        setSelectedDataset(data.selected);
        fetchDatasetContent(data.selected.checksum);
      } else if (filteredEntries.length > 0) {
        setSelectedDataset(filteredEntries[0]);
        fetchDatasetContent(filteredEntries[0].checksum);
      } else {
        setSelectedDataset(null);
        setDatasetContent(null);
      }
    } catch (error) {
      toast.error('Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  const fetchDatasetContent = async (checksum) => {
    setLoadingContent(true);
    try {
      const content = await datasetService.getCompleteDataset(checksum);
      setDatasetContent(content);
    } catch (error) {
      toast.error('Failed to load dataset content');
    } finally {
      setLoadingContent(false);
    }
  };

  const handleSelectDataset = async (dataset) => {
    try {
      await datasetService.selectDataset(dataset.checksum);
      setSelectedDataset(dataset);
      fetchDatasetContent(dataset.checksum);
      toast.success(`Selected: ${dataset.filename}`);
    } catch (error) {
      toast.error('Failed to select dataset');
    }
  };

  if (!selectedWorkspace) {
    return (
      <div className="text-center py-12">
        <Settings className="mx-auto text-gray-400 mb-4" size={48} />
        <p className="text-gray-600">Please select a workspace to view datasets</p>
      </div>
    );
  }

  if (loading) {
    return <Loader text="Loading datasets..." />;
  }

  if (datasets.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="mx-auto text-gray-400 mb-4" size={48} />
        <p className="text-gray-600 mb-2">No datasets found in this workspace</p>
        <p className="text-sm text-gray-500">Upload a dataset in the Upload Data tab</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Dataset List */}
      <div>
        <h3 className="text-lg font-semibold mb-3" style={{ color: '#f3f8ff' }}>Recent Datasets</h3>
        <div className="space-y-2">
          {datasets.map((dataset) => (
            <div
              key={dataset.checksum}
              onClick={() => handleSelectDataset(dataset)}
              className="p-4 border-2 rounded-lg cursor-pointer transition-all"
              style={
                selectedDataset?.checksum === dataset.checksum
                  ? { 
                      background: 'rgba(50, 244, 122, 0.15)',
                      borderColor: 'var(--accent)',
                      boxShadow: '0 0 20px rgba(50, 244, 122, 0.2)'
                    }
                  : { 
                      background: 'rgba(255, 255, 255, 0.04)',
                      borderColor: 'rgba(255, 255, 255, 0.15)'
                    }
              }
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Database style={{ color: 'var(--accent)' }} size={24} />
                  <div>
                    <h4 className="font-semibold" style={{ 
                      color: selectedDataset?.checksum === dataset.checksum ? '#04130a' : '#f3f8ff'
                    }}>
                      {selectedDataset?.checksum === dataset.checksum && '✓ '}
                      {dataset.filename}
                    </h4>
                    <p className="text-sm" style={{ 
                      color: selectedDataset?.checksum === dataset.checksum 
                        ? 'rgba(4, 19, 10, 0.7)' 
                        : 'rgba(243, 248, 255, 0.7)'
                    }}>
                      {dataset.sentence_count || 0} sentences
                      {dataset.updated_at && (
                        <> • {new Date(dataset.updated_at).toLocaleString()}</>
                      )}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dataset Content */}
      {selectedDataset && (
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold mb-3">Dataset Preview</h3>
          
          {loadingContent ? (
            <Loader text="Loading content..." />
          ) : datasetContent ? (
            <div className="space-y-4">
              {/* Statistics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="card text-center">
                  <p className="text-sm text-gray-600">Total Rows</p>
                  <p className="text-2xl font-bold text-primary-600">
                    {datasetContent.stats?.total_rows || 0}
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-600">Columns</p>
                  <p className="text-2xl font-bold text-primary-600">
                    {datasetContent.stats?.total_columns || 0}
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-600">Intents</p>
                  <p className="text-2xl font-bold text-primary-600">
                    {datasetContent.stats?.intent_count || 0}
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-600">Entities</p>
                  <p className="text-2xl font-bold text-primary-600">
                    {datasetContent.stats?.entity_count || 0}
                  </p>
                </div>
              </div>

              {/* Full Data Table */}
              {(() => {
                const displayData = datasetContent.content?.full_records && 
                                   datasetContent.content.full_records.length > 0
                  ? datasetContent.content.full_records
                  : datasetContent.content?.sample_records || [];
                
                if (displayData.length === 0) return null;

                return (
                  <div className="card">
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="font-semibold">
                        Dataset Content ({displayData.length} rows)
                      </h4>
                      {datasetContent.content?.full_records && 
                       datasetContent.content.full_records.length > 100 && (
                        <span className="text-sm text-gray-500">
                          Showing all {displayData.length} rows
                        </span>
                      )}
                    </div>
                    <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 sticky top-0">
                          <tr>
                            <th className="px-4 py-2 text-left font-medium text-gray-700 w-12">
                              #
                            </th>
                            {Object.keys(displayData[0]).map((header) => (
                              <th key={header} className="px-4 py-2 text-left font-medium text-gray-700">
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {displayData.map((row, idx) => (
                            <tr key={idx} className="hover:bg-gray-50">
                              <td className="px-4 py-2 text-gray-500 text-xs">
                                {idx + 1}
                              </td>
                              {Object.values(row).map((value, colIdx) => (
                                <td key={colIdx} className="px-4 py-2 text-gray-600">
                                  {String(value)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                );
              })()}

              {/* Intents */}
              {datasetContent.content?.intents && 
               datasetContent.content.intents.length > 0 && (
                <div className="card">
                  <h4 className="font-semibold mb-3">Unique Intents</h4>
                  <div className="flex flex-wrap gap-2">
                    {datasetContent.content.intents.map((intent, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                      >
                        {intent}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Entities */}
              {datasetContent.content?.entities && 
               datasetContent.content.entities.length > 0 && (
                <div className="card">
                  <h4 className="font-semibold mb-3">Unique Entities</h4>
                  <div className="flex flex-wrap gap-2">
                    {datasetContent.content.entities.map((entity, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                      >
                        {entity}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-600">No content available</p>
          )}
        </div>
      )}
    </div>
  );
};

const AnnotateTab = () => {
  const selectedWorkspace = useWorkspaceStore((state) => state.selectedWorkspace);
  const selectedDataset = useDatasetStore((state) => state.selectedDataset);
  const [sentence, setSentence] = useState('');
  const [selectedModel, setSelectedModel] = useState('spacy');
  const [prediction, setPrediction] = useState(null);
  const [intent, setIntent] = useState('');
  const [customIntent, setCustomIntent] = useState('');
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [annotations, setAnnotations] = useState([]);
  const [newEntityText, setNewEntityText] = useState('');
  const [newEntityLabel, setNewEntityLabel] = useState('person');
  const [trainedModelCache, setTrainedModelCache] = useState({});

  const commonIntents = [
    'book_flight', 'book_ticket', 'cancel_ticket', 'cancel_flight', 'fare_inquiry',
    'show_schedule', 'check_status', 'status_check', 'change_ticket', 'information_request',
    'general_query', 'help_request', 'greeting', 'goodbye', 'thank_you',
    'order_food', 'cancel_order', 'track_order', 'menu_query', 'restaurant_search',
    'add_item', 'remove_item', 'modify_order', 'order_status', 'offers_query',
    'appointment_booking', 'cancel_appointment', 'change_appointment', 'doctor_search',
    'symptoms_query', 'prescription_refill', 'lab_test_booking', 'insurance_query',
    'clinic_hours', 'report_status', 'emergency_help', 'health_tips', 'medicine_info'
  ];

  const entityTypes = [
    'person', 'location', 'organization', 'date', 'time', 'cost', 'product', 'number',
    'category', 'other', 'medicine', 'symptom', 'food', 'airline', 'restaurant',
    'quantity', 'size', 'flight_number', 'source', 'destination', 'city', 'doctor',
    'specialist', 'patient', 'test'
  ];

  // Load annotations for selected dataset
  useEffect(() => {
    if (selectedDataset?.checksum) {
      loadAnnotations(selectedDataset.checksum);
    }
  }, [selectedDataset]);

  const loadAnnotations = async (checksum) => {
    try {
      const response = await api.get(`/annotations/${checksum}`);
      if (response.data?.annotations) {
        setAnnotations(response.data.annotations);
      }
    } catch (error) {
      console.error('Failed to load annotations:', error);
    }
  };

  const handlePredict = async () => {
    if (!sentence.trim()) {
      toast.error('Please enter a sentence');
      return;
    }

    setLoading(true);
    try {
      // First, ensure the model is trained for this dataset
      const trainSuccess = await ensureModelTrained();
      if (!trainSuccess) {
        setLoading(false);
        return;
      }

      // Now make the prediction
      const response = await api.post('/predict', {
        text: sentence,
        model_id: selectedModel,
        include_rules: true,
      });

      const data = response.data;
      setPrediction(data);
      
      // Set intent from prediction
      const predictedIntent = data.intent || data.label || data.predicted_intent || '';
      if (predictedIntent) {
        if (commonIntents.includes(predictedIntent)) {
          setIntent(predictedIntent);
          setCustomIntent('');
        } else {
          setIntent('');
          setCustomIntent(predictedIntent);
        }
      }
      
      // Process entities from response
      const processedEntities = (data.entities || []).map((ent) => {
        const text = ent.text || ent.word || '';
        const label = ent.label || ent.entity || ent.entity_group || 'other';
        const confidence = ent.score || ent.confidence || 'auto';
        
        // Find position in sentence
        const sentenceLower = sentence.toLowerCase();
        const textLower = text.toLowerCase();
        const start = ent.start ?? sentenceLower.indexOf(textLower);
        const end = ent.end ?? (start !== -1 ? start + text.length : -1);
        
        return {
          text,
          label: label.toLowerCase(),
          start,
          end,
          confidence,
        };
      }).filter(ent => ent.start !== -1); // Only keep entities found in sentence
      
      setEntities(processedEntities);
      toast.success(`✅ Predicted: ${predictedIntent}`);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      toast.error('Prediction failed: ' + errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const ensureModelTrained = async () => {
    if (!selectedDataset) {
      toast.error('Please select a dataset first');
      return false;
    }

    // Check cache - if this model is already trained for this dataset, skip training
    const cacheKey = `${selectedModel}_${selectedDataset.checksum}`;
    if (trainedModelCache[cacheKey]) {
      return true;
    }

    try {
      // Fetch complete dataset content with full records
      const fetchToast = toast.loading('📥 Fetching dataset...');
      const datasetContent = await datasetService.getCompleteDataset(selectedDataset.checksum);
      toast.dismiss(fetchToast);
      
      const records = datasetContent.content?.full_records || datasetContent.content?.sample_records || [];
      
      if (!records || records.length === 0) {
        toast.error('Dataset has no records');
        return false;
      }

      // Extract texts and intents - try multiple possible column names
      const texts = [];
      const labels = [];
      const trainingRecords = [];

      records.forEach(record => {
        // Try different possible column names for text
        const textValue = record.text || record.sentence || record.utterance || 
                         record.query || record.message || record.input || '';
        // Try different possible column names for intent
        const intentValue = record.intent || record.label || record.category || 
                           record.tag || '';
        
        if (textValue && intentValue) {
          const text = String(textValue).trim();
          const intent = String(intentValue).trim().toLowerCase();
          
          if (text && intent) {
            texts.push(text);
            labels.push(intent);
            
            // For NERT, include entities
            const entities = record.entities || [];
            trainingRecords.push({
              text: text,
              intent: intent,
              entities: Array.isArray(entities) ? entities : []
            });
          }
        }
      });

      if (texts.length === 0) {
        toast.error('No valid training data found. Dataset must have text and intent columns.');
        console.error('Dataset records:', records[0]); // Log first record for debugging
        return false;
      }

      // Train the model based on selected type
      let endpoint = '';
      let payload = {};
      let modelName = '';

      if (selectedModel === 'spacy') {
        endpoint = '/train/intent/spacy';
        payload = { texts, labels, epochs: 12 };
        modelName = 'spaCy textcat';
      } else if (selectedModel === 'rasa') {
        endpoint = '/train/intent/rasa-lite';
        payload = { texts, labels };
        modelName = 'Rasa-lite';
      } else if (selectedModel === 'nert') {
        endpoint = '/train/ner/nert-lite';
        payload = { records: trainingRecords };
        modelName = 'NERT-lite';
      } else {
        toast.error('Unsupported model type');
        return false;
      }

      const trainToast = toast.loading(`⚙️ Training ${modelName} with ${texts.length} samples...`);
      
      const response = await api.post(endpoint, payload);
      
      toast.dismiss(trainToast);
      
      // Cache the trained model
      setTrainedModelCache({
        ...trainedModelCache,
        [cacheKey]: true
      });
      
      toast.success(`✅ ${modelName} trained successfully!`);
      return true;

    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      console.error('Training error:', error);
      toast.error('Training failed: ' + errorMsg);
      return false;
    }
  };

  const handleAddEntity = () => {
    const text = newEntityText.trim();
    if (!text) {
      toast.error('Please enter entity text');
      return;
    }

    const sentenceLower = sentence.toLowerCase();
    const textLower = text.toLowerCase();
    const start = sentenceLower.indexOf(textLower);
    
    if (start === -1) {
      toast.error(`"${text}" not found in sentence!`);
      return;
    }

    const newEntity = {
      text,
      label: newEntityLabel,
      start,
      end: start + text.length,
      confidence: 'manual',
    };

    setEntities([...entities, newEntity]);
    setNewEntityText('');
    toast.success(`✅ Added: ${text}`);
  };

  const handleRemoveEntity = (index) => {
    setEntities(entities.filter((_, i) => i !== index));
  };

  const handleSaveAnnotation = async () => {
    const finalIntent = customIntent || intent;
    
    if (!finalIntent) {
      toast.error('Please select or enter an intent');
      return;
    }

    if (!selectedDataset?.checksum) {
      toast.error('No dataset selected');
      return;
    }

    const annotation = {
      sentence,
      intent: finalIntent,
      entities,
    };

    try {
      const payload = {
        workspace_id: selectedWorkspace?.id,
        dataset_checksum: selectedDataset.checksum,
        annotations: [annotation],
      };

      await api.post('/annotations/save', payload);
      
      // Reload annotations
      await loadAnnotations(selectedDataset.checksum);
      
      toast.success('✅ Annotation saved!');
      
      // Reset form
      setSentence('');
      setPrediction(null);
      setIntent('');
      setCustomIntent('');
      setEntities([]);
    } catch (error) {
      toast.error('Save failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleClear = () => {
    setSentence('');
    setPrediction(null);
    setIntent('');
    setCustomIntent('');
    setEntities([]);
    toast.success('🗑️ Cleared');
  };

  if (!selectedWorkspace || !selectedDataset) {
    return (
      <div className="text-center py-12">
        <Target className="mx-auto text-gray-400 mb-4" size={48} />
        <p className="text-gray-600">Please select a workspace and dataset first</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Annotation Interface */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">📝 Text Annotation</h3>
        
        {/* Model Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2" style={{ color: '#f3f8ff' }}>
            Select Model for Prediction:
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="input-field"
            style={{ color: '#f7fbff' }}
          >
            {MODEL_OPTIONS.map((model) => (
              <option key={model.id} value={model.id} style={{ background: '#1a2332', color: '#f7fbff' }}>
                {model.name}
              </option>
            ))}
          </select>
          <p className="text-xs mt-1" style={{ color: 'rgba(243, 248, 255, 0.6)' }}>Using engine: <code>{selectedModel}</code></p>
        </div>

        {/* Sentence Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Paste sentence from your dataset:
          </label>
          <input
            type="text"
            value={sentence}
            onChange={(e) => setSentence(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !loading && handlePredict()}
            className="input-field"
            placeholder="Paste text here and press Enter"
          />
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          <button
            onClick={handlePredict}
            disabled={loading || !sentence.trim()}
            className="btn-primary col-span-3 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader size="sm" />
                Analyzing...
              </>
            ) : (
              '🤖 Auto-Predict Intent & Entities'
            )}
          </button>
          <button
            onClick={handleClear}
            className="btn-secondary"
          >
            🗑️ Clear
          </button>
        </div>

        {/* Prediction Results */}
        {prediction && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded">
            <p className="text-sm font-semibold text-green-900">
              ✅ Predicted Intent: <span className="text-green-700">{prediction.intent}</span>
            </p>
            {prediction.confidence && (
              <p className="text-xs text-green-600 mt-1">
                Confidence: {(prediction.confidence * 100).toFixed(1)}%
              </p>
            )}
          </div>
        )}

        {/* Intent Selection */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">🎯 Intent Selection</h4>
          <div className="grid md:grid-cols-2 gap-3">
            <select
              value={customIntent ? '' : intent}
              onChange={(e) => {
                setIntent(e.target.value);
                setCustomIntent('');
              }}
              className="input-field"
            >
              <option value="">-- Select Intent --</option>
              {commonIntents.map((int) => (
                <option key={int} value={int}>
                  {int}
                </option>
              ))}
            </select>
            <input
              type="text"
              value={customIntent}
              onChange={(e) => {
                setCustomIntent(e.target.value);
                if (e.target.value) setIntent('');
              }}
              className="input-field"
              placeholder="Or Custom Intent"
            />
          </div>
          {(intent || customIntent) && (
            <p className="text-xs text-green-600 mt-1">
              ✓ Ready to save: {customIntent || intent}
            </p>
          )}
        </div>

        {/* Entity Display */}
        {entities.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">
              🏷️ Entity Labeling ({entities.length})
            </h4>
            <div className="space-y-2">
              {entities.map((ent, idx) => (
                <div key={idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded border">
                  <span className="text-sm">
                    {ent.confidence === 'manual' ? '✋' : '🤖'}
                  </span>
                  <span className="font-medium text-gray-900">{ent.text}</span>
                  <span className="text-gray-400">→</span>
                  <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-sm">
                    {ent.label}
                  </span>
                  <button
                    onClick={() => handleRemoveEntity(idx)}
                    className="ml-auto text-red-600 hover:text-red-700 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">🤖 = Auto-detected | ✋ = Manually added</p>
          </div>
        )}

        {/* Add Entity Manually */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Add Entity Manually</h4>
          <div className="grid grid-cols-3 gap-2">
            <input
              type="text"
              value={newEntityText}
              onChange={(e) => setNewEntityText(e.target.value)}
              className="input-field"
              placeholder="Entity text"
            />
            <select
              value={newEntityLabel}
              onChange={(e) => setNewEntityLabel(e.target.value)}
              className="input-field"
            >
              {entityTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
            <button onClick={handleAddEntity} className="btn-secondary">
              ➕ Add
            </button>
          </div>
        </div>

        {/* Save Button */}
        <button
          onClick={handleSaveAnnotation}
          disabled={!sentence || (!intent && !customIntent)}
          className="btn-primary w-full"
        >
          ✅ Save This Annotation
        </button>
      </div>

      {/* Saved Annotations List */}
      {annotations.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">
            📋 Annotated Sentences ({annotations.length} total)
          </h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {annotations.slice(0, 10).map((ann, idx) => (
              <div key={idx} className="p-3 bg-gray-50 rounded border">
                <p className="text-sm text-gray-900 font-medium mb-1">
                  {ann.sentence.length > 70 ? ann.sentence.substring(0, 70) + '...' : ann.sentence}
                </p>
                <p className="text-xs text-gray-700">
                  🎯 Intent: <span className="font-semibold text-primary-600">{ann.intent}</span>
                </p>
                {ann.entities && ann.entities.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {ann.entities.map((ent, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-xs"
                      >
                        {ent.text}: {ent.label}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          {annotations.length > 10 && (
            <p className="text-xs text-gray-500 mt-2">Showing most recent 10 annotations</p>
          )}
        </div>
      )}
    </div>
  );
};

const EvaluateTab = ({ onResultsReady, onAddToHistory }) => {
  const selectedDataset = useDatasetStore((state) => state.selectedDataset);
  const [selectedModel, setSelectedModel] = useState('spacy');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [trainPercentage, setTrainPercentage] = useState(80);

  // Clear results only when model changes
  useEffect(() => {
    setResults(null);
  }, [selectedModel]);

  const handleRunEvaluation = async () => {
    if (!selectedDataset) {
      toast.error('Please select a dataset first');
      return;
    }

    setLoading(true);
    const evaluationToast = toast.loading(`🔄 Evaluating ${MODEL_OPTIONS.find(m => m.id === selectedModel)?.name}...`);

    try {
      // Load corrections from backend
      let feedbackCorrections = {};
      try {
        const feedbackResponse = await api.get('/active-learning/corrections');
        const feedbackItems = feedbackResponse.data?.items || [];
        
        // Create a map of text -> corrected_intent for quick lookup
        feedbackItems.forEach(item => {
          if (item.corrected_intent && item.text) {
            const textKey = item.text.trim().toLowerCase();
            feedbackCorrections[textKey] = item.corrected_intent;
          }
        });
        
        if (Object.keys(feedbackCorrections).length > 0) {
          console.log(`Loaded ${Object.keys(feedbackCorrections).length} feedback corrections`);
        }
      } catch (feedbackError) {
        console.error('Failed to load feedback:', feedbackError);
        // Continue evaluation even if feedback loading fails
      }

      // Fetch complete dataset
      const datasetContent = await datasetService.getCompleteDataset(selectedDataset.checksum);
      const records = datasetContent.content?.full_records || datasetContent.content?.sample_records || [];
      
      if (!records || records.length === 0) {
        toast.dismiss(evaluationToast);
        toast.error('Dataset has no records');
        setLoading(false);
        return;
      }

      // Extract training data
      const trainingData = [];
      records.forEach(record => {
        const text = record.text || record.sentence || record.utterance || record.query || '';
        const intent = record.intent || record.label || record.category || '';
        const entities = record.entities || [];
        
        if (text && intent) {
          trainingData.push({
            text: String(text).trim(),
            intent: String(intent).trim().toLowerCase(),
            entities: Array.isArray(entities) ? entities : []
          });
        }
      });

      if (trainingData.length === 0) {
        toast.dismiss(evaluationToast);
        toast.error('No valid training data found');
        setLoading(false);
        return;
      }

      // Split data into train and test
      const trainSize = Math.floor(trainingData.length * (trainPercentage / 100));
      const trainData = trainingData.slice(0, trainSize);
      const testData = trainingData.slice(trainSize);

      // Train the model
      const trainTexts = trainData.map(d => d.text);
      const trainLabels = trainData.map(d => d.intent);

      let trainEndpoint = '';
      let trainPayload = {};

      if (selectedModel === 'spacy') {
        trainEndpoint = '/train/intent/spacy';
        trainPayload = { texts: trainTexts, labels: trainLabels, epochs: 12 };
      } else if (selectedModel === 'rasa') {
        trainEndpoint = '/train/intent/rasa-lite';
        trainPayload = { texts: trainTexts, labels: trainLabels };
      } else if (selectedModel === 'nert') {
        trainEndpoint = '/train/ner/nert-lite';
        trainPayload = { records: trainData };
      }

      await api.post(trainEndpoint, trainPayload);
      
      toast.dismiss(evaluationToast);
      toast.success(`✅ Model trained with ${trainSize} samples`);

      // Predict on test data using batch prediction
      const predictToast = toast.loading('🔮 Running predictions on test set...');
      
      const testTexts = testData.map(d => d.text);
      const testLabels = testData.map(d => d.intent);
      
      // Get unique intents from test set
      const uniqueIntents = [...new Set(testLabels)];

      const batchResponse = await api.post('/predict/batch', {
        texts: testTexts,
        model_id: selectedModel,
        allowed_intents: uniqueIntents,
        include_rules: false,
      });

      // Extract predictions with confidence scores
      const predictionDetails = batchResponse.data.predictions.map(pred => ({
        intent: (pred.intent || 'unknown').toLowerCase(),
        confidence: pred.confidence || 0.0
      }));

      let predictions = predictionDetails.map(pred => pred.intent);
      let confidenceScores = predictionDetails.map(pred => pred.confidence);

      // Apply feedback corrections to predictions
      let correctedPredictions = 0;
      predictions = predictions.map((pred, idx) => {
        const textKey = testTexts[idx].trim().toLowerCase();
        if (feedbackCorrections[textKey]) {
          correctedPredictions++;
          return feedbackCorrections[textKey];
        }
        return pred;
      });

      if (correctedPredictions > 0) {
        console.log(`Applied ${correctedPredictions} feedback corrections to predictions`);
      }

      toast.dismiss(predictToast);

      // Calculate metrics
      const correct = predictions.filter((pred, idx) => pred === testLabels[idx]).length;
      const accuracy = correct / testLabels.length;

      // Calculate per-class metrics
      const intentMetrics = {};
      uniqueIntents.forEach(intent => {
        const truePositives = predictions.filter((pred, idx) => 
          pred === intent && testLabels[idx] === intent
        ).length;
        const falsePositives = predictions.filter((pred, idx) => 
          pred === intent && testLabels[idx] !== intent
        ).length;
        const falseNegatives = predictions.filter((pred, idx) => 
          pred !== intent && testLabels[idx] === intent
        ).length;

        const precision = truePositives + falsePositives > 0 
          ? truePositives / (truePositives + falsePositives) 
          : 0;
        const recall = truePositives + falseNegatives > 0 
          ? truePositives / (truePositives + falseNegatives) 
          : 0;
        const f1 = precision + recall > 0 
          ? 2 * (precision * recall) / (precision + recall) 
          : 0;

        intentMetrics[intent] = { precision, recall, f1, support: testLabels.filter(l => l === intent).length };
      });

      // Calculate weighted average
      const totalSupport = testLabels.length;
      let weightedPrecision = 0;
      let weightedRecall = 0;
      let weightedF1 = 0;

      Object.entries(intentMetrics).forEach(([intent, metrics]) => {
        const weight = metrics.support / totalSupport;
        weightedPrecision += metrics.precision * weight;
        weightedRecall += metrics.recall * weight;
        weightedF1 += metrics.f1 * weight;
      });

      // Prepare results with mismatches including confidence scores
      const mismatches = testData
        .map((item, idx) => ({
          text: item.text,
          true: testLabels[idx],
          predicted: predictions[idx],
          confidence: confidenceScores[idx] || 0.0,
          correct: testLabels[idx] === predictions[idx]
        }))
        .filter(item => !item.correct);

      // Build confusion matrix
      const confusionMatrix = uniqueIntents.map(trueIntent => 
        uniqueIntents.map(predIntent => 
          predictions.filter((pred, idx) => 
            testLabels[idx] === trueIntent && pred === predIntent
          ).length
        )
      );

      const evaluationResults = {
        model_name: MODEL_OPTIONS.find(m => m.id === selectedModel)?.name,
        model_id: selectedModel,
        accuracy,
        precision: weightedPrecision,
        recall: weightedRecall,
        f1: weightedF1,
        train_size: trainSize,
        test_size: testLabels.length,
        correct_predictions: correct,
        incorrect_predictions: testLabels.length - correct,
        per_class_metrics: intentMetrics,
        confusion_matrix: confusionMatrix,
        labels: uniqueIntents,
        sample_predictions: testData.map((item, idx) => ({
          text: item.text,
          true: testLabels[idx],
          predicted: predictions[idx],
          confidence: confidenceScores[idx] || 0.0,
          match: testLabels[idx] === predictions[idx]
        })),
        display_predictions: testData.slice(0, 15).map((item, idx) => ({
          text: item.text,
          true: testLabels[idx],
          predicted: predictions[idx],
          confidence: confidenceScores[idx] || 0.0,
          match: testLabels[idx] === predictions[idx]
        })),
        mismatches: mismatches
      };

      setResults(evaluationResults);
      
      // Pass results to parent for Matrix & Comparison tab
      if (onResultsReady) {
        onResultsReady(evaluationResults);
      }

      // Add to model history for Model Comparison tab
      if (onAddToHistory) {
        const historyItem = {
          version: `v${Date.now()}`,
          model_name: evaluationResults.model_name,
          accuracy: (evaluationResults.accuracy * 100).toFixed(2) + '%',
          f1: (evaluationResults.f1 * 100).toFixed(2) + '%',
          train_samples: evaluationResults.train_size,
          test_samples: evaluationResults.test_size,
          timestamp: new Date().toLocaleString(),
          raw_accuracy: evaluationResults.accuracy,
          raw_f1: evaluationResults.f1,
          precision: evaluationResults.precision,
          recall: evaluationResults.recall,
        };
        onAddToHistory(historyItem);
      }

      toast.success(`✅ Evaluation complete! Accuracy: ${(accuracy * 100).toFixed(1)}%`);
    } catch (error) {
      toast.dismiss(evaluationToast);
      const errorMsg = error.response?.data?.detail || error.message;
      toast.error('Evaluation failed: ' + errorMsg);
      console.error('Evaluation error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!selectedDataset) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="mx-auto text-gray-400 mb-4" size={48} />
        <p className="text-gray-600">Please select a dataset in View Data tab first</p>
      </div>
    );
  }

  const testPercentage = 100 - trainPercentage;
  const totalRecords = selectedDataset.sentence_count || 0;
  const trainCount = Math.floor(totalRecords * (trainPercentage / 100));
  const testCount = totalRecords - trainCount;

  return (
    <div className="space-y-6">
      {/* Model Selection */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">🤖 Model Selection</h3>
        
        <div className="mb-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Model
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="input-field"
          >
            {MODEL_OPTIONS.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">Engine: <code>{selectedModel}</code></p>
        </div>
      </div>

      {/* Train/Test Split Configuration */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">📊 Dataset Split Configuration</h3>
        <p className="text-sm text-gray-600 mb-4">Configure how to split your dataset for training and testing</p>
        
        <div className="grid md:grid-cols-2 gap-6 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Training Data (%)
            </label>
            <input
              type="range"
              min="50"
              max="90"
              step="5"
              value={trainPercentage}
              onChange={(e) => setTrainPercentage(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>50%</span>
              <span className="font-semibold text-primary-600">{trainPercentage}%</span>
              <span>90%</span>
            </div>
            <div className="mt-3 text-center p-4 bg-blue-50 rounded">
              <p className="text-sm text-gray-600">Training Samples</p>
              <p className="text-3xl font-bold text-blue-600">{trainCount}</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Testing Data: {testPercentage}%
            </label>
            <p className="text-xs text-gray-500 mb-2"></p>
            <div className="h-2 bg-gray-200 rounded-lg mt-[27px]">
              <div 
                className="h-full bg-orange-400 rounded-lg transition-all duration-300"
                style={{ width: `${testPercentage}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>10%</span>
              <span className="font-semibold text-orange-600">{testPercentage}%</span>
              <span>50%</span>
            </div>
            <div className="mt-3 text-center p-4 bg-orange-50 rounded">
              <p className="text-sm text-gray-600">Testing Samples</p>
              <p className="text-3xl font-bold text-orange-600">{testCount}</p>
            </div>
          </div>
        </div>

        {/* Visual Progress Bar */}
        <div className="relative pt-1">
          <div className="flex mb-2 items-center justify-between">
            <div>
              <span className="text-xs font-semibold inline-block text-blue-600">
                Train: {trainPercentage}%
              </span>
            </div>
            <div>
              <span className="text-xs font-semibold inline-block text-orange-600">
                Test: {testPercentage}%
              </span>
            </div>
          </div>
          <div className="flex h-3 mb-4 overflow-hidden text-xs bg-gray-200 rounded">
            <div 
              style={{ width: `${trainPercentage}%` }} 
              className="flex flex-col justify-center bg-blue-500 text-white text-center transition-all duration-300"
            />
            <div 
              style={{ width: `${testPercentage}%` }} 
              className="flex flex-col justify-center bg-orange-500 text-white text-center transition-all duration-300"
            />
          </div>
        </div>

        <button
          onClick={handleRunEvaluation}
          disabled={loading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader size="sm" />
              Evaluating...
            </>
          ) : (
            '🚀 Run Evaluation'
          )}
        </button>
      </div>

      {/* Results */}
      {results && (
        <>
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">📊 Evaluation Results</h3>
            
            <div className="mb-4">
              <p className="text-sm"><strong>Model:</strong> {results.model_name}</p>
              <p className="text-sm text-gray-600">
                Samples: Training: {results.train_size.toLocaleString()} | Testing: {results.test_size.toLocaleString()}
              </p>
            </div>

            {/* Overall Metrics */}
            <h4 className="font-semibold mb-3">📈 Overall Performance Metrics</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-blue-50 rounded">
                <p className="text-sm text-gray-600">Accuracy</p>
                <p className="text-3xl font-bold text-blue-600">
                  {(results.accuracy * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded">
                <p className="text-sm text-gray-600">Precision</p>
                <p className="text-3xl font-bold text-green-600">
                  {(results.precision * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded">
                <p className="text-sm text-gray-600">Recall</p>
                <p className="text-3xl font-bold text-purple-600">
                  {(results.recall * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded">
                <p className="text-sm text-gray-600">F1-Score</p>
                <p className="text-3xl font-bold text-orange-600">
                  {(results.f1 * 100).toFixed(1)}%
                </p>
              </div>
            </div>

            {/* Per-Class Metrics */}
            <h4 className="font-semibold mb-3">📋 Per-Intent Performance</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Intent</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Precision</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Recall</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">F1-Score</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Support</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {Object.entries(results.per_class_metrics).map(([intent, metrics]) => (
                    <tr key={intent} className="hover:bg-gray-50">
                      <td className="px-4 py-2 font-medium text-gray-900">{intent}</td>
                      <td className="px-4 py-2 text-gray-600">{(metrics.precision * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2 text-gray-600">{(metrics.recall * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2 text-gray-600">{(metrics.f1 * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2 text-gray-600">{metrics.support}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Prediction Analysis */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">🔍 Prediction Analysis</h3>
            
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center p-3 bg-green-50 rounded">
                <p className="text-sm text-gray-600">✅ Correct</p>
                <p className="text-2xl font-bold text-green-600">{results.correct_predictions}</p>
              </div>
              <div className="text-center p-3 bg-red-50 rounded">
                <p className="text-sm text-gray-600">❌ Incorrect</p>
                <p className="text-2xl font-bold text-red-600">{results.incorrect_predictions}</p>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded">
                <p className="text-sm text-gray-600">📊 Total Test</p>
                <p className="text-2xl font-bold text-blue-600">{results.test_size}</p>
              </div>
            </div>

            {/* Sample Predictions */}
            <h4 className="font-semibold mb-2">Sample Predictions</h4>
            <div className="overflow-x-auto mb-4">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Text</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">True Intent</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Predicted</th>
                    <th className="px-4 py-2 text-center font-medium text-gray-700">Match</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {results.display_predictions.map((pred, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-600">
                        {pred.text.length > 60 ? pred.text.substring(0, 60) + '...' : pred.text}
                      </td>
                      <td className="px-4 py-2 text-gray-900">{pred.true}</td>
                      <td className="px-4 py-2 text-gray-900">{pred.predicted}</td>
                      <td className="px-4 py-2 text-center">{pred.match ? '✅' : '❌'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mismatches */}
            {results.mismatches.length > 0 && (
              <>
                <h4 className="font-semibold mb-2 text-red-600">
                  ⚠️ Mismatches ({results.mismatches.length})
                </h4>
                <div className="overflow-x-auto max-h-96 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-red-50 sticky top-0">
                      <tr>
                        <th className="px-4 py-2 text-left font-medium text-gray-700">Text</th>
                        <th className="px-4 py-2 text-left font-medium text-gray-700">True Intent</th>
                        <th className="px-4 py-2 text-left font-medium text-gray-700">Predicted</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {results.mismatches.map((mismatch, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-2 text-gray-600">
                            {mismatch.text.length > 80 ? mismatch.text.substring(0, 80) + '...' : mismatch.text}
                          </td>
                          <td className="px-4 py-2 text-green-700 font-medium">{mismatch.true}</td>
                          <td className="px-4 py-2 text-red-700 font-medium">{mismatch.predicted}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
};

const MatrixComparisonTab = ({ results }) => {
  const [displayCount, setDisplayCount] = useState(null); // Start with null to show all by default

  if (!results) {
    return (
      <div className="text-center py-12">
        <Brain className="mx-auto text-gray-400 mb-4" size={48} />
        <p className="text-gray-600">No evaluation results available</p>
        <p className="text-sm text-gray-500 mt-2">
          Run an evaluation in the Evaluate tab first
        </p>
      </div>
    );
  }

  const totalSamples = results.sample_predictions?.length || 0;
  
  // Show all data by default, or limit to displayCount if slider is used
  const displayData = displayCount 
    ? results.sample_predictions?.slice(0, displayCount) || []
    : results.sample_predictions || [];

  // Helper function to get color based on value for confusion matrix
  const getColorIntensity = (value, maxValue, isDiagonal) => {
    if (value === 0) return '#f9fafb'; // Light gray for zero values
    
    // Red shades for mismatches (off-diagonal)
    if (!isDiagonal && value > 0) {
      const intensity = maxValue > 0 ? value / maxValue : 0;
      const red = 255;
      const green = Math.round(200 - (intensity * 150)); // Range from 200 to 50
      const blue = Math.round(200 - (intensity * 150));
      return `rgb(${red}, ${green}, ${blue})`;
    }
    
    // Blue shades for correct predictions (diagonal)
    const intensity = maxValue > 0 ? value / maxValue : 0;
    const blue = Math.round(255 - (intensity * 200)); // Range from 255 (light) to 55 (dark)
    return `rgb(${blue}, ${blue + 20}, 255)`;
  };

  const getTextColor = (value, maxValue, isDiagonal) => {
    if (value === 0) return '#9ca3af'; // Gray text for zero
    
    const intensity = maxValue > 0 ? value / maxValue : 0;
    return intensity > 0.5 ? 'white' : 'black';
  };

  return (
    <div className="space-y-6">
      {/* Confusion Matrix */}
      {results.confusion_matrix && results.labels && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">🎯 Confusion Matrix</h3>
          <p className="text-sm text-gray-600 mb-4">
            Rows represent true intents, columns represent predicted intents
          </p>
          
          <div className="overflow-x-auto">
            <div className="inline-block min-w-full">
              <table className="border-collapse" style={{ tableLayout: 'fixed' }}>
                <thead>
                  <tr>
                    <th className="border border-gray-300 bg-gray-100 p-2 text-xs font-semibold text-gray-700 w-32">
                      True \ Predicted
                    </th>
                    {results.labels.map((label, idx) => (
                      <th 
                        key={idx} 
                        className="border border-gray-300 bg-gray-100 p-2 text-xs font-semibold text-gray-700 w-24"
                        style={{ wordWrap: 'break-word' }}
                      >
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {results.confusion_matrix.map((row, i) => {
                    const maxValue = Math.max(...results.confusion_matrix.flat());
                    return (
                      <tr key={i}>
                        <td className="border border-gray-300 bg-gray-100 p-2 text-xs font-semibold text-gray-700">
                          {results.labels[i]}
                        </td>
                        {row.map((value, j) => {
                          const isDiagonal = i === j; // Diagonal = correct predictions
                          return (
                            <td 
                              key={j}
                              className="border border-gray-300 p-2 text-center text-sm font-semibold"
                              style={{
                                backgroundColor: getColorIntensity(value, maxValue, isDiagonal),
                                color: getTextColor(value, maxValue, isDiagonal)
                              }}
                            >
                              {value}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="mt-4 text-xs text-gray-500">
            <p>💡 <span className="font-semibold">Blue cells</span> (diagonal) show correct predictions. <span className="font-semibold text-red-600">Red cells</span> (off-diagonal) show mismatches.</p>
          </div>
        </div>
      )}

      {/* Intent Comparison Table */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">🔍 Intent Comparison</h3>
        
        {totalSamples > 10 && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rows to display: {displayCount || totalSamples} {!displayCount && '(All)'}
            </label>
            <input
              type="range"
              min="10"
              max={totalSamples}
              step="1"
              value={displayCount || totalSamples}
              onChange={(e) => {
                const value = parseInt(e.target.value);
                setDisplayCount(value >= totalSamples ? null : value);
              }}
              className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer slider-thumb"
              style={{
                background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((displayCount || totalSamples) / totalSamples) * 100}%, #e5e7eb ${((displayCount || totalSamples) / totalSamples) * 100}%, #e5e7eb 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>10</span>
              <span>{totalSamples} (All)</span>
            </div>
          </div>
        )}

        <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-700">#</th>
                <th className="px-4 py-2 text-left font-medium text-gray-700">Text Sample</th>
                <th className="px-4 py-2 text-left font-medium text-gray-700">True Intent</th>
                <th className="px-4 py-2 text-left font-medium text-gray-700">Predicted Intent</th>
                <th className="px-4 py-2 text-center font-medium text-gray-700">Match</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {displayData.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-500">{idx + 1}</td>
                  <td className="px-4 py-2 text-gray-600">
                    {item.text.length > 100 ? item.text.substring(0, 100) + '...' : item.text}
                  </td>
                  <td className="px-4 py-2 text-gray-900">{item.true}</td>
                  <td className="px-4 py-2 text-gray-900">{item.predicted}</td>
                  <td className="px-4 py-2 text-center">
                    {item.match ? '✅' : '❌'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-sm text-gray-500 mt-3">
          Showing {displayData.length} of {totalSamples} samples
        </p>
      </div>

      {/* Download Results */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">📥 Download Results</h3>
        <button
          onClick={() => {
            // Create CSV content
            const headers = ['Text', 'True Intent', 'Predicted Intent', 'Correct'];
            const rows = results.sample_predictions.map(item => [
              item.text.replace(/"/g, '""'),
              item.true,
              item.predicted,
              item.match ? 'Yes' : 'No'
            ]);
            
            const csvContent = [
              headers.join(','),
              ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
            ].join('\n');

            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `intent_comparison_${results.model_name || 'model'}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            toast.success('CSV downloaded!');
          }}
          className="btn-primary flex items-center gap-2"
        >
          📥 Download Detailed Results (CSV)
        </button>
      </div>
    </div>
  );
};

const ModelComparisonTab = ({ history }) => {
  const selectedWorkspace = useWorkspaceStore((state) => state.selectedWorkspace);
  const [saving, setSaving] = useState(false);

  if (!history || history.length === 0) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="mx-auto text-gray-400 mb-4" size={48} />
        <p className="text-gray-600">No model history yet</p>
        <p className="text-sm text-gray-500 mt-2">
          Run evaluations to populate the comparison table
        </p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    const headers = ['Version', 'Model Name', 'Accuracy', 'F1 Score', 'Train Samples', 'Test Samples', 'Timestamp'];
    const rows = history.map(item => [
      item.version,
      item.model_name,
      item.accuracy,
      item.f1,
      item.train_samples,
      item.test_samples,
      item.timestamp
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'model_comparison.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    toast.success('CSV downloaded!');
  };

  const handleSaveToDatabase = async () => {
    if (!selectedWorkspace) {
      toast.error('Please select a workspace first');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        workspace_id: selectedWorkspace.id,
        workspace_name: selectedWorkspace.name,
        models: history.map(item => ({
          version: item.version,
          model_name: item.model_name,
          accuracy: item.accuracy,
          f1: item.f1,
          train_samples: item.train_samples,
          test_samples: item.test_samples,
          timestamp: item.timestamp,
        }))
      };

      await api.post('/evaluation/model-comparison/save', payload);
      toast.success('✅ Model comparison saved successfully!');
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      toast.error('Failed to save: ' + errorMsg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">📈 Model Comparison</h3>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Version</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Model Name</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Accuracy</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">F1 Score</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Train Samples</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Test Samples</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {history.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-900">{item.version}</td>
                  <td className="px-4 py-3 text-gray-900">{item.model_name}</td>
                  <td className="px-4 py-3 text-gray-900">{item.accuracy}</td>
                  <td className="px-4 py-3 text-gray-900">{item.f1}</td>
                  <td className="px-4 py-3 text-gray-900">{item.train_samples}</td>
                  <td className="px-4 py-3 text-gray-900">{item.test_samples}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{item.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-6 flex gap-4">
          <button
            onClick={handleDownloadCSV}
            className="btn-primary flex-1 flex items-center justify-center gap-2"
          >
            📥 Download Model Comparison Report
          </button>
          
          <button
            onClick={handleSaveToDatabase}
            disabled={saving}
            className="btn-primary flex-1 flex items-center justify-center gap-2"
          >
            {saving ? (
              <>
                <Loader2 className="animate-spin" size={16} />
                Saving...
              </>
            ) : (
              '💾 Save to Database'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

const ActiveLearningTab = ({ evaluationResults }) => {
  const selectedDataset = useDatasetStore((state) => state.selectedDataset);
  const [selectedModel, setSelectedModel] = useState('spacy');
  const [corrections, setCorrections] = useState({});
  const [loading, setLoading] = useState(false);
  const [showCorrected, setShowCorrected] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState(50);

  // Get mismatched predictions from evaluation results
  const allMismatchedSamples = evaluationResults?.mismatches || [];
  
  // Filter by confidence threshold - show predictions with confidence below threshold
  const mismatchedSamples = allMismatchedSamples.filter(sample => {
    const confidence = sample.confidence || 0;
    return (confidence * 100) < confidenceThreshold;
  });
  
  const correctedCount = Object.keys(corrections).length;

  const handleCorrectIntent = (index, correctedIntent) => {
    setCorrections({
      ...corrections,
      [index]: correctedIntent,
    });
  };

  const handleRetrainModel = async () => {
    if (correctedCount === 0) {
      toast.error('No corrections made. Please correct at least one intent.');
      return;
    }

    if (!selectedDataset) {
      toast.error('Please select a dataset first');
      return;
    }

    setLoading(true);
    const savingToast = toast.loading(`💾 Saving ${correctedCount} corrections to feedback...`);

    try {
      // Prepare feedback items for the backend
      const feedbackItems = mismatchedSamples
        .map((sample, idx) => {
          if (corrections[idx]) {
            return {
              text: sample.text,
              predicted_intent: sample.predicted,
              predicted_confidence: 0.0, // We don't have confidence from evaluation
              corrected_intent: corrections[idx],
              entities: [],
              model_id: evaluationResults?.model_id || selectedModel,
              model_name: evaluationResults?.model_name || selectedModel,
              remarks: 'Active Learning Correction'
            };
          }
          return null;
        })
        .filter(item => item !== null);

      // Save corrections to backend
      await api.post('/active-learning/corrections', {
        items: feedbackItems
      });

      toast.dismiss(savingToast);
      toast.success(`✅ Saved ${feedbackItems.length} corrections!`);
      
      const trainToast = toast.loading('Starting model training...');

      // Start training using the /train/start endpoint
      try {
        await api.post('/train/start', {
          dataset_checksum: selectedDataset.checksum
        });

        toast.dismiss(trainToast);
        toast.success(`🎉 Model training started! This will retrain with ${feedbackItems.length} corrected samples.`);
        
        // Clear corrections after successful training start
        setCorrections({});
        setLoading(false);
      } catch (trainError) {
        toast.dismiss(trainToast);
        console.error('Training error:', trainError);
        
        let trainMsg = 'Training failed';
        if (trainError.response?.data?.detail) {
          trainMsg = trainError.response.data.detail;
        } else if (trainError.response?.data?.message) {
          trainMsg = trainError.response.data.message;
        } else if (trainError.message) {
          trainMsg = trainError.message;
        }
        
        toast.error('Training failed: ' + trainMsg);
        setLoading(false);
      }
    } catch (error) {
      toast.dismiss(savingToast);
      console.error('Error saving feedback:', error);
      
      let errorMsg = 'Unknown error occurred';
      if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMsg = error.response.data.message;
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      toast.error('Failed to save corrections: ' + errorMsg);
      setLoading(false);
    }
  };

  const handleClearCorrections = () => {
    setCorrections({});
    setShowCorrected(false);
    toast.success('Corrections cleared');
  };

  if (!evaluationResults || !evaluationResults.mismatches) {
    return (
      <div className="text-center py-12">
        <RefreshCw className="mx-auto text-gray-400 mb-4" size={48} />
        <p className="text-gray-600">No evaluation results available</p>
        <p className="text-sm text-gray-500 mt-2">
          💡 Run an evaluation in the Evaluate tab first to see incorrect predictions
        </p>
      </div>
    );
  }

  if (mismatchedSamples.length === 0) {
    return (
      <div className="text-center py-12">
        <RefreshCw className="mx-auto text-gray-400 mb-4" size={48} />
        <p className="text-green-600 font-semibold">🎉 Perfect! No incorrect predictions found.</p>
        <p className="text-sm text-gray-500 mt-2">
          Your model achieved 100% accuracy on the test set.
        </p>
      </div>
    );
  }

  if (!selectedDataset) {
    return (
      <div className="text-center py-12">
        <RefreshCw className="mx-auto text-gray-400 mb-4" size={48} />
        <p className="text-gray-600">Please select a dataset in View Data tab first</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">🔄 Active Learning</h3>
        <p className="text-sm text-gray-600 mb-4">
          Found <span className="font-bold text-red-600">{mismatchedSamples.length}</span> incorrect predictions from the last evaluation.
          Correct them below and retrain the model to improve accuracy.
        </p>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Model for Retraining
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="input-field"
            >
              {MODEL_OPTIONS.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Engine: {selectedModel}
            </p>
          </div>

          <div className="flex items-end">
            <div className="w-full">
              <div className="rounded-lg p-3" style={{ 
                background: 'rgba(50, 186, 255, 0.08)', 
                border: '1px solid rgba(50, 186, 255, 0.35)' 
              }}>
                <p className="text-sm font-medium" style={{ color: '#f3f8ff' }}>
                  Corrections: <span className="text-xl font-bold" style={{ color: '#32beff' }}>{correctedCount}</span> / {mismatchedSamples.length}
                </p>
                <p className="text-xs mt-1" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>
                  {mismatchedSamples.length > 0 ? ((correctedCount / mismatchedSamples.length) * 100).toFixed(0) : 0}% corrected
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Confidence Threshold Slider */}
        <div className="mt-4">
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-gray-700">
              🎯 Confidence Threshold: <span className="font-bold text-primary-600">{confidenceThreshold}%</span>
            </label>
            <span className="text-xs text-gray-500">
              Showing predictions with confidence &lt; {confidenceThreshold}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={confidenceThreshold}
            onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
            className="w-full h-2 rounded-lg appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, #ff6b6b 0%, #ff6b6b ${confidenceThreshold}%, rgba(255, 107, 107, 0.2) ${confidenceThreshold}%, rgba(255, 107, 107, 0.2) 100%)`,
            }}
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0% (Most Certain)</span>
            <span>50% (Uncertain)</span>
            <span>100% (All Predictions)</span>
          </div>
        </div>
      </div>

      {/* Incorrect Predictions */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-semibold">
              ❌ Uncertain Predictions ({mismatchedSamples.length})
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              Showing {mismatchedSamples.length} of {allMismatchedSamples.length} total predictions
            </p>
          </div>
          <div className="flex gap-2">
            {correctedCount > 0 && (
              <button onClick={handleClearCorrections} className="btn-secondary text-sm">
                🗑️ Clear All
              </button>
            )}
            <button 
              onClick={handleRetrainModel}
              disabled={loading || correctedCount === 0}
              className="btn-primary flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={16} />
                  Retraining...
                </>
              ) : (
                <>
                  🚀 Retrain with Corrections ({correctedCount})
                </>
              )}
            </button>
          </div>
        </div>

        {mismatchedSamples.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-2">
              🎯 No predictions found below {confidenceThreshold}% confidence threshold
            </p>
            <p className="text-sm text-gray-400">
              Try adjusting the slider above to see more predictions
            </p>
          </div>
        ) : (
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {mismatchedSamples.map((sample, idx) => (
            <div 
              key={idx} 
              className="p-4 border-2 rounded-lg transition-all"
              style={{
                background: corrections[idx] 
                  ? 'rgba(50, 244, 122, 0.08)' 
                  : 'rgba(255, 107, 107, 0.08)',
                borderColor: corrections[idx]
                  ? 'rgba(50, 244, 122, 0.35)'
                  : 'rgba(255, 107, 107, 0.35)'
              }}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-1">
                  {corrections[idx] ? (
                    <span className="text-2xl">✅</span>
                  ) : (
                    <span className="text-2xl">❌</span>
                  )}
                </div>
                
                <div className="flex-1">
                  <div className="flex justify-between items-start mb-3">
                    <p className="font-medium" style={{ color: '#f3f8ff' }}>
                      <span className="text-sm mr-2" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>#{idx + 1}</span>
                      {sample.text}
                    </p>
                    {sample.confidence !== undefined && (
                      <span 
                        className="text-xs font-semibold px-2 py-1 rounded"
                        style={{
                          background: sample.confidence < 0.3 
                            ? 'rgba(255, 107, 107, 0.2)' 
                            : sample.confidence < 0.5 
                            ? 'rgba(255, 193, 7, 0.2)' 
                            : 'rgba(255, 152, 0, 0.2)',
                          color: sample.confidence < 0.3 
                            ? '#ff6b6b' 
                            : sample.confidence < 0.5 
                            ? '#ffc107' 
                            : '#ff9800'
                        }}
                      >
                        {(sample.confidence * 100).toFixed(1)}% confidence
                      </span>
                    )}
                  </div>
                  
                  <div className="grid md:grid-cols-3 gap-3">
                    <div className="p-3 rounded border" style={{ 
                      background: 'rgba(255, 255, 255, 0.04)', 
                      borderColor: 'rgba(142, 228, 175, 0.25)' 
                    }}>
                      <p className="text-xs uppercase font-semibold mb-1" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>True Intent</p>
                      <p className="text-sm font-medium" style={{ color: '#2bf06f' }}>{sample.true}</p>
                    </div>

                    <div className="p-3 rounded border" style={{ 
                      background: 'rgba(255, 255, 255, 0.04)', 
                      borderColor: 'rgba(142, 228, 175, 0.25)' 
                    }}>
                      <p className="text-xs uppercase font-semibold mb-1" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>Predicted Intent</p>
                      <p className="text-sm font-medium" style={{ color: '#ff6b6b' }}>{sample.predicted}</p>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold uppercase mb-1" style={{ color: '#f3f8ff' }}>
                        Corrected Intent:
                      </label>
                      <input
                        type="text"
                        value={corrections[idx] || sample.true}
                        onChange={(e) => handleCorrectIntent(idx, e.target.value)}
                        className="input-field text-sm"
                        placeholder="Enter correct intent"
                        style={{ color: '#f7fbff' }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            ))}
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="card" style={{ 
        background: 'rgba(50, 186, 255, 0.08)', 
        borderColor: 'rgba(50, 186, 255, 0.35)' 
      }}>
        <h4 className="font-semibold mb-2" style={{ color: '#32beff' }}>💡 How Active Learning Works:</h4>
        <ol className="text-sm space-y-1 list-decimal list-inside" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>
          <li>Adjust the confidence threshold slider to filter uncertain predictions (default 50%)</li>
          <li>Review the predictions with low confidence scores (highlighted in red)</li>
          <li>Correct the predicted intents in the input fields</li>
          <li>Click "Retrain with Corrections" to train the model with corrected data</li>
          <li>The model learns from its mistakes and improves accuracy</li>
          <li>Run evaluation again to verify improvement</li>
        </ol>
      </div>
    </div>
  );
};

// Feedback Tab Component
const FeedbackTab = () => {
  const [feedbackItems, setFeedbackItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newFeedback, setNewFeedback] = useState({
    text: '',
    predicted_intent: '',
    correct_intent: '',
    entities: [],
    remarks: ''
  });

  // Load existing feedback on mount
  useEffect(() => {
    loadFeedback();
  }, []);

  const loadFeedback = async () => {
    try {
      setLoading(true);
      const response = await api.get('/feedback/list');
      setFeedbackItems(response.data?.items || []);
    } catch (error) {
      console.error('Failed to load feedback:', error);
      toast.error('Failed to load feedback');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveFeedback = async () => {
    // Validation
    if (!newFeedback.text.trim()) {
      toast.error('User query is required');
      return;
    }

    if (!newFeedback.predicted_intent.trim() && !newFeedback.correct_intent.trim()) {
      toast.error('At least one intent (predicted or correct) is required');
      return;
    }

    const savingToast = toast.loading('Saving feedback...');

    try {
      await api.post('/feedback/save', {
        items: [newFeedback]
      });

      toast.dismiss(savingToast);
      toast.success('✅ Feedback saved successfully!');
      
      // Reset form
      setNewFeedback({
        text: '',
        predicted_intent: '',
        correct_intent: '',
        entities: [],
        remarks: ''
      });

      // Reload feedback list
      loadFeedback();
    } catch (error) {
      toast.dismiss(savingToast);
      console.error('Failed to save feedback:', error);
      toast.error(error.response?.data?.detail || 'Failed to save feedback');
    }
  };

  const handleAddEntity = () => {
    setNewFeedback({
      ...newFeedback,
      entities: [
        ...newFeedback.entities,
        { entity: '', value: '', start: 0, end: 0 }
      ]
    });
  };

  const handleRemoveEntity = (index) => {
    const updatedEntities = newFeedback.entities.filter((_, i) => i !== index);
    setNewFeedback({ ...newFeedback, entities: updatedEntities });
  };

  const handleEntityChange = (index, field, value) => {
    const updatedEntities = [...newFeedback.entities];
    updatedEntities[index][field] = value;
    setNewFeedback({ ...newFeedback, entities: updatedEntities });
  };

  if (loading) {
    return <div className="text-center py-12"><Loader2 className="animate-spin mx-auto" size={48} /></div>;
  }

  return (
    <div className="space-y-6">
      {/* Feedback Form Card */}
      <Card style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
        <CardHeader>
          <h3 className="text-xl font-bold" style={{ color: '#32beff' }}>📝 Submit Feedback</h3>
          <p className="text-sm" style={{ color: 'rgba(228, 247, 238, 0.7)' }}>
            Provide feedback on model predictions to help improve accuracy
          </p>
        </CardHeader>

        <div className="p-6 space-y-4">
          {/* User Query */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'rgba(228, 247, 238, 0.9)' }}>
              User Query *
            </label>
            <textarea
              value={newFeedback.text}
              onChange={(e) => setNewFeedback({ ...newFeedback, text: e.target.value })}
              placeholder="Enter the user's query..."
              rows={2}
              className="w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              style={{
                background: 'rgba(17, 25, 40, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.125)',
                color: 'rgba(228, 247, 238, 0.9)'
              }}
            />
          </div>

          {/* Predicted Intent */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'rgba(228, 247, 238, 0.9)' }}>
              Predicted Intent
            </label>
            <input
              type="text"
              value={newFeedback.predicted_intent}
              onChange={(e) => setNewFeedback({ ...newFeedback, predicted_intent: e.target.value })}
              placeholder="What the model predicted..."
              className="w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              style={{
                background: 'rgba(17, 25, 40, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.125)',
                color: 'rgba(228, 247, 238, 0.9)'
              }}
            />
          </div>

          {/* Correct Intent */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'rgba(228, 247, 238, 0.9)' }}>
              Correct Intent *
            </label>
            <input
              type="text"
              value={newFeedback.correct_intent}
              onChange={(e) => setNewFeedback({ ...newFeedback, correct_intent: e.target.value })}
              placeholder="What the correct intent should be..."
              className="w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              style={{
                background: 'rgba(17, 25, 40, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.125)',
                color: 'rgba(228, 247, 238, 0.9)'
              }}
            />
          </div>

          {/* Entities Section */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium" style={{ color: 'rgba(228, 247, 238, 0.9)' }}>
                Entities (Optional)
              </label>
              <button
                onClick={handleAddEntity}
                className="px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200"
                style={{
                  background: 'rgba(50, 190, 255, 0.1)',
                  border: '1px solid rgba(50, 190, 255, 0.3)',
                  color: '#32beff'
                }}
              >
                Add Entity
              </button>
            </div>

            {newFeedback.entities.map((entity, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={entity.entity}
                  onChange={(e) => handleEntityChange(index, 'entity', e.target.value)}
                  placeholder="Entity type"
                  className="flex-1 px-3 py-2 rounded-lg border text-sm"
                  style={{
                    background: 'rgba(17, 25, 40, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.125)',
                    color: 'rgba(228, 247, 238, 0.9)'
                  }}
                />
                <input
                  type="text"
                  value={entity.value}
                  onChange={(e) => handleEntityChange(index, 'value', e.target.value)}
                  placeholder="Entity value"
                  className="flex-1 px-3 py-2 rounded-lg border text-sm"
                  style={{
                    background: 'rgba(17, 25, 40, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.125)',
                    color: 'rgba(228, 247, 238, 0.9)'
                  }}
                />
                <button
                  onClick={() => handleRemoveEntity(index)}
                  className="px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200"
                  style={{
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#ef4444'
                  }}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          {/* Feedback Remarks */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'rgba(228, 247, 238, 0.9)' }}>
              Feedback Remarks
            </label>
            <textarea
              value={newFeedback.remarks}
              onChange={(e) => setNewFeedback({ ...newFeedback, remarks: e.target.value })}
              placeholder="Additional notes or context..."
              rows={3}
              className="w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              style={{
                background: 'rgba(17, 25, 40, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.125)',
                color: 'rgba(228, 247, 238, 0.9)'
              }}
            />
          </div>

          {/* Save Button */}
          <div className="flex justify-end pt-4">
            <button
              onClick={handleSaveFeedback}
              className="px-6 py-2 rounded-lg font-medium transition-all duration-200 hover:scale-105"
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: 'white'
              }}
            >
              Save Feedback
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
};
