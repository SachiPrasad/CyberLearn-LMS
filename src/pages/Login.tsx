import { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import GoogleAuth from '../components/GoogleAuth';
import { authService } from '../services/auth';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    try {
      setIsLoading(true);
      setError('');
      const user = await authService.login(email, password);
      login(user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || "Failed to login");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F3F5FF] flex flex-col items-center justify-center p-6 page-transition">
      <div className="w-full max-w-sm space-y-10">
        <header className="space-y-2">
          <h1 className="text-[32px] font-extrabold text-[#1E1B4B] tracking-tight">Welcome Back</h1>
          <p className="text-slate-500 font-medium">Login to continue your learning journey</p>
        </header>

        <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); handleLogin(); }}>
          <div className="space-y-2">
            <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">Email</label>
            <div className="relative group">
              <Mail className="absolute left-4 top-4 text-slate-300 group-focus-within:text-purple-500 transition-colors" size={20} />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email" 
                required
                className="w-full h-14 bg-white border border-slate-100 rounded-2xl pl-12 pr-4 outline-none focus:ring-4 focus:ring-purple-100 focus:border-purple-300 transition-all shadow-sm" 
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">Password</label>
            <div className="relative group">
              <Lock className="absolute left-4 top-4 text-slate-300 group-focus-within:text-purple-500 transition-colors" size={20} />
              <input 
                type={showPassword ? "text" : "password"} 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password" 
                required
                className="w-full h-14 bg-white border border-slate-100 rounded-2xl pl-12 pr-12 outline-none focus:ring-4 focus:ring-purple-100 focus:border-purple-300 transition-all shadow-sm" 
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-4 text-slate-400 hover:text-slate-600 focus:outline-none"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            <div className="text-right">
              <button type="button" className="text-xs font-bold text-purple-600 hover:text-purple-700">Forgot Password?</button>
            </div>
          </div>

          {error && <div className="text-red-500 text-sm font-semibold text-center">{error}</div>}

          <button 
            type="submit"
            disabled={isLoading}
            className="w-full h-14 cyber-gradient text-white font-bold rounded-2xl shadow-[0_12px_24px_-8px_rgba(168,85,247,0.5)] hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:hover:scale-100 transition-all flex items-center justify-center gap-2"
          >
            {isLoading ? <Loader2 className="animate-spin" size={18} /> : <>Login <ArrowRight size={18} /></>}
          </button>
        </form>

        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <div className="h-[1px] flex-1 bg-slate-200"></div>
            <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest">or</span>
            <div className="h-[1px] flex-1 bg-slate-200"></div>
          </div>

          <GoogleAuth />

          <p className="text-slate-500 text-sm text-center">
            Don't have an account? <Link to="/register" className="text-purple-600 font-bold hover:underline">Sign Up</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
