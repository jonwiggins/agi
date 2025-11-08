import { useState, useEffect, useRef } from 'react';

export function useWebSocket(executionId) {
  const [messages, setMessages] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const ws = useRef(null);

  useEffect(() => {
    if (!executionId) return;

    // WebSocket URL
    const wsUrl = `ws://${window.location.hostname}:8000/ws/${executionId}`;

    // Create WebSocket connection
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
    };

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setMessages(prev => [...prev, message]);
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');
    };

    // Cleanup
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [executionId]);

  return { messages, connectionStatus };
}
