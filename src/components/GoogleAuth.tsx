import React, { useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

const GoogleAuth: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [isProcessing, setIsProcessing] = useState(false);

  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setIsProcessing(true);
      try {
        // 1. Fetch user profile using the access token
        const res = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        });
        
        const profile = await res.json();

        // 2. Update Auth Context with real data
        login({
          name: profile.name,
          email: profile.email,
          picture: profile.picture
        });

        // 3. Proceed to Dashboard
        navigate('/dashboard');
      } catch (error) {
        console.error("Failed to fetch Google profile:", error);
        alert("Google Authentication failed. Please try again.");
      } finally {
        setIsProcessing(false);
      }
    },
    onError: (error) => {
      console.log('Login Failed:', error);
      setIsProcessing(false);
    },
  });

  return (
    <button
      onClick={() => {
        setIsProcessing(true);
        handleGoogleLogin();
      }}
      disabled={isProcessing}
      type="button"
      className="w-full h-14 bg-white border border-slate-200 rounded-2xl flex items-center justify-center gap-3 font-bold text-slate-700 shadow-sm hover:bg-slate-50 active:scale-[0.98] transition-all duration-200 disabled:opacity-70"
    >
      {isProcessing ? (
        <Loader2 className="animate-spin text-purple-600" size={24} />
      ) : (
        <>
          <img 
            src="https://www.svgrepo.com/show/475656/google-color.svg" 
            alt="Google" 
            className="w-6 h-6" 
          />
          <span className="text-[15px] tracking-tight">
            Continue with Google
          </span>
        </>
      )}
    </button>
  );
};

export default GoogleAuth;
