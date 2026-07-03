import React, { createContext, useContext, useState, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ChatContext = createContext(null);

export const useChat = () => {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be inside ChatProvider');
  return ctx;
};

export const ChatProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [threads, setThreads] = useState([]);
  const [currentThread, setCurrentThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState({});
  const [error, setError] = useState(null);
  const [initialized, setInitialized] = useState(false);

  const selectThread = useCallback((threadId) => {
    setCurrentThread(threadId);
  }, []);

  const fetchThreads = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/v1/a0/history?limit=50`);
      setThreads(res.data.threads || []);
      return res.data.threads || [];
    } catch (err) {
      if (err?.response?.status === 401) {
        return [];
      }
      console.error('Failed to fetch threads:', err);
      return [];
    }
  }, []);

  const loadThread = useCallback(async (threadId) => {
    try {
      const res = await axios.get(`${API}/v1/a0/thread/${threadId}`);
      selectThread(threadId);
      setMessages(res.data || []);
    } catch (err) {
      if (err?.response?.status === 401) {
        return;
      }
      console.error('Failed to load thread:', err);
    }
  }, [selectThread]);

  // ---- Fallback: non-streaming collected response ----
  const sendPromptCollected = useCallback(async (message, models, options = {}) => {
    const body = {
      message,
      models,
      thread_id: currentThread || undefined,
      global_context: options.globalContext || undefined,
      per_model_context: options.perModelContext || undefined,
    };

    const res = await fetch(`${API}/v1/a0/prompt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(body),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }, [currentThread]);

  const sendPrompt = useCallback(async (message, models, options = {}) => {
    setLoading(true);
    setStreaming({});
    setError(null);

    // Add user message optimistically
    const userMsgId = `msg_temp_${Date.now()}`;
    setMessages(prev => [...prev, {
      message_id: userMsgId, role: 'user', content: message,
      model: 'user', timestamp: new Date().toISOString(),
    }]);

    try {
      // Try SSE streaming first
      const body = {
        message, models,
        thread_id: currentThread || undefined,
        global_context: options.globalContext || undefined,
        per_model_context: options.perModelContext || undefined,
      };

      const response = await fetch(`${API}/v1/a0/prompt/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`SSE_FAIL_${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      const newResponses = {};
      let threadId = currentThread;
      let gotAnyData = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event: ')) continue;
          if (!line.startsWith('data: ')) continue;

          try {
            const data = JSON.parse(line.slice(6));
            gotAnyData = true;

            if (data.thread_id && !threadId) {
              threadId = data.thread_id;
              selectThread(threadId);
            }

            if (data.message_id && data.model) {
              if (data.content !== undefined) {
                // Chunk
                if (!newResponses[data.model]) {
                  newResponses[data.model] = { content: '', message_id: data.message_id };
                }
                newResponses[data.model].content += data.content;
                setStreaming(prev => ({
                  ...prev,
                  [data.model]: {
                    message_id: data.message_id,
                    content: newResponses[data.model].content,
                  },
                }));
              } else if (data.response_time_ms !== undefined) {
                // Complete
                const finalContent = newResponses[data.model]?.content || '';
                setMessages(prev => [...prev, {
                  message_id: data.message_id, thread_id: threadId,
                  role: 'assistant', content: finalContent, model: data.model,
                  timestamp: new Date().toISOString(), response_time_ms: data.response_time_ms,
                }]);
                setStreaming(prev => {
                  const next = { ...prev };
                  delete next[data.model];
                  return next;
                });
              }
            }
          } catch (parseError) {
            console.error('Skipped malformed SSE JSON chunk:', parseError);
          }
        }
      }

      // If SSE connected but no data arrived, fall back to collected
      if (!gotAnyData) {
        throw new Error('SSE_EMPTY');
      }

      fetchThreads();
    } catch (err) {
      console.warn('SSE failed, falling back to collected endpoint:', err.message);
      setStreaming({});

      // Show loading indicator for each model
      const tempStreaming = {};
      for (const m of models) {
        tempStreaming[m] = { message_id: null, content: '' };
      }
      setStreaming(tempStreaming);

      try {
        // Fallback to collected (non-streaming) endpoint
        const data = await sendPromptCollected(message, models, options);

        if (data.thread_id) selectThread(data.thread_id);

        // Add all responses at once
        for (const resp of (data.responses || [])) {
          setMessages(prev => [...prev, {
            message_id: resp.message_id, thread_id: data.thread_id,
            role: 'assistant', content: resp.content, model: resp.model,
            timestamp: new Date().toISOString(), response_time_ms: resp.response_time_ms,
          }]);
        }
        fetchThreads();
      } catch (fallbackErr) {
        console.error('Collected endpoint also failed:', fallbackErr);
        setError(`Failed to get responses: ${fallbackErr.message}`);
      }
    } finally {
      setLoading(false);
      setStreaming({});
    }
  }, [currentThread, fetchThreads, selectThread, sendPromptCollected]);

  const newThread = useCallback(() => {
    selectThread(null);
    setMessages([]);
    setStreaming({});
    setError(null);
  }, [selectThread]);

  const submitFeedback = useCallback(async (messageId, feedback) => {
    try {
      await axios.post(`${API}/v1/a0/feedback`, { message_id: messageId, feedback });
      setMessages(prev => prev.map(m =>
        m.message_id === messageId ? { ...m, feedback } : m
      ));
    } catch (err) {
      console.error('Feedback error:', err);
    }
  }, []);

  const addOptimisticMessage = useCallback((msg) => {
    setMessages(prev => [...prev, msg]);
  }, []);

  React.useEffect(() => {
    if (!isAuthenticated) {
      setInitialized(false);
      setThreads([]);
      setCurrentThread(null);
      setMessages([]);
      setStreaming({});
      return undefined;
    }

    if (!initialized) {
      setInitialized(true);
      fetchThreads();
    }

    const handleFocus = () => {
      fetchThreads();
      if (currentThread) {
        axios.get(`${API}/v1/a0/thread/${currentThread}`).then(res => {
          if (res.data) setMessages(res.data);
        }).catch((focusError) => {
          console.error('Failed to refresh current thread on focus:', focusError);
        });
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [initialized, fetchThreads, currentThread, isAuthenticated]);

  return (
    <ChatContext.Provider value={{
      threads, currentThread, messages, loading, streaming, error,
      fetchThreads, loadThread, sendPrompt, newThread, submitFeedback,
      addOptimisticMessage, setCurrentThread: selectThread,
    }}>
      {children}
    </ChatContext.Provider>
  );
};
