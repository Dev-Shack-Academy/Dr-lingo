import { useState, useEffect } from 'react';
import { Terminal, Refresh, CheckCircle, Error, PlayArrow } from '@mui/icons-material';
import httpClient from '../../api/HttpClient';
import routes, { API_BASE_URL } from '../../api/routes';

interface Task {
  id: string;
  name: string;
  status: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY' | 'REVOKED';
  result: any;
  args: any[];
  kwargs: any;
  worker: string;
  started: string;
  runtime: number;
}

export default function TaskMonitor() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchTasks = async () => {
    setIsLoading(true);
    try {
      // Temporary check until backend endpoint is fully verified
      const response = await httpClient.get(`${API_BASE_URL}${routes.CELERY_STATUS}`);
      setTasks(response.data.tasks || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 30000); // 30 seconds polling
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle className="text-green-500 w-5 h-5" />;
      case 'FAILURE':
        return <Error className="text-red-500 w-5 h-5" />;
      case 'STARTED':
      case 'PENDING':
        return <PlayArrow className="text-blue-500 w-5 h-5 animate-pulse" />;
      default:
        return <Refresh className="text-gray-400 w-5 h-5 animate-spin" />;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="p-6 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
            <Terminal className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Task Monitor</h2>
            <p className="text-sm text-gray-500">Real-time status of background Celery workers</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-400">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </span>
          <button
            onClick={fetchTasks}
            disabled={isLoading}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
          >
            <Refresh className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Task ID
              </th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Started
              </th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Runtime
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {tasks.length > 0 ? (
              tasks.map((task) => (
                <tr key={task.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(task.status)}
                      <span className="text-sm font-medium">{task.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600">
                      {task.id.substring(0, 8)}...
                    </code>
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{task.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(task.started).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {task.runtime ? `${task.runtime.toFixed(2)}s` : '-'}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                  {isLoading ? 'Fetching task data...' : 'No active or recent tasks found.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
