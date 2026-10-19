import { useState, useEffect, useRef, useCallback } from 'react'

export function useWebSocket(url) {
  const [lastMessage, setLastMessage] = useState(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)
  const mountedRef = useRef(true)

  const connect = useCallback(() => {
    if (!mountedRef.current) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        if (mountedRef.current) setConnected(true)
      }

      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data)
          if (mountedRef.current) setLastMessage(data)
        } catch {}
      }

      ws.onclose = () => {
        if (mountedRef.current) {
          setConnected(false)
          // Auto-reconnect after 3s
          reconnectTimer.current = setTimeout(connect, 3000)
        }
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch (e) {
      reconnectTimer.current = setTimeout(connect, 3000)
    }
  }, [url])

  useEffect(() => {
    mountedRef.current = true
    connect()
    return () => {
      mountedRef.current = false
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  const reconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current)
    wsRef.current?.close()
    setTimeout(connect, 500)
  }, [connect])

  return { lastMessage, connected, reconnect }
}
