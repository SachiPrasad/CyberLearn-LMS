import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, User, Eye } from 'lucide-react';
import GoogleAuth from '../components/GoogleAuth';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login({ name, email });
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-[#f3f4ff] flex flex-col items-center p-8 font-sans">
      <div className="w-full max-w-md">
        <header className="mb-10 mt-10">
          <h1 className="text-3xl font-bold text-[#1e1b4b]">Create Account</h1>
          <p className="text-slate-500 mt-2">Sign up to start your learning journey</p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wide">Full Name</label>
            <div className="relative">
              <User className="absolute left-4 top-3.5 text-slate-400" size={18} />
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Enter your name" className="w-full bg-white border border-slate-200 rounded-2xl py-3.5 pl-12 pr-4 focus:ring-2 focus:ring-purple-400 outline-none transition-all" required />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wide">Email</label>
            <div className="relative">
              <Mail className="absolute left-4 top-3.5 text-slate-400" size={18} />
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Enter your email" className="w-full bg-white border border-slate-200 rounded-2xl py-3.5 pl-12 pr-4 focus:ring-2 focus:ring-purple-400 outline-none transition-all" required />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wide">Password</label>
            <div className="relative">
              <Lock className="absolute left-4 top-3.5 text-slate-400" size={18} />
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Create a password" className="w-full bg-white border border-slate-200 rounded-2xl py-3.5 pl-12 pr-12 focus:ring-2 focus:ring-purple-400 outline-none transition-all" required />
              <Eye className="absolute right-4 top-3.5 text-slate-400 cursor-pointer" size={18} />
            </div>
          </div>

          <button type="submit" className="w-full bg-gradient-to-r from-[#6366f1] to-[#a855f7] text-white font-bold py-4 rounded-2xl shadow-lg shadow-purple-200 hover:scale-[1.02] transition-transform">
            Sign Up
          </button>
        </form>

        <div className="mt-8 text-center space-y-6">
          <div className="flex items-center gap-4 text-slate-400 text-xs uppercase font-bold">
            <div className="flex-1 h-[1px] bg-slate-200"></div> or <div className="flex-1 h-[1px] bg-slate-200"></div>
          </div>
          
          <GoogleAuth />

          <p className="text-slate-500 text-sm">
            Already have an account? <Link to="/login" className="text-purple-600 font-bold">Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
