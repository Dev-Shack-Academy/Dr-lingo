import { useState, useEffect, useRef, useCallback } from 'react';
import type {
  WebSocketStatus,
  ServerEvent,
  ClientEvent,
  UseWebSocketOptions,
  UseWebSocketReturn,
} from '../types/websocket';

const DEFAULT_RECONNECT_INTERVAL = 1000; // Start with 1 second
const MAX_RECONNECT_INTERVAL = 30000; // Max 30 seconds
const DEFAULT_MAX_RECONNECT_ATTEMPTS = 10;
const DEFAULT_PING_INTERVAL = 30000; // 30 seconds

/**
 * Generic WebSocket hook with automatic reconnection and exponential backoff.
 * Handles React Strict Mode by deduplicating connections.
 */
export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnect: shouldReconnect = true,
    reconnectInterval = DEFAULT_RECONNECT_INTERVAL,
    maxReconnectAttempts = DEFAULT_MAX_RECONNECT_ATTEMPTS,
    pingInterval = DEFAULT_PING_INTERVAL,
  } = options;

  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const connectionIdRef = useRef<number>(0);
  const isConnectingRef = useRef(false);

  // Store callbacks in refs to avoid effect dependencies
  const callbacksRef = useRef({
    onMessage,
    onConnect,
    onDisconnect,
    onError,
  });

  // Update callbacks ref when they change
  useEffect(() => {
    callbacksRef.current = {
      onMessage,
      onConnect,
      onDisconnect,
      onError,
    };
  }, [onMessage, onConnect, onDisconnect, onError]);

  // Calculate reconnect delay with exponential backoff
  const getReconnectDelay = useCallback(() => {
    const delay = Math.min(
      reconnectInterval * Math.pow(2, reconnectAttemptsRef.current),
      MAX_RECONNECT_INTERVAL
    );
    return delay;
  }, [reconnectInterval]);

  // Clear all timers
  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  // Start ping interval to keep connection alive
  const startPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, pingInterval);
  }, [pingInterval]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!mountedRef.current) {
      console.log('[WebSocket] Not connecting - component unmounted');
      return;
    }

    if (!url) {
      console.log('[WebSocket] Not connecting - no URL provided');
      return;
    }

    // Prevent duplicate connection attempts
    if (isConnectingRef.current) {
      console.log('[WebSocket] Already connecting, skipping duplicate attempt');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      console.log('[WebSocket] Connection in progress');
      return;
    }

    // Mark as connecting
    isConnectingRef.current = true;
    const currentConnectionId = ++connectionIdRef.current;

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('connecting');
    console.log(`[WebSocket] Connecting to ${url}... (connection #${currentConnectionId})`);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        // Check if this connection is still valid
        if (!mountedRef.current || connectionIdRef.current !== currentConnectionId) {
          console.log(
            `[WebSocket] Connection #${currentConnectionId} opened but component unmounted or superseded, closing`
          );
          ws.close(1000, 'Stale connection');
          return;
        }

        isConnectingRef.current = false;
        console.log(`[WebSocket] Connected (connection #${currentConnectionId})`);
        setStatus('connected');
        reconnectAttemptsRef.current = 0;
        startPingInterval();
        callbacksRef.current.onConnect?.();
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current || connectionIdRef.current !== currentConnectionId) return;
        try {
          const data = JSON.parse(event.data) as ServerEvent;
          console.log('[WebSocket] Received:', data.type);
          callbacksRef.current.onMessage?.(data);
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err);
        }
      };

      ws.onerror = (event) => {
        if (!mountedRef.current || connectionIdRef.current !== currentConnectionId) return;
        console.error('[WebSocket] Error:', event);
        isConnectingRef.current = false;
        setStatus('error');
        callbacksRef.current.onError?.(event);
      };

      ws.onclose = (event) => {
        isConnectingRef.current = false;

        // Check if this is a stale connection
        if (connectionIdRef.current !== currentConnectionId) {
          console.log(`[WebSocket] Stale connection #${currentConnectionId} closed, ignoring`);
          return;
        }

        if (!mountedRef.current) {
          console.log(`[WebSocket] Connection #${currentConnectionId} closed after unmount`);
          return;
        }

        console.log(
          `[WebSocket] Closed: code=${event.code}, reason=${event.reason} (connection #${currentConnectionId})`
        );
        clearTimers();
        wsRef.current = null;

        // Handle different close codes
        if (event.code === 4001) {
          console.log('[WebSocket] Authentication failed');
          setStatus('error');
          return;
        }
        if (event.code === 4002) {
          console.log('[WebSocket] OTP verification required');
          setStatus('error');
          return;
        }
        if (event.code === 4003) {
          console.log('[WebSocket] Access denied to room');
          setStatus('error');
          return;
        }

        setStatus('disconnected');
        callbacksRef.current.onDisconnect?.();

        // Attempt reconnection if enabled and component still mounted
        if (
          mountedRef.current &&
          shouldReconnect &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          const delay = getReconnectDelay();
          console.log(
            `[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`
          );
          setStatus('reconnecting');
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              connect();
            }
          }, delay);
        }
      };
    } catch (err) {
      console.error('[WebSocket] Failed to create connection:', err);
      isConnectingRef.current = false;
      setStatus('error');
    }
  }, [
    url,
    shouldReconnect,
    maxReconnectAttempts,
    getReconnectDelay,
    clearTimers,
    startPingInterval,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    console.log('[WebSocket] Disconnecting...');
    clearTimers();
    isConnectingRef.current = false;
    reconnectAttemptsRef.current = maxReconnectAttempts; // Prevent auto-reconnect
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    setStatus('disconnected');
  }, [clearTimers, maxReconnectAttempts]);

  // Manual reconnect
  const manualReconnect = useCallback(() => {
    console.log('[WebSocket] Manual reconnect requested');
    reconnectAttemptsRef.current = 0;
    isConnectingRef.current = false;

    // Increment connection ID to invalidate any pending connections
    connectionIdRef.current++;

    clearTimers();
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual reconnect');
      wsRef.current = null;
    }

    // Small delay to ensure cleanup completes
    setTimeout(() => {
      if (mountedRef.current) {
        connect();
      }
    }, 100);
  }, [connect, clearTimers]);

  // Send message
  const send = useCallback((message: ClientEvent) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Cannot send message - not connected');
    }
  }, []);

  // Connect on mount, disconnect on unmount
  // Use URL as dependency to reconnect when room changes
  useEffect(() => {
    mountedRef.current = true;
    isConnectingRef.current = false;

    // Small delay to handle React Strict Mode double-mount
    const connectTimeout = setTimeout(() => {
      if (mountedRef.current && url) {
        connect();
      }
    }, 50);

    return () => {
      mountedRef.current = false;
      clearTimeout(connectTimeout);
      clearTimers();

      // Increment connection ID to invalidate any in-flight connections
      connectionIdRef.current++;

      if (wsRef.current) {
        console.log('[WebSocket] Closing on unmount');
        wsRef.current.close(1000, 'Component unmount');
        wsRef.current = null;
      }
    };
  }, [url]); // Only depend on URL, not connect function

  return {
    status,
    send,
    disconnect,
    reconnect: manualReconnect,
  };
}

export default useWebSocket;
