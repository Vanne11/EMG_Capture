import asyncio
import json
import websockets
from PyQt6.QtCore import QThread, pyqtSignal
import threading
from datetime import datetime

class WebSocketServer(QThread):
    server_status = pyqtSignal(bool, str)
    client_connected = pyqtSignal(int)
    
    def __init__(self, host="localhost", port=8765):
        super().__init__()
        self.host = host
        self.port = port
        self.server = None
        self.connected_clients = set()
        self.is_running = False
        self.loop = None
        
    def start_server(self):
        if not self.is_running:
            self.is_running = True
            self.start()
    
    def stop_server(self):
        if self.is_running:
            self.is_running = False
            if self.loop and self.server:
                asyncio.run_coroutine_threadsafe(self.server.close(), self.loop)
            self.wait()
    
    def run(self):
        # Crear nuevo loop para este thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._start_websocket_server())
        except Exception as e:
            self.server_status.emit(False, f"Error del servidor: {str(e)}")
    
    async def _start_websocket_server(self):
        try:
            self.server = await websockets.serve(
                self._handle_client, 
                self.host, 
                self.port
            )
            self.server_status.emit(True, f"Servidor WebSocket iniciado en {self.host}:{self.port}")
            
            # Mantener el servidor corriendo
            await self.server.wait_closed()
            
        except Exception as e:
            self.server_status.emit(False, f"Error al iniciar servidor: {str(e)}")
    
    async def _handle_client(self, websocket, path):
        client_id = id(websocket)
        self.connected_clients.add(websocket)
        self.client_connected.emit(len(self.connected_clients))
        
        try:
            # Enviar mensaje de bienvenida
            welcome_msg = {
                "type": "connection",
                "message": "Conectado al servidor EMG",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(welcome_msg))
            
            # Mantener conexión activa
            async for message in websocket:
                # Procesar mensajes del cliente si es necesario
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        pong_msg = {
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(pong_msg))
                except json.JSONDecodeError:
                    pass
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Error manejando cliente {client_id}: {e}")
        finally:
            self.connected_clients.discard(websocket)
            self.client_connected.emit(len(self.connected_clients))
    
    def send_data(self, raw_value, filtered_value):
        if not self.connected_clients or not self.is_running:
            return
            
        message = {
            "type": "emg_data",
            "timestamp": datetime.now().isoformat(),
            "raw_value": raw_value,
            "filtered_value": filtered_value
        }
        
        # Enviar a todos los clientes conectados
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self._broadcast_message(json.dumps(message)),
                self.loop
            )
    
    async def _broadcast_message(self, message):
        if self.connected_clients:
            disconnected = set()
            for client in self.connected_clients.copy():
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
                except Exception as e:
                    print(f"Error enviando mensaje: {e}")
                    disconnected.add(client)
            
            # Remover clientes desconectados
            for client in disconnected:
                self.connected_clients.discard(client)
                
            if disconnected:
                self.client_connected.emit(len(self.connected_clients))