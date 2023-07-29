import os
import sys
import socket
import asyncio
import websockets

async def handle_connection(websocket, path):
    try:
        # 接收客户端发送的第一条消息
        msg = await websocket.recv()

        # 解析消息内容
        VERSION = msg[0]
        id = msg[1:17]
        uuid = os.getenv('UUID', 'd342d11e-d424-4583-b36e-524ab1f0afa4').replace('-', '')
        if not all(v == int(uuid[i * 2:i * 2 + 2], 16) for i, v in enumerate(id)):
            return

        i = 17
        port = int.from_bytes(msg[i:i+2], 'big')
        i += 2
        ATYP = msg[i]
        i += 1

        if ATYP == 1:
            host = '.'.join(str(b) for b in msg[i:i+4])  # IPv4
        elif ATYP == 2:
            domain_len = msg[i]
            i += 1
            host = msg[i:i+domain_len].decode()  # domain
        elif ATYP == 3:
            host = ':'.join(msg[i:i+16][i:i+2].hex() for i in range(0, 16, 2))  # IPv6
        else:
            return

        print(f'conn: {host}, {port}')
        await websocket.send(bytes([VERSION, 0]))

        try:
            reader, writer = await asyncio.open_connection(host, port)
            while True:
                data = await asyncio.wait_for(websocket.recv(), timeout=10)  # 设置接收超时时间
                if not data:
                    break
                writer.write(data)
                await writer.drain()
                response = await asyncio.wait_for(reader.read(), timeout=10)  # 设置读取超时时间
                await asyncio.wait_for(websocket.send(response), timeout=10)  # 设置发送超时时间
        except ConnectionRefusedError as e:
            print(f'Conn-Err: {host}, {port}, Connection refused')
        except asyncio.TimeoutError as e:
            print(f'Conn-Err: {host}, {port}, Timeout')
        except Exception as e:
            print(f'Conn-Err: {host}, {port}, {e}')
        finally:
            if writer:
                writer.close()

    except websockets.exceptions.ConnectionClosed:
        pass

async def start_server():
    port = int(os.getenv('PORT', 3000))
    async with websockets.serve(handle_connection, 'localhost', port):
        print(f'listen: {port}')
        await asyncio.Future()  # 持续运行服务器

if __name__ == '__main__':
    asyncio.run(start_server())
