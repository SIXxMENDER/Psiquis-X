
import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
import sys
import io

# Manager de Conexiones para la Terminal
class TerminalManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.log_buffer = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Enviar últimos logs al conectar para contexto
        for log in self.log_buffer[-50:]:
            await websocket.send_text(log)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Guardar en buffer circular
        self.log_buffer.append(message)
        if len(self.log_buffer) > 200:
            self.log_buffer.pop(0)
            
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

# Instancia Global
terminal_manager = TerminalManager()

# Hook para interceptar prints del sistema
class StdoutInterceptor(io.StringIO):
    def __init__(self, loop=None):
        super().__init__()
        self.loop = loop
        self._is_writing = False

    def set_loop(self, loop):
        self.loop = loop

    def write(self, message):
        if self._is_writing:
            sys.__stdout__.write(message)
            return

        self._is_writing = True
        try:
            if message.strip():
                if self.loop and self.loop.is_running():
                    # 1. Send to Terminal (Legacy)
                    self.loop.call_soon_threadsafe(
                        lambda: asyncio.create_task(terminal_manager.broadcast(message))
                    )
                    # 2. Bridge to Mission Dashboard V2 (Neural Thought Stream) - NO PRINT to avoid recursion
                    from core.mission_control import mission_manager
                    clean_msg = message.strip()
                    if clean_msg:
                         self.loop.call_soon_threadsafe(
                            lambda: asyncio.create_task(mission_manager.emit_event(
                                "thought", 
                                clean_msg, 
                                agent="SYSTEM", 
                                log_to_console=False
                            ))
                        )
            # Mantener comportamiento original
            sys.__stdout__.write(message)
        finally:
            self._is_writing = False

    def flush(self):
        sys.__stdout__.flush()
