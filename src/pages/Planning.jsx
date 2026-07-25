import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

const Planning = () => {
  const [goals, setGoals] = useState([]);
  const [selectedGoal, setSelectedGoal] = useState(null);
  const [loading, setLoading] = useState(true);

  async function fetchGoals() {
    try {
      const res = await api.get('/planning/goals');
      setGoals(res.data);
      if (res.data.length > 0) {
        fetchGoalDetails(res.data[0].id);
      } else {
        setLoading(false);
      }
    } catch (err) {
      console.error("Failed to fetch goals:", err);
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchGoals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchGoalDetails(goalId) {
    setLoading(true);
    try {
      const res = await api.get(`/planning/goals/${goalId}`);
      setSelectedGoal(res.data);
    } catch (err) {
      console.error("Failed to fetch goal details:", err);
    } finally {
      setLoading(false);
    }
  }

  const updateTaskStatus = async (taskId, status) => {
    try {
      await api.patch(`/planning/tasks/${taskId}/status`, { status });
      // Refresh goal details
      fetchGoalDetails(selectedGoal.id);
      // Refresh overall progress
      const res = await api.get('/planning/goals');
      setGoals(res.data);
    } catch (err) {
      console.error("Failed to update task:", err);
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'completed': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'in_progress': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'blocked': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-zinc-800 text-zinc-400 border-zinc-700';
    }
  };

  return (
    <div className="flex h-screen bg-black text-zinc-100 font-inter">
      {/* Sidebar for Goals */}
      <div className="w-1/4 border-r border-zinc-800 p-6 flex flex-col bg-zinc-950/50 backdrop-blur-xl">
        <h2 className="text-xl font-bold tracking-tight mb-6 bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">Goals</h2>
        <div className="space-y-4 overflow-y-auto flex-1">
          {goals.map(goal => (
            <motion.div 
              key={goal.id}
              whileHover={{ scale: 1.02 }}
              onClick={() => fetchGoalDetails(goal.id)}
              className={`p-4 rounded-xl cursor-pointer border transition-colors duration-300 ${
                selectedGoal?.id === goal.id ? 'bg-zinc-800/80 border-blue-500/50' : 'bg-zinc-900 border-zinc-800 hover:border-zinc-700'
              }`}
            >
              <h3 className="font-semibold text-zinc-200">{goal.title}</h3>
              <div className="mt-3 flex items-center justify-between text-xs font-medium text-zinc-500">
                <span className="uppercase tracking-wider">{goal.category}</span>
                <span>{goal.progress_percent}%</span>
              </div>
              <div className="w-full bg-zinc-800 rounded-full h-1.5 mt-2 overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${goal.progress_percent}%` }}
                  className="bg-gradient-to-r from-blue-500 to-indigo-500 h-1.5 rounded-full"
                ></motion.div>
              </div>
            </motion.div>
          ))}
          {goals.length === 0 && !loading && (
            <div className="text-zinc-500 text-sm text-center mt-10">No goals active. Ask FRIDAY to plan a project!</div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-8 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : selectedGoal ? (
          <div className="max-w-5xl mx-auto">
            <header className="mb-10">
              <h1 className="text-4xl font-bold tracking-tight text-white mb-3">{selectedGoal.title}</h1>
              <p className="text-zinc-400 text-lg">{selectedGoal.description}</p>
            </header>

            <div className="space-y-12">
              {selectedGoal.milestones.map((milestone, mIdx) => (
                <div key={milestone.id} className="relative">
                  {/* Timeline connector */}
                  {mIdx !== selectedGoal.milestones.length - 1 && (
                    <div className="absolute left-6 top-16 bottom-[-3rem] w-[2px] bg-zinc-800 z-0"></div>
                  )}
                  
                  <div className="flex items-center gap-4 mb-6 relative z-10">
                    <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-700 shadow-xl font-bold text-zinc-300">
                      {mIdx + 1}
                    </div>
                    <h2 className="text-2xl font-semibold text-zinc-100">{milestone.title}</h2>
                  </div>

                  <div className="pl-16 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {milestone.tasks.map(task => (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        key={task.id} 
                        className={`p-5 rounded-xl border bg-zinc-900/50 backdrop-blur-sm ${getStatusColor(task.status)} flex flex-col justify-between`}
                      >
                        <div>
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-semibold text-lg text-white">{task.title}</h4>
                            <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded bg-black/40">
                              {task.status.replace('_', ' ')}
                            </span>
                          </div>
                          {task.description && <p className="text-sm opacity-80 mb-4">{task.description}</p>}
                        </div>
                        
                        <div className="flex items-center justify-between mt-4 border-t border-white/10 pt-4">
                          <div className="flex items-center gap-3">
                            <span className="text-xs flex items-center gap-1 opacity-70">
                              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {task.estimated_duration || "TBD"}
                            </span>
                            {task.assigned_agent && (
                              <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded flex items-center gap-1">
                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                                {task.assigned_agent}
                              </span>
                            )}
                          </div>
                          
                          {task.status !== 'completed' && (
                            <button 
                              onClick={() => updateTaskStatus(task.id, 'completed')}
                              className="text-xs bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 px-3 py-1.5 rounded transition-colors"
                            >
                              Mark Done
                            </button>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-zinc-500">
            Select a goal to view the execution DAG
          </div>
        )}
      </div>
    </div>
  );
};

export default Planning;
