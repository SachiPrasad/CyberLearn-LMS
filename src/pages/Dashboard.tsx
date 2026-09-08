import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Bell, Play, Star, Bookmark, LayoutGrid, Search, User, LogOut } from 'lucide-react';
import Chatbot from '../components/Chatbot';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-[#F8F9FF] pb-24 font-sans">
      <header className="p-6 flex justify-between items-center relative">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center text-white font-black text-sm">
            C
          </div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">CyberLearn</h2>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative p-2 rounded-xl bg-white shadow-sm border border-slate-100 cursor-pointer">
            <Bell className="text-slate-600" size={20} />
            <span className="absolute 1 top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white"></span>
          </div>

          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 bg-white p-1.5 pr-3 rounded-full border border-slate-100 shadow-sm hover:border-purple-200 transition-all"
            >
              {user?.picture ? (
                <img src={user.picture} className="w-8 h-8 rounded-full object-cover" alt="profile" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 font-bold flex items-center justify-center text-xs">
                  {user?.name ? user.name[0].toUpperCase() : 'U'}
                </div>
              )}
              <span className="text-xs font-bold text-slate-700 max-w-[100px] truncate">
                {user?.name?.split(' ')[0] || 'User'}
              </span>
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-2xl shadow-xl border border-slate-100 py-2 z-50 animate-in fade-in slide-in-from-top-2">
                <div className="px-4 py-2 border-b border-slate-50">
                  <p className="text-xs font-bold text-slate-800 truncate">{user?.name || 'Learner'}</p>
                  <p className="text-[10px] text-slate-400 truncate">{user?.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full px-4 py-2.5 text-left text-xs font-bold text-red-500 hover:bg-red-50 flex items-center gap-2 transition-colors"
                >
                  <LogOut size={14} />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="p-6 space-y-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-black text-slate-900">Hi, {user?.name?.split(' ')[0] || user?.email?.split('@')[0] || 'Learner'}! 👋</h1>
            <p className="text-slate-500 text-sm font-medium">Let's continue your learning journey today.</p>
          </div>
          {user?.picture && (
            <img src={user.picture} className="w-12 h-12 rounded-full border-2 border-purple-200 shadow-sm" alt="profile" />
          )}
        </div>

        {/* Progress Card */}
        <div className="bg-gradient-to-r from-[#6366f1] to-[#a855f7] rounded-[2.5rem] p-8 text-white shadow-xl relative overflow-hidden">
          <p className="text-[10px] font-bold uppercase tracking-widest opacity-80">Continue Learning</p>
          <h3 className="text-xl font-bold mt-1">Network Security Basics</h3>
          <div className="mt-6 space-y-2">
            <div className="flex justify-between text-xs font-bold">
              <div className="flex-1 h-1.5 bg-white/20 rounded-full mt-1 mr-4 overflow-hidden">
                <div className="h-full bg-white w-[45%]"></div>
              </div>
              <span>45%</span>
            </div>
          </div>
          <button className="mt-6 bg-white text-purple-600 px-6 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2">
            Resume Course <Play size={12} fill="currentColor" />
          </button>
        </div>

        {/* Categories */}
        <section>
          <div className="flex justify-between items-center mb-4">
            <h4 className="font-bold text-slate-800">Top Categories</h4>
            <span className="text-purple-600 text-[10px] font-bold cursor-pointer">View All</span>
          </div>
          <div className="flex gap-4 overflow-x-auto no-scrollbar pb-2">
            {['Network Security', 'Ethical Hacking', 'Web Security'].map((cat, i) => (
              <div key={i} className="min-w-[120px] bg-white p-5 rounded-[2rem] flex flex-col items-center gap-3 shadow-sm border border-slate-50">
                <div className={`p-3 rounded-2xl ${i === 0 ? 'bg-purple-50 text-purple-600' : i === 1 ? 'bg-blue-50 text-blue-600' : 'bg-pink-50 text-pink-600'}`}>
                  <Bookmark size={20} />
                </div>
                <span className="text-[10px] font-bold text-slate-700 text-center">{cat}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Recommended */}
        <section className="space-y-4">
           <h4 className="font-bold text-slate-800">Recommended Courses</h4>
           <div className="bg-white p-4 rounded-[2rem] shadow-sm border border-slate-50 flex gap-4">
              <div className="w-20 h-20 bg-slate-100 rounded-2xl flex-shrink-0"></div>
              <div className="flex-1">
                 <h5 className="font-bold text-slate-800 text-sm">Ethical Hacking for Beginners</h5>
                 <p className="text-[10px] text-slate-400 font-bold mt-1 uppercase tracking-tighter">Beginner Level</p>
                 <div className="flex items-center gap-1 mt-2">
                    <Star size={10} className="text-yellow-400 fill-yellow-400" />
                    <span className="text-[10px] font-bold">4.8</span>
                    <span className="text-[10px] text-slate-300 ml-1">(1.2K)</span>
                 </div>
              </div>
           </div>
        </section>
      </div>

      {/* Footer Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-100 p-4 flex justify-around items-center">
        <LayoutGrid className="text-purple-600" size={24} />
        <Search className="text-slate-300" size={24} />
        <Play className="text-slate-300" size={24} />
        <User className="text-slate-300" size={24} />
      </nav>

      <Chatbot />
    </div>
  );
};

export default Dashboard;
