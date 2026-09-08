import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';
import { authService } from '../services/auth';

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "948938768813-rk3pu018jiecai5l7vgde5rq1gcied95.apps.googleusercontent.com";

const GoogleAuth: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [isProcessing, setIsProcessing] = useState(false);

  const handleGoogleLogin = () => {
    setIsProcessing(true);

    const startOAuth = () => {
      try {
        const client = (window as any).google?.accounts?.oauth2?.initTokenClient({
          client_id: CLIENT_ID,
          scope: 'email profile openid',
          callback: async (tokenResponse: any) => {
            if (tokenResponse.error) {
              console.error("Google Auth error:", tokenResponse);
              setIsProcessing(false);
              return;
            }
            await handleToken(tokenResponse.access_token);
          },
        });
        
        if (client) {
          client.requestAccessToken();
        } else {
          setIsProcessing(false);
        }
      } catch (err) {
        console.error("GIS initialization error:", err);
        setIsProcessing(false);
      }
    };

    if (typeof window !== 'undefined' && (window as any).google?.accounts?.oauth2) {
      startOAuth();
    } else {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = startOAuth;
      script.onerror = () => {
        alert("Unable to load Google Sign-In script. Please check your network connection.");
        setIsProcessing(false);
      };
      document.body.appendChild(script);
    }
  };

  const handleToken = async (accessToken: string) => {
    try {
      const res = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const profile = await res.json();

      let user;
      try {
        user = await authService.googleAuth({
          email: profile.email,
          name: profile.name,
          picture: profile.picture,
          token: accessToken,
        });
      } catch (apiErr) {
        console.warn("Backend auth failed, falling back to local session:", apiErr);
        user = {
          name: profile.name || profile.email.split('@')[0],
          email: profile.email,
          picture: profile.picture,
        };
        localStorage.setItem("access_token", accessToken);
      }

      login(user);
      navigate('/dashboard');
    } catch (error) {
      console.error("Failed to fetch Google profile:", error);
      alert("Google Authentication failed. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <button
      onClick={handleGoogleLogin}
      disabled={isProcessing}
      type="button"
      className="w-full h-14 bg-white border border-slate-200 rounded-2xl flex items-center justify-center gap-3 font-bold text-slate-700 shadow-sm hover:bg-slate-50 active:scale-[0.98] transition-all duration-200 disabled:opacity-70 cursor-pointer"
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

