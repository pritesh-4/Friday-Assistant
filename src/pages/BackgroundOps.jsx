import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

const BackgroundOps = () => {
  const [jobs, setJobs] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('jobs');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  async function fetchData() {
    try {
      const [jobsRes, notifsRes] = await Promise.all([
        api.get('/background/jobs'),
        api.get('/background/notifications')
      ]);
      setJobs(jobsRes.data);
      setNotifications(notifsRes.data);
    } catch (err) {
      console.error("Failed to fetch background data:", err);
    } finally {
      setLoading(false);
    }
  }

  const handleRetryJob = async (jobId) => {
    try {
      await api.post(`/background/jobs/${jobId}/retry`);
      fetchData();
    } catch (err) {
      console.error("Failed to retry job:", err);
    }
  };

  const handleMarkRead = async (notifId) => {
    try {
      await api.patch(`/background/notifications/${notifId}/read`);
      fetchData();
    } catch (err) {
      console.error("Failed to mark read:", err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'failed': return 'text-red-400 bg-red-500/10 border-red-500/30';
      case 'running': return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
      case 'waiting': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      case 'queued':
      case 'scheduled': return 'text-zinc-400 bg-zinc-500/10 border-zinc-500/30';
      default: return 'text-zinc-500 bg-zinc-800 border-zinc-700';
    }
  };

  return (
    <div className="min-h-screen bg-black text-zinc-100 font-inter pt-28 px-6 pb-12">
      <div className="max-w-6xl mx-auto">
        <header className="mb-10 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-white mb-2">Background Operations</h1>
            <p className="text-zinc-400 text-lg">Monitor autonomous tasks and system intelligence.</p>
          </div>
          <div className="flex gap-4 bg-zinc-900/80 p-1.5 rounded-full border border-white/10 backdrop-blur-md">
            <button 
              onClick={() => setActiveTab('jobs')}
              className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
                activeTab === 'jobs' ? 'bg-primary-container text-on-primary-container shadow-[0_0_15px_rgba(0,240,255,0.2)]' : 'text-zinc-400 hover:text-white'
              }`}
            >
              Jobs
            </button>
            <button 
              onClick={() => setActiveTab('notifications')}
              className={`relative px-6 py-2 rounded-full text-sm font-medium transition-all ${
                activeTab === 'notifications' ? 'bg-primary-container text-on-primary-container shadow-[0_0_15px_rgba(0,240,255,0.2)]' : 'text-zinc-400 hover:text-white'
              }`}
            >
              Notifications
              {notifications.filter(n => n.status === 'unread').length > 0 && (
                <span className="absolute top-1 right-2 w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              )}
            </button>
          </div>
        </header>

        {loading && jobs.length === 0 ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <AnimatePresence mode="wait">
            {activeTab === 'jobs' && (
              <motion.div 
                key="jobs"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-4"
              >
                <div className="grid grid-cols-6 text-xs font-semibold uppercase tracking-wider text-zinc-500 pb-3 border-b border-zinc-800 px-4">
                  <div className="col-span-2">Task Type</div>
                  <div>Status</div>
                  <div>Scheduled</div>
                  <div>Retries</div>
                  <div className="text-right">Actions</div>
                </div>
                
                {jobs.map(job => (
                  <motion.div 
                    layout
                    key={job.id} 
                    className="grid grid-cols-6 items-center bg-zinc-900/40 hover:bg-zinc-900/80 border border-zinc-800/50 rounded-xl p-4 transition-colors"
                  >
                    <div className="col-span-2">
                      <div className="font-medium text-zinc-200">{job.task_type}</div>
                      <div className="text-xs text-zinc-500 font-mono mt-1">{job.id.substring(0, 8)}...</div>
                    </div>
                    <div>
                      <span className={`px-2.5 py-1 rounded-md border text-xs font-semibold uppercase tracking-wider ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                    </div>
                    <div className="text-sm text-zinc-400">
                      {new Date(job.scheduled_at).toLocaleTimeString()}
                    </div>
                    <div className="text-sm text-zinc-400">
                      {job.retries} / {job.max_retries}
                    </div>
                    <div className="text-right">
                      {job.status === 'failed' && (
                        <button 
                          onClick={() => handleRetryJob(job.id)}
                          className="text-xs bg-white/5 hover:bg-white/10 text-white px-3 py-1.5 rounded transition-colors"
                        >
                          Retry
                        </button>
                      )}
                      {job.status === 'waiting' && (
                        <button className="text-xs bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 px-3 py-1.5 rounded transition-colors">
                          Review
                        </button>
                      )}
                    </div>
                    
                    {job.error_message && (
                      <div className="col-span-6 mt-3 text-sm text-red-400/80 bg-red-500/5 p-3 rounded-lg border border-red-500/10 font-mono overflow-x-auto">
                        {job.error_message}
                      </div>
                    )}
                  </motion.div>
                ))}
                {jobs.length === 0 && (
                  <div className="text-center py-20 text-zinc-500">No background jobs found.</div>
                )}
              </motion.div>
            )}

            {activeTab === 'notifications' && (
              <motion.div 
                key="notifications"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-4"
              >
                {notifications.map(notif => (
                  <motion.div 
                    layout
                    key={notif.id} 
                    className={`flex items-start gap-4 p-5 rounded-xl border transition-colors ${
                      notif.status === 'unread' 
                        ? 'bg-zinc-800/80 border-blue-500/30 shadow-[0_0_15px_rgba(0,120,255,0.05)]' 
                        : 'bg-zinc-900/40 border-zinc-800/50 opacity-70'
                    }`}
                  >
                    <div className={`mt-1 p-2 rounded-full ${
                      notif.type === 'error' ? 'bg-red-500/20 text-red-400' :
                      notif.type === 'success' ? 'bg-emerald-500/20 text-emerald-400' :
                      notif.type === 'approval' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {notif.type === 'error' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                      {notif.type === 'success' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>}
                      {notif.type === 'approval' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
                      {notif.type === 'info' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex justify-between items-start mb-1">
                        <h4 className={`font-semibold ${notif.status === 'unread' ? 'text-white' : 'text-zinc-300'}`}>{notif.title}</h4>
                        <span className="text-xs text-zinc-500">{new Date(notif.created_at).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-zinc-400 text-sm mb-3">{notif.message}</p>
                      
                      <div className="flex items-center gap-3">
                        {notif.status === 'unread' && (
                          <button 
                            onClick={() => handleMarkRead(notif.id)}
                            className="text-xs text-blue-400 hover:text-blue-300 font-medium transition-colors"
                          >
                            Mark as read
                          </button>
                        )}
                        {notif.action_url && (
                          <a 
                            href={notif.action_url}
                            className="text-xs bg-white/10 hover:bg-white/15 text-white px-3 py-1.5 rounded transition-colors"
                          >
                            Take Action
                          </a>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
                {notifications.length === 0 && (
                  <div className="text-center py-20 text-zinc-500">No notifications.</div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
};

export default BackgroundOps;
