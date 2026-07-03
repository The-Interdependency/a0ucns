import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AuthCallback() {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Prevent double-processing in React StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processSession = async () => {
      // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH

      const queryParams = new URLSearchParams(window.location.search);
      const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ''));

      const oauthError = queryParams.get('error') || hashParams.get('error');
      const oauthErrorDescription = queryParams.get('error_description') || hashParams.get('error_description');
      if (oauthError) {
        toast.error(oauthErrorDescription || 'Google sign-in failed. Please try again.');
        navigate('/auth', { replace: true });
        return;
      }

      const sessionId = hashParams.get('session_id') || queryParams.get('session_id');

      if (!sessionId) {
        toast.error('Google sign-in session missing. Please try again.');
        navigate('/auth', { replace: true });
        return;
      }

      try {
        // Exchange session_id for user data and set cookie
        const response = await axios.post(
          `${API}/auth/google/session`,
          {},
          {
            headers: {
              'X-Session-ID': sessionId
            },
            withCredentials: true  // Important for cookies
          }
        );

        const user = response.data;
        const accessToken = response.data?.access_token;

        if (accessToken) {
          axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
        }
        
        toast.success(`Welcome, ${user.name}!`);
        
        // Redirect to chat with user data
        navigate('/chat', { state: { user }, replace: true });
        
      } catch (error) {
        console.error('Auth callback error:', error);
        const detail = error?.response?.data?.detail;
        const message = (typeof detail === 'string' && detail)
          || (typeof detail === 'object' && (detail.error_description || detail.error || detail.message))
          || 'Authentication failed';
        toast.error(message);
        navigate('/auth', { replace: true });
      }
    };

    processSession();
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Completing sign in...</p>
      </div>
    </div>
  );
}
